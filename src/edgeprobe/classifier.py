from __future__ import annotations

import re

from edgeprobe.models import Category, Report, Severity, Signal, Snapshot, severity_rank


_DRIVER_PATTERNS = (
    re.compile(r"\b(reset|timeout|firmware|dma|pcie|xid)\b", re.IGNORECASE),
    re.compile(r"\b(iommu|irq|napi|rx queue|tx queue)\b", re.IGNORECASE),
)
_NETWORK_PATTERNS = (
    re.compile(r"\b(retrans|drop|unreachable|mtu|conntrack|tcp)\b", re.IGNORECASE),
    re.compile(r"\bdefault via|cni|calico|flannel|vxlan\b", re.IGNORECASE),
)
_KUBE_PATTERNS = (
    re.compile(r"\b(backoff|evicted|notready|failedscheduling|imagepull)\b", re.IGNORECASE),
    re.compile(r"\bcrashloopbackoff|nodepressure|readiness probe failed\b", re.IGNORECASE),
)
_WIRELESS_PATTERNS = (
    re.compile(r"\b(rsrp|rsrq|sinr|lte|5g|nr|wifi|wlan|roam)\b", re.IGNORECASE),
)
_WIRELESS_METRICS = re.compile(r"\b(rsrp|sinr)=(-?\d+)\b", re.IGNORECASE)
_REALTIME_BOOT_FLAGS = re.compile(r"\b(isolcpus|nohz_full|rcu_nocbs|preempt=rt)\b", re.IGNORECASE)
_REALTIME_STALL_PATTERNS = re.compile(
    r"\b(rcu_sched self-detected stall|rcu_preempt.*stall|soft lockup|hard lockup|"
    r"scheduling while atomic|blocked for more than \d+ seconds|hrtimer interrupt took)",
    re.IGNORECASE,
)


def classify(snapshot: Snapshot) -> Report:
    signals: list[Signal] = []
    passed: list[str] = []

    _classify_drivers(snapshot, signals, passed)
    _classify_network(snapshot, signals, passed)
    _classify_kubernetes(snapshot, signals, passed)
    _classify_runtime(snapshot, signals, passed)
    _classify_heterogeneous_compute(snapshot, signals, passed)
    _classify_wireless(snapshot, signals, passed)
    _classify_realtime(snapshot, signals, passed)
    _classify_ci_delivery(snapshot, signals, passed)

    signals.sort(key=lambda signal: severity_rank(signal.severity))

    confidence = min(0.98, 0.56 + (len(signals) * 0.07) + (len(passed) * 0.02))
    summary = _summary(signals)
    return Report(
        snapshot=snapshot,
        signals=tuple(signals),
        confidence=confidence,
        summary=summary,
        passed_checks=tuple(passed),
    )


def _classify_drivers(snapshot: Snapshot, signals: list[Signal], passed: list[str]) -> None:
    hits = [
        line
        for line in snapshot.dmesg_lines
        if any(pattern.search(line) for pattern in _DRIVER_PATTERNS)
    ]
    if hits:
        signals.append(
            Signal(
                Category.DEVICE_DRIVER,
                Severity.CRITICAL if any("timeout" in hit.lower() for hit in hits) else Severity.WARN,
                "Kernel or device-driver instability detected",
                hits[0],
                "Capture dmesg with monotonic timestamps, compare driver/firmware versions, "
                "and isolate DMA/IRQ pressure before redeploying the workload.",
            )
        )
    else:
        passed.append("driver log scan")


def _classify_network(snapshot: Snapshot, signals: list[Signal], passed: list[str]) -> None:
    corpus = (*snapshot.routes, *snapshot.sockets, *snapshot.ip_addresses, *snapshot.dmesg_lines)
    hits = [line for line in corpus if any(pattern.search(line) for pattern in _NETWORK_PATTERNS)]
    if hits:
        signals.append(
            Signal(
                Category.NETWORK_PATH,
                Severity.WARN,
                "Full-stack network path needs inspection",
                hits[0],
                "Verify route selection, MTU, conntrack pressure, and application socket state "
                "from OS to service endpoint.",
            )
        )
    else:
        passed.append("network route and socket scan")


def _classify_kubernetes(snapshot: Snapshot, signals: list[Signal], passed: list[str]) -> None:
    hits = [line for line in snapshot.kube_events if any(p.search(line) for p in _KUBE_PATTERNS)]
    if hits:
        signals.append(
            Signal(
                Category.CONTAINER_ORCHESTRATION,
                Severity.CRITICAL,
                "Kubernetes readiness is blocking delivery",
                hits[0],
                "Correlate pod events with node pressure, image pulls, readiness probes, and "
                "container runtime logs before rolling forward.",
            )
        )
    else:
        passed.append("kubernetes event scan")


def _classify_runtime(snapshot: Snapshot, signals: list[Signal], passed: list[str]) -> None:
    unhealthy = [row for row in snapshot.docker_rows if "unhealthy" in row.lower()]
    if unhealthy:
        signals.append(
            Signal(
                Category.RESOURCE_PRESSURE,
                Severity.WARN,
                "Container runtime reports unhealthy workloads",
                unhealthy[0],
                "Inspect cgroup CPU/memory pressure and container health checks before restarting blindly.",
            )
        )
    else:
        passed.append("docker runtime health")


def _classify_heterogeneous_compute(
    snapshot: Snapshot, signals: list[Signal], passed: list[str]
) -> None:
    if snapshot.gpu_devices:
        signals.append(
            Signal(
                Category.GPU_CPU_HETEROGENEOUS,
                Severity.INFO,
                "GPU/CPU heterogeneous node detected",
                snapshot.gpu_devices[0],
                "Pin device-plugin versions and validate NUMA, PCIe, and driver compatibility in CI.",
            )
        )
    else:
        passed.append("gpu inventory")


def _is_weak_wireless_line(line: str) -> bool:
    for metric, value in _WIRELESS_METRICS.findall(line):
        reading = int(value)
        if metric.lower() == "rsrp" and reading <= -110:
            return True
        if metric.lower() == "sinr" and reading < 0:
            return True
    return False


def _classify_wireless(snapshot: Snapshot, signals: list[Signal], passed: list[str]) -> None:
    hits = [line for line in snapshot.wireless_lines if any(p.search(line) for p in _WIRELESS_PATTERNS)]
    weak_signal = [line for line in hits if _is_weak_wireless_line(line)]
    if weak_signal:
        signals.append(
            Signal(
                Category.CELLULAR_WIFI,
                Severity.WARN,
                "Cellular or WiFi signal quality may affect readiness",
                weak_signal[0],
                "Track RSRP/RSRQ/SINR or WLAN roam events alongside application latency before blaming code.",
            )
        )
    elif hits:
        passed.append("cellular and wifi telemetry")
    else:
        passed.append("wireless telemetry absent")


def _classify_realtime(snapshot: Snapshot, signals: list[Signal], passed: list[str]) -> None:
    is_rt_provisioned = bool(
        (snapshot.kernel_cmdline and _REALTIME_BOOT_FLAGS.search(snapshot.kernel_cmdline))
        or (snapshot.kernel_release and "-rt" in snapshot.kernel_release.lower())
    )
    stalls = [line for line in snapshot.dmesg_lines if _REALTIME_STALL_PATTERNS.search(line)]

    if stalls:
        signals.append(
            Signal(
                Category.REALTIME_LATENCY,
                Severity.CRITICAL if is_rt_provisioned else Severity.WARN,
                "Kernel scheduling latency or CPU stall detected",
                stalls[0],
                "Correlate isolcpus/nohz_full/rcu_nocbs boot flags with the stall trace, check "
                "housekeeping-CPU IRQ affinity, and re-run cyclictest before trusting this node "
                "for latency-sensitive workloads.",
            )
        )
    else:
        passed.append("realtime kernel latency scan")


def _classify_ci_delivery(snapshot: Snapshot, signals: list[Signal], passed: list[str]) -> None:
    if snapshot.kernel_release and snapshot.kernel_cmdline:
        passed.append("os build provenance")
        return
    signals.append(
        Signal(
            Category.CI_DELIVERY,
            Severity.WARN,
            "OS build provenance is incomplete",
            "missing kernel_release.txt or proc_cmdline.txt",
            "Export kernel release, boot parameters, image digest, and Git SHA in every CI artifact.",
        )
    )


def _summary(signals: list[Signal]) -> str:
    if not signals:
        return "No blocking readiness signals found."
    critical = sum(1 for signal in signals if signal.severity == Severity.CRITICAL)
    warn = sum(1 for signal in signals if signal.severity == Severity.WARN)
    return f"{critical} critical and {warn} warning signal(s) found across Linux edge readiness checks."


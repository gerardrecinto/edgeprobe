from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum


class Category(StrEnum):
    CONTAINER_ORCHESTRATION = "container_orchestration"
    DEVICE_DRIVER = "device_driver"
    NETWORK_PATH = "network_path"
    REALTIME_LATENCY = "realtime_latency"
    GPU_CPU_HETEROGENEOUS = "gpu_cpu_heterogeneous"
    CELLULAR_WIFI = "cellular_wifi"
    CI_DELIVERY = "ci_delivery"
    RESOURCE_PRESSURE = "resource_pressure"


class Severity(StrEnum):
    INFO = "info"
    WARN = "warn"
    CRITICAL = "critical"


@dataclass(frozen=True)
class Signal:
    category: Category
    severity: Severity
    title: str
    evidence: str
    remediation: str


@dataclass(frozen=True)
class Snapshot:
    name: str
    kernel_release: str | None = None
    kernel_cmdline: str | None = None
    cpu_model: str | None = None
    gpu_devices: tuple[str, ...] = ()
    dmesg_lines: tuple[str, ...] = ()
    ip_addresses: tuple[str, ...] = ()
    routes: tuple[str, ...] = ()
    sockets: tuple[str, ...] = ()
    kube_events: tuple[str, ...] = ()
    docker_rows: tuple[str, ...] = ()
    wireless_lines: tuple[str, ...] = ()


@dataclass(frozen=True)
class Report:
    snapshot: Snapshot
    signals: tuple[Signal, ...]
    confidence: float
    summary: str
    passed_checks: tuple[str, ...] = field(default_factory=tuple)

    @property
    def status(self) -> str:
        if any(signal.severity == Severity.CRITICAL for signal in self.signals):
            return "ACTION REQUIRED"
        if any(signal.severity == Severity.WARN for signal in self.signals):
            return "WATCH"
        return "READY"


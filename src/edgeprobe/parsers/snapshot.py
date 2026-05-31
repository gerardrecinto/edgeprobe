from __future__ import annotations

from pathlib import Path

from edgeprobe.models import Snapshot


def _read_optional(path: Path) -> str | None:
    if not path.exists():
        return None
    return path.read_text(encoding="utf-8").strip()


def _read_lines(path: Path) -> tuple[str, ...]:
    text = _read_optional(path)
    if text is None:
        return ()
    return tuple(line.strip() for line in text.splitlines() if line.strip())


def _cpu_model(cpuinfo: str | None) -> str | None:
    if cpuinfo is None:
        return None
    for line in cpuinfo.splitlines():
        if line.lower().startswith("model name"):
            _, value = line.split(":", 1)
            return value.strip()
    return None


def _gpu_devices(lspci: str | None) -> tuple[str, ...]:
    if lspci is None:
        return ()
    return tuple(
        line.strip()
        for line in lspci.splitlines()
        if any(token in line.lower() for token in ("vga", "3d controller", "display"))
    )


def load_snapshot(snapshot_dir: Path) -> Snapshot:
    if not snapshot_dir.exists():
        raise FileNotFoundError(f"snapshot directory not found: {snapshot_dir}")
    if not snapshot_dir.is_dir():
        raise NotADirectoryError(f"snapshot path is not a directory: {snapshot_dir}")

    cpuinfo = _read_optional(snapshot_dir / "proc_cpuinfo.txt")
    lspci = _read_optional(snapshot_dir / "lspci.txt")

    return Snapshot(
        name=snapshot_dir.name,
        kernel_release=_read_optional(snapshot_dir / "kernel_release.txt"),
        kernel_cmdline=_read_optional(snapshot_dir / "proc_cmdline.txt"),
        cpu_model=_cpu_model(cpuinfo),
        gpu_devices=_gpu_devices(lspci),
        dmesg_lines=_read_lines(snapshot_dir / "dmesg.log"),
        ip_addresses=_read_lines(snapshot_dir / "ip_addr.txt"),
        routes=_read_lines(snapshot_dir / "ip_route.txt"),
        sockets=_read_lines(snapshot_dir / "ss.txt"),
        kube_events=_read_lines(snapshot_dir / "kube_events.log"),
        docker_rows=_read_lines(snapshot_dir / "docker_ps.txt"),
        wireless_lines=_read_lines(snapshot_dir / "wireless.log"),
    )


from __future__ import annotations

import json

from edgeprobe.models import Report, Severity, severity_rank


def terminal_report(report: Report) -> str:
    lines = [
        "────────────────────────────────────────────────────────────",
        "  edgeprobe",
        "────────────────────────────────────────────────────────────",
        f"  {status_icon(report.status)}  {report.status}",
        f"  snapshot:   {report.snapshot.name}",
        f"  kernel:     {report.snapshot.kernel_release or 'unknown'}",
        f"  confidence: {round(report.confidence * 100)}%",
        "",
        f"  SUMMARY",
        f"  {report.summary}",
        "",
    ]

    if report.signals:
        lines.append("  SIGNALS")
        for signal in report.signals:
            lines.extend(
                [
                    f"  - {signal.severity.upper()} · {signal.category}",
                    f"    {signal.title}",
                    f"    evidence: {signal.evidence}",
                    f"    fix: {signal.remediation}",
                ]
            )
    else:
        lines.append("  SIGNALS")
        lines.append("  - none")

    if report.passed_checks:
        lines.append("")
        lines.append("  PASSED CHECKS")
        for check in report.passed_checks:
            lines.append(f"  - {check}")

    lines.append("────────────────────────────────────────────────────────────")
    return "\n".join(lines)


def json_report(report: Report) -> str:
    payload = {
        "status": report.status,
        "snapshot": report.snapshot.name,
        "kernel": report.snapshot.kernel_release,
        "confidence": report.confidence,
        "summary": report.summary,
        "signals": [
            {
                "category": signal.category,
                "severity": signal.severity,
                "title": signal.title,
                "evidence": signal.evidence,
                "remediation": signal.remediation,
            }
            for signal in report.signals
        ],
        "passed_checks": list(report.passed_checks),
    }
    return json.dumps(payload, indent=2, sort_keys=True)


def status_icon(status: str) -> str:
    return "✗" if status == "ACTION REQUIRED" else "!" if status == "WATCH" else "✓"


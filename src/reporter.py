"""
Markdown report generator for TestDesignOutput.

Responsibility: format a validated TestDesignOutput and its source
RequirementInput as a clean, human-readable Markdown report.

Public interface:
    generate_report(requirement, output) -> str
    write_report(report, path) -> None
"""

from pathlib import Path

from .models import RequirementInput, TestDesignOutput


def _bullet_section(heading: str, items: list[str]) -> list[str]:
    lines = [f"## {heading}", ""]
    for item in items:
        lines.append(f"- {item}")
    lines.append("")
    return lines


def generate_report(requirement: RequirementInput, output: TestDesignOutput) -> str:
    lines: list[str] = []

    lines.append("# Test Design Report")
    lines.append("")

    lines.append("## Executive Summary")
    lines.append("")
    if requirement.source_type:
        lines.append(f"- **Source type:** {requirement.source_type.replace('_', ' ').title()}")
    lines.append(f"- **Positive scenarios:** {len(output.positive_scenarios)}")
    lines.append(f"- **Negative scenarios:** {len(output.negative_scenarios)}")
    lines.append(f"- **Edge cases:** {len(output.edge_cases)}")
    lines.append(f"- **Clarification questions:** {len(output.clarification_questions)}")
    lines.append(f"- **Risks:** {len(output.risks)}")
    lines.append("")

    lines.extend(_bullet_section("Positive Scenarios", output.positive_scenarios))
    lines.extend(_bullet_section("Negative Scenarios", output.negative_scenarios))
    lines.extend(_bullet_section("Edge Cases", output.edge_cases))
    lines.extend(_bullet_section("Clarification Questions", output.clarification_questions))
    lines.extend(_bullet_section("Risks", output.risks))

    lines.append("## Requirement Snapshot")
    lines.append("")
    for raw_line in requirement.raw_text.splitlines():
        lines.append(f"> {raw_line}" if raw_line.strip() else ">")
    lines.append("")

    return "\n".join(lines)


def write_report(report: str, path: Path) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(report, encoding="utf-8")

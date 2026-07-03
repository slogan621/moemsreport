#!/usr/bin/env python3
"""Generate per-student PDF exam reports from YAML population and student data."""

from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from pathlib import Path

import matplotlib.pyplot as plt
import yaml
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.patches import FancyBboxPatch

from exam_percentile import percentile_rank


@dataclass(frozen=True)
class Population:
    label: str
    size: int
    percentages: dict[int, float]


@dataclass(frozen=True)
class Student:
    name: str
    score: int


@dataclass(frozen=True)
class ReportContext:
    team_name: str | None = None
    season: str | None = None
    contest_number: int | None = None


def parse_score_percentages(values: list[float]) -> dict[int, float]:
    """Convert [pct@5, pct@4, ..., pct@0] into {score: pct} for scores 0-5."""
    if len(values) != 6:
        raise ValueError(f"Expected 6 score percentages, got {len(values)}")
    return {score: float(values[5 - score]) for score in range(6)}


def load_populations(path: Path) -> list[Population]:
    with path.open(encoding="utf-8") as handle:
        data = yaml.safe_load(handle)

    populations: list[Population] = []
    for index, entry in enumerate(data.get("populations", []), start=1):
        label = entry.get("label")
        size = entry.get("size")
        score_percentages = entry.get("score_percentages")

        if not label:
            raise ValueError(f"Population #{index} is missing a label.")
        if size is None or int(size) < 1:
            raise ValueError(f"Population '{label}' must have size >= 1.")
        if score_percentages is None:
            raise ValueError(f"Population '{label}' is missing score_percentages.")

        percentages = parse_score_percentages(score_percentages)
        total = sum(percentages.values())
        if abs(total - 100.0) > 0.01:
            print(f"Warning: '{label}' percentages sum to {total:.2f}% (expected 100%).")

        populations.append(
            Population(label=str(label), size=int(size), percentages=percentages)
        )

    if not populations:
        raise ValueError(f"No populations found in {path}.")

    return populations


def load_students(path: Path) -> list[Student]:
    with path.open(encoding="utf-8") as handle:
        data = yaml.safe_load(handle)

    students: list[Student] = []
    for index, entry in enumerate(data.get("students", []), start=1):
        name = entry.get("name")
        score = entry.get("score")

        if not name:
            raise ValueError(f"Student #{index} is missing a name.")
        if score is None:
            raise ValueError(f"Student '{name}' is missing a score.")

        score_value = int(score)
        if score_value < 0 or score_value > 5:
            raise ValueError(f"Student '{name}' has invalid score {score_value}; expected 0-5.")

        students.append(Student(name=str(name), score=score_value))

    if not students:
        raise ValueError(f"No students found in {path}.")

    return students


def percentile_label(value: float) -> str:
    rounded = int(round(value))
    if 11 <= (rounded % 100) <= 13:
        suffix = "th"
    else:
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(rounded % 10, "th")
    return f"{value:.1f}{suffix}"


def sanitize_filename(name: str) -> str:
    cleaned = re.sub(r"[^\w\s-]", "", name, flags=re.UNICODE)
    cleaned = re.sub(r"[-\s]+", "_", cleaned.strip())
    return cleaned or "student"


def format_report_heading(context: ReportContext | None) -> tuple[str, str | None]:
    if context is None:
        return "Exam Results Report", None

    if context.team_name:
        title = f"{context.team_name} — Exam Results"
    else:
        title = "Exam Results Report"

    subtitle_parts: list[str] = []
    if context.season:
        subtitle_parts.append(f"{context.season} Season")
    if context.contest_number is not None:
        subtitle_parts.append(f"Contest {context.contest_number}")

    subtitle = " · ".join(subtitle_parts) if subtitle_parts else None
    return title, subtitle


def population_display_label(population: Population, context: ReportContext | None) -> str:
    if context and context.team_name and population.label.strip().lower() == "my team":
        return context.team_name
    return population.label


def report_filename(student: Student, context: ReportContext | None) -> str:
    base = sanitize_filename(student.name)
    if context and context.contest_number is not None:
        return f"{base}_contest_{context.contest_number:02d}_report.pdf"
    return f"{base}_report.pdf"


def add_report_heading(fig: plt.Figure, context: ReportContext | None) -> None:
    title, subtitle = format_report_heading(context)
    fig.suptitle(title, fontsize=20, fontweight="bold", y=0.96, color="#0D47A1")
    if subtitle:
        fig.text(0.5, 0.925, subtitle, ha="center", fontsize=13, color="#37474F")


def percentile_color(value: float) -> str:
    if value >= 75:
        return "#2E7D32"
    if value >= 50:
        return "#1565C0"
    if value >= 25:
        return "#EF6C00"
    return "#C62828"


def cumulative_percentages(percentages: dict[int, float]) -> list[float]:
    running = 0.0
    cumulative: list[float] = []
    for score in range(6):
        running += percentages[score]
        cumulative.append(running)
    return cumulative


def mean_score(percentages: dict[int, float]) -> float:
    return sum(score * percentages[score] for score in range(6)) / 100.0


POPULATION_COLORS = [
    "#1565C0",
    "#2E7D32",
    "#EF6C00",
    "#6A1B9A",
    "#C62828",
    "#00838F",
    "#4E342E",
    "#546E7A",
]


def population_colors(count: int) -> list[str]:
    return [POPULATION_COLORS[index % len(POPULATION_COLORS)] for index in range(count)]


def draw_score_summary(fig: plt.Figure, student: Student) -> None:
    ax = fig.add_axes([0.08, 0.78, 0.84, 0.16])
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    box = FancyBboxPatch(
        (0.0, 0.0),
        1.0,
        1.0,
        boxstyle="round,pad=0.02,rounding_size=0.03",
        linewidth=1.5,
        edgecolor="#1565C0",
        facecolor="#E3F2FD",
    )
    ax.add_patch(box)
    ax.text(
        0.5,
        0.62,
        f"{student.name}",
        ha="center",
        va="center",
        fontsize=22,
        fontweight="bold",
        color="#0D47A1",
    )
    ax.text(
        0.5,
        0.28,
        f"Score: {student.score} out of 5 questions correct",
        ha="center",
        va="center",
        fontsize=16,
        color="#1A237E",
    )


def draw_percentile_chart(
    fig: plt.Figure,
    populations: list[Population],
    percentiles: list[float],
    context: ReportContext | None = None,
) -> None:
    chart_height = min(0.52, max(0.28, 0.05 * len(populations)))
    bottom = max(0.08, 0.74 - chart_height)
    ax = fig.add_axes([0.12, bottom, 0.78, chart_height])
    labels = [population_display_label(population, context) for population in populations]
    y_positions = range(len(labels))
    colors = [percentile_color(value) for value in percentiles]

    bars = ax.barh(
        list(y_positions),
        percentiles,
        color=colors,
        edgecolor="#37474F",
        height=0.65,
    )
    ax.set_yticks(list(y_positions), labels=labels)
    ax.set_xlim(0, 100)
    ax.set_xlabel("Percentile rank")
    ax.set_title("Your percentile rank by comparison group", fontsize=14, pad=12)
    ax.axvline(50, color="#90A4AE", linestyle="--", linewidth=1, alpha=0.8)
    ax.grid(axis="x", linestyle=":", alpha=0.5)

    for bar, value, population in zip(bars, percentiles, populations):
        ax.text(
            min(value + 2, 92),
            bar.get_y() + bar.get_height() / 2,
            f"{percentile_label(value)}  (n={population.size:,})",
            va="center",
            fontsize=10,
            fontweight="bold",
            color="#263238",
        )


def draw_population_comparison_page(
    fig: plt.Figure,
    populations: list[Population],
    context: ReportContext | None = None,
) -> None:
    labels = [population_display_label(population, context) for population in populations]
    colors = population_colors(len(populations))
    averages = [mean_score(population.percentages) for population in populations]

    mean_ax = fig.add_axes([0.14, 0.58, 0.78, 0.28])
    y_positions = range(len(labels))
    mean_bars = mean_ax.barh(
        list(y_positions),
        averages,
        color=colors,
        edgecolor="#37474F",
        height=0.65,
    )
    mean_ax.set_yticks(list(y_positions), labels=labels)
    mean_ax.set_xlim(0, 5)
    mean_ax.set_xlabel("Average score (out of 5)")
    mean_ax.set_title("Average score by group", fontsize=13, pad=10)
    mean_ax.grid(axis="x", linestyle=":", alpha=0.5)

    for bar, average in zip(mean_bars, averages):
        mean_ax.text(
            min(average + 0.08, 4.55),
            bar.get_y() + bar.get_height() / 2,
            f"{average:.2f}",
            va="center",
            fontsize=10,
            fontweight="bold",
            color="#263238",
        )

    dist_ax = fig.add_axes([0.12, 0.12, 0.82, 0.36])
    scores = list(range(6))
    group_width = 0.75
    bar_width = group_width / len(populations)
    base_offset = -group_width / 2 + bar_width / 2

    for index, (population, label, color) in enumerate(zip(populations, labels, colors)):
        offset = base_offset + index * bar_width
        dist_ax.bar(
            [score + offset for score in scores],
            [population.percentages[score] for score in scores],
            width=bar_width * 0.92,
            label=label,
            color=color,
            edgecolor="#37474F",
            linewidth=0.6,
        )

    dist_ax.set_xlim(-0.5, 5.5)
    dist_ax.set_xticks(scores)
    dist_ax.set_xlabel("Questions correct")
    dist_ax.set_ylabel("% of group")
    dist_ax.set_title("Score distribution by group", fontsize=13, pad=10)
    dist_ax.grid(axis="y", linestyle=":", alpha=0.4)
    dist_ax.legend(loc="upper right", fontsize=8, framealpha=0.9)


def draw_distribution_panel(
    fig: plt.Figure,
    bounds: tuple[float, float, float, float],
    student: Student,
    population: Population,
    percentile: float,
    *,
    show_legend: bool,
    context: ReportContext | None = None,
) -> None:
    ax = fig.add_axes(bounds)

    scores = list(range(6))
    distribution = [population.percentages[score] for score in scores]
    cumulative = cumulative_percentages(population.percentages)

    ax.bar(
        scores,
        distribution,
        color="#BBDEFB",
        edgecolor="#1565C0",
        width=0.75,
        label="Score distribution",
    )
    ax.plot(
        scores,
        cumulative,
        color="#EF6C00",
        marker="o",
        linewidth=2,
        label="Cumulative %",
    )
    ax.axvline(
        student.score,
        color="#2E7D32",
        linewidth=2.5,
        linestyle="-",
        label="Your score",
    )

    ax.set_xlim(-0.5, 5.5)
    ax.set_ylim(0, max(100, max(cumulative) + 5))
    ax.set_xticks(scores)
    ax.set_xlabel("Questions correct")
    ax.set_ylabel("%")
    label = population_display_label(population, context)
    ax.set_title(
        f"{label}: you are in the {percentile_label(percentile)} percentile",
        fontsize=11,
        loc="left",
    )
    ax.grid(axis="y", linestyle=":", alpha=0.4)

    if show_legend:
        ax.legend(loc="upper left", fontsize=8, framealpha=0.9)


def distribution_page_layout(panel_count: int) -> list[tuple[float, float, float, float]]:
    """Return axis bounds for up to three distribution panels on one page."""
    left = 0.10
    width = 0.82
    gap = 0.06
    usable_height = 0.78
    panel_height = (usable_height - gap * (panel_count - 1)) / panel_count
    top = 0.88

    layouts: list[tuple[float, float, float, float]] = []
    for index in range(panel_count):
        bottom = top - (index + 1) * panel_height - index * gap
        layouts.append((left, bottom, width, panel_height))
    return layouts


def build_report_pdf(
    output_path: Path,
    student: Student,
    populations: list[Population],
    context: ReportContext | None = None,
) -> None:
    percentiles = [
        percentile_rank(student.score, population.percentages) for population in populations
    ]
    panels_per_page = 3
    footer = (
        "Percentile rank = share of students who scored below you, "
        "plus half of those with the same score."
    )

    with PdfPages(output_path) as pdf:
        summary_fig = plt.figure(figsize=(8.5, 11))
        summary_fig.patch.set_facecolor("white")
        add_report_heading(summary_fig, context)
        draw_score_summary(summary_fig, student)
        draw_percentile_chart(summary_fig, populations, percentiles, context)
        summary_fig.text(0.5, 0.03, footer, ha="center", fontsize=9, color="#546E7A")
        pdf.savefig(summary_fig, bbox_inches="tight")
        plt.close(summary_fig)

        comparison_fig = plt.figure(figsize=(8.5, 11))
        comparison_fig.patch.set_facecolor("white")
        contest_suffix = (
            f" (Contest {context.contest_number})"
            if context and context.contest_number is not None
            else ""
        )
        comparison_fig.suptitle(
            f"How Each Group Performed Relative to Others{contest_suffix}",
            fontsize=16,
            fontweight="bold",
            y=0.96,
            color="#0D47A1",
        )
        draw_population_comparison_page(comparison_fig, populations, context)
        comparison_fig.text(
            0.5,
            0.03,
            "Higher average scores and more mass on the right side of the distribution indicate stronger group performance.",
            ha="center",
            fontsize=9,
            color="#546E7A",
        )
        pdf.savefig(comparison_fig, bbox_inches="tight")
        plt.close(comparison_fig)

        for page_start in range(0, len(populations), panels_per_page):
            page_populations = populations[page_start : page_start + panels_per_page]
            page_percentiles = percentiles[page_start : page_start + panels_per_page]
            layouts = distribution_page_layout(len(page_populations))

            detail_fig = plt.figure(figsize=(8.5, 11))
            detail_fig.patch.set_facecolor("white")
            contest_suffix = (
                f" (Contest {context.contest_number})"
                if context and context.contest_number is not None
                else ""
            )
            detail_fig.suptitle(
                f"Score Distribution Comparison — {student.name}{contest_suffix}",
                fontsize=16,
                fontweight="bold",
                y=0.96,
                color="#0D47A1",
            )

            for index, (population, percentile, bounds) in enumerate(
                zip(page_populations, page_percentiles, layouts)
            ):
                draw_distribution_panel(
                    detail_fig,
                    bounds,
                    student,
                    population,
                    percentile,
                    show_legend=index == 0,
                    context=context,
                )

            detail_fig.text(0.5, 0.03, footer, ha="center", fontsize=9, color="#546E7A")
            pdf.savefig(detail_fig, bbox_inches="tight")
            plt.close(detail_fig)


def generate_reports(
    populations_path: Path,
    students_path: Path,
    output_dir: Path,
    context: ReportContext | None = None,
) -> list[Path]:
    populations = load_populations(populations_path)
    students = load_students(students_path)
    output_dir.mkdir(parents=True, exist_ok=True)

    created: list[Path] = []
    for student in students:
        output_path = output_dir / report_filename(student, context)
        build_report_pdf(output_path, student, populations, context)
        created.append(output_path)
        print(f"Created {output_path}")

    return created


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate per-student PDF exam reports from YAML files."
    )
    parser.add_argument(
        "populations_yaml",
        type=Path,
        help="YAML file describing comparison populations",
    )
    parser.add_argument(
        "students_yaml",
        type=Path,
        help="YAML file listing students and their scores",
    )
    parser.add_argument(
        "-o",
        "--output-dir",
        type=Path,
        default=Path("reports"),
        help="Directory where PDF reports will be written (default: reports)",
    )
    parser.add_argument(
        "--team-name",
        help="Team name shown on reports (replaces the 'my team' population label)",
    )
    parser.add_argument(
        "--season",
        help='Contest season label, e.g. "2025 - 2026"',
    )
    parser.add_argument(
        "--contest-number",
        type=int,
        help="Contest number for this report set",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    if not args.populations_yaml.is_file():
        raise SystemExit(f"Populations file not found: {args.populations_yaml}")
    if not args.students_yaml.is_file():
        raise SystemExit(f"Students file not found: {args.students_yaml}")
    if args.contest_number is not None and args.contest_number < 1:
        raise SystemExit("Contest number must be at least 1.")

    context = ReportContext(
        team_name=args.team_name,
        season=args.season,
        contest_number=args.contest_number,
    )
    reports = generate_reports(
        args.populations_yaml,
        args.students_yaml,
        args.output_dir,
        context,
    )
    print(f"\nGenerated {len(reports)} report(s) in {args.output_dir.resolve()}")


if __name__ == "__main__":
    main()

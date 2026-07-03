#!/usr/bin/env python3
"""Generate exam reports for one contest or an entire season from a season YAML file."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path

import yaml

from exam_percentile_report import ReportContext, generate_reports


@dataclass(frozen=True)
class ContestSpec:
    number: int
    populations_path: Path
    students_path: Path


@dataclass(frozen=True)
class SeasonSpec:
    team_name: str
    season: str
    contests: list[ContestSpec]
    base_dir: Path


def resolve_season_path(base_dir: Path, value: str) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path
    return (base_dir / path).resolve()


def load_season(path: Path) -> SeasonSpec:
    with path.open(encoding="utf-8") as handle:
        data = yaml.safe_load(handle)

    team_name = data.get("team_name")
    season = data.get("season")
    if not team_name:
        raise ValueError(f"{path}: missing team_name.")
    if not season:
        raise ValueError(f"{path}: missing season.")

    base_dir = path.parent.resolve()
    contests: list[ContestSpec] = []
    for index, entry in enumerate(data.get("contests", []), start=1):
        number = entry.get("number")
        populations = entry.get("populations")
        students = entry.get("students")

        if number is None:
            raise ValueError(f"Contest #{index} in {path} is missing number.")
        if not populations:
            raise ValueError(f"Contest {number} in {path} is missing populations.")
        if not students:
            raise ValueError(f"Contest {number} in {path} is missing students.")

        contests.append(
            ContestSpec(
                number=int(number),
                populations_path=resolve_season_path(base_dir, str(populations)),
                students_path=resolve_season_path(base_dir, str(students)),
            )
        )

    if not contests:
        raise ValueError(f"No contests found in {path}.")

    contests.sort(key=lambda contest: contest.number)
    numbers = [contest.number for contest in contests]
    if len(numbers) != len(set(numbers)):
        raise ValueError(f"Duplicate contest numbers found in {path}.")

    return SeasonSpec(
        team_name=str(team_name),
        season=str(season),
        contests=contests,
        base_dir=base_dir,
    )


def select_contests(season: SeasonSpec, contest_number: int | None) -> list[ContestSpec]:
    if contest_number is None:
        return season.contests

    matches = [contest for contest in season.contests if contest.number == contest_number]
    if not matches:
        available = ", ".join(str(contest.number) for contest in season.contests)
        raise ValueError(
            f"Contest {contest_number} not found in season file. Available: {available}"
        )
    return matches


def default_output_dir(season_file: Path) -> Path:
    return season_file.parent / "reports"


def contest_output_dir(output_root: Path, contest_number: int) -> Path:
    return output_root / f"contest_{contest_number:02d}"


def run_season(
    season_file: Path,
    output_dir: Path,
    contest_number: int | None = None,
) -> list[Path]:
    season = load_season(season_file)
    selected = select_contests(season, contest_number)
    created: list[Path] = []

    print(
        f"Team: {season.team_name}\n"
        f"Season: {season.season}\n"
        f"Running {len(selected)} contest(s)\n"
    )

    for contest in selected:
        if not contest.populations_path.is_file():
            raise FileNotFoundError(f"Populations file not found: {contest.populations_path}")
        if not contest.students_path.is_file():
            raise FileNotFoundError(f"Students file not found: {contest.students_path}")

        contest_dir = contest_output_dir(output_dir, contest.number)
        context = ReportContext(
            team_name=season.team_name,
            season=season.season,
            contest_number=contest.number,
        )

        print(f"Contest {contest.number}")
        print(f"  Populations: {contest.populations_path}")
        print(f"  Students:    {contest.students_path}")
        print(f"  Output:      {contest_dir}")

        reports = generate_reports(
            contest.populations_path,
            contest.students_path,
            contest_dir,
            context,
        )
        created.extend(reports)
        print()

    return created


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate exam reports for one contest or a full season."
    )
    parser.add_argument(
        "season_yaml",
        type=Path,
        help="Season YAML file listing team metadata and contests",
    )
    parser.add_argument(
        "-o",
        "--output-dir",
        type=Path,
        help="Root output directory (contest subfolders are created inside)",
    )
    parser.add_argument(
        "--contest",
        type=int,
        help="Generate reports for a single contest number instead of the full season",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    if not args.season_yaml.is_file():
        raise SystemExit(f"Season file not found: {args.season_yaml}")
    if args.contest is not None and args.contest < 1:
        raise SystemExit("Contest number must be at least 1.")

    output_dir = args.output_dir or default_output_dir(args.season_yaml)
    reports = run_season(args.season_yaml, output_dir, args.contest)

    scope = f"contest {args.contest}" if args.contest is not None else "season"
    print(f"Generated {len(reports)} report(s) for the {scope} in {output_dir.resolve()}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Create sample season YAML files for demonstration."""

from pathlib import Path

import yaml

BASE = Path(__file__).resolve().parent / "2025-2026"
CONTESTS = BASE / "contests"

NAMES = [
    "Maya Chen",
    "Jordan Brooks",
    "Sofia Martinez",
    "Ethan Nguyen",
    "Olivia Parker",
    "Liam O'Connor",
    "Aisha Rahman",
    "Noah Kim",
    "Emma Sullivan",
    "Marcus Johnson",
    "Zoe Williams",
    "Diego Flores",
    "Hannah Becker",
    "Tyler Anderson",
    "Priya Sharma",
    "Caleb Thompson",
    "Lily Nakamura",
]

SCORES_BY_CONTEST = {
    1: [4, 3, 3, 2, 4, 2, 3, 2, 3, 2, 4, 1, 2, 3, 2, 2, 3],
    2: [4, 4, 3, 3, 4, 3, 3, 2, 4, 3, 4, 2, 3, 4, 2, 3, 4],
    3: [5, 4, 4, 3, 4, 3, 4, 3, 4, 3, 5, 2, 3, 4, 3, 3, 4],
    4: [5, 4, 4, 3, 5, 4, 4, 3, 4, 3, 5, 2, 4, 4, 3, 3, 4],
    5: [5, 5, 4, 4, 5, 4, 4, 3, 5, 4, 5, 3, 4, 5, 4, 4, 5],
}

POPULATIONS_BY_CONTEST = {
    1: {
        "my team": [10, 22, 28, 20, 14, 6],
        "All Participants": [5, 10, 17, 24, 24, 20],
        "6th grade": [7, 12, 19, 24, 23, 15],
        "5th grade": [4, 9, 16, 23, 25, 23],
        "4th grade": [3, 7, 13, 21, 27, 29],
    },
    2: {
        "my team": [11, 23, 28, 19, 13, 6],
        "All Participants": [6, 11, 18, 24, 23, 18],
        "6th grade": [8, 13, 20, 24, 22, 13],
        "5th grade": [5, 10, 17, 23, 24, 21],
        "4th grade": [4, 8, 14, 22, 26, 26],
    },
    3: {
        "my team": [12, 24, 29, 18, 12, 5],
        "All Participants": [6, 11, 18, 24, 23, 18],
        "6th grade": [8, 14, 20, 24, 22, 12],
        "5th grade": [5, 10, 17, 23, 24, 21],
        "4th grade": [4, 8, 14, 22, 26, 26],
    },
    4: {
        "my team": [13, 25, 28, 17, 11, 6],
        "All Participants": [7, 12, 19, 24, 22, 16],
        "6th grade": [9, 15, 21, 24, 21, 10],
        "5th grade": [5, 10, 17, 23, 24, 21],
        "4th grade": [4, 8, 14, 22, 26, 26],
    },
    5: {
        "my team": [14, 26, 27, 17, 10, 6],
        "All Participants": [7, 12, 19, 24, 22, 16],
        "6th grade": [9, 15, 21, 24, 21, 10],
        "5th grade": [5, 10, 17, 23, 24, 21],
        "4th grade": [4, 8, 14, 22, 26, 26],
    },
}

POPULATION_LABELS = ["my team", "All Participants", "6th grade", "5th grade", "4th grade"]

SIZES = {
    "my team": 17,
    "All Participants": 1000,
    "6th grade": 400,
    "5th grade": 300,
    "4th grade": 300,
}


def write_contest(number: int) -> None:
    contest_dir = CONTESTS / f"contest_{number:02d}"
    contest_dir.mkdir(parents=True, exist_ok=True)

    populations = []
    for label in POPULATION_LABELS:
        populations.append(
            {
                "label": label,
                "size": SIZES[label],
                "score_percentages": POPULATIONS_BY_CONTEST[number][label],
            }
        )

    students = [
        {"name": name, "score": score}
        for name, score in zip(NAMES, SCORES_BY_CONTEST[number])
    ]

    with (contest_dir / "populations.yaml").open("w", encoding="utf-8") as handle:
        yaml.safe_dump({"populations": populations}, handle, sort_keys=False)

    with (contest_dir / "students.yaml").open("w", encoding="utf-8") as handle:
        yaml.safe_dump({"students": students}, handle, sort_keys=False)


def main() -> None:
    BASE.mkdir(parents=True, exist_ok=True)

    season = {
        "team_name": "AOE Math Club",
        "season": "2025 - 2026",
        "contests": [
            {
                "number": number,
                "populations": f"contests/contest_{number:02d}/populations.yaml",
                "students": f"contests/contest_{number:02d}/students.yaml",
            }
            for number in range(1, 6)
        ],
    }

    for number in range(1, 6):
        write_contest(number)

    with (BASE / "season.yaml").open("w", encoding="utf-8") as handle:
        yaml.safe_dump(season, handle, sort_keys=False)

    print(f"Created sample season in {BASE}")


if __name__ == "__main__":
    main()

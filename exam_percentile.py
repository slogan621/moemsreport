#!/usr/bin/env python3
"""Compute exam percentiles for a student against populations A and B."""

from __future__ import annotations


def prompt_float(label: str, *, min_value: float | None = None) -> float:
    while True:
        raw = input(label).strip()
        try:
            value = float(raw)
        except ValueError:
            print("  Please enter a valid number.")
            continue

        if min_value is not None and value < min_value:
            print(f"  Please enter a value of at least {min_value}.")
            continue

        return value


def prompt_int(label: str, *, min_value: int = 1) -> int:
    while True:
        raw = input(label).strip()
        try:
            value = int(raw)
        except ValueError:
            print("  Please enter a whole number.")
            continue

        if value < min_value:
            print(f"  Please enter a value of at least {min_value}.")
            continue

        return value


def read_population_size(name: str) -> int:
    return prompt_int(f"Number of students in population {name}: ", min_value=1)


def read_score_percentages(name: str) -> dict[int, float]:
    print(f"\nScore breakdown for population {name} (% of students for each score 0-5):")
    percentages: dict[int, float] = {}

    for score in range(6):
        pct = prompt_float(f"  % who scored {score}: ", min_value=0.0)
        percentages[score] = pct

    total = sum(percentages.values())
    if abs(total - 100.0) > 0.01:
        print(f"  Warning: percentages sum to {total:.2f}% (expected 100%).")

    return percentages


def percentile_rank(student_score: int, percentages: dict[int, float]) -> float:
    """
    Midrank percentile: share of students below the score, plus half of those
    with the same score. With percentage inputs this is:
      sum(% for scores < student_score) + 0.5 * (% for student_score)
    """
    below = sum(percentages[score] for score in range(student_score))
    at_score = percentages.get(student_score, 0.0)
    return below + 0.5 * at_score


def main() -> None:
    print("Exam percentile calculator")
    print("=" * 28)

    size_a = read_population_size("A")
    size_b = read_population_size("B")

    percentages_a = read_score_percentages("A")
    percentages_b = read_score_percentages("B")

    student_score = prompt_int("\nNumber of questions this student answered correctly (0-5): ", min_value=0)
    if student_score > 5:
        print("Warning: score is above 5; percentile will treat missing higher scores as 0%.")

    rank_a = percentile_rank(student_score, percentages_a)
    rank_b = percentile_rank(student_score, percentages_b)

    print("\nResults")
    print("-" * 28)
    print(f"Student score: {student_score} / 5")
    print(f"Population A ({size_a:,} students): {rank_a:.1f}th percentile")
    print(f"Population B ({size_b:,} students): {rank_b:.1f}th percentile")
    print(
        "\nInterpretation: a 75th percentile means about 75% of students in that "
        "population scored at or below this student's result."
    )


if __name__ == "__main__":
    main()

"""Validation of classification results against ground truth."""

import logging

import pandas as pd

from .utils import CLASSIFICATION_COLUMNS

logger = logging.getLogger(__name__)

# Columns where multi-value comparison (set-based) applies.
# "Typ zboží" has "alu, plech" but that's a single allowed value, not multi-value.
_MULTI_VALUE_COLUMNS = {"Typ pneumatik", "Cena"}


def compare_cell(pred_val, gt_val, column: str) -> str:
    """Compare a single predicted value against ground truth.

    Returns one of: 'correct', 'incorrect', 'false_positive', 'false_negative'.
    """
    pred_empty = pd.isna(pred_val) or pred_val is None or str(pred_val).strip() == ""
    gt_empty = pd.isna(gt_val) or gt_val is None or str(gt_val).strip() == ""

    if pred_empty and gt_empty:
        return "correct"  # True negative
    if pred_empty and not gt_empty:
        return "false_negative"  # Missed classification
    if not pred_empty and gt_empty:
        return "false_positive"  # Hallucinated classification

    # Both have values — compare
    pred_str = str(pred_val).strip()
    gt_str = str(gt_val).strip()

    if column in _MULTI_VALUE_COLUMNS:
        # Set-based comparison for multi-value fields (order-independent)
        pred_set = {p.strip().lower() for p in pred_str.split(",")}
        gt_set = {p.strip().lower() for p in gt_str.split(",")}
        return "correct" if pred_set == gt_set else "incorrect"
    else:
        # Direct comparison (case-insensitive)
        return "correct" if pred_str.lower() == gt_str.lower() else "incorrect"


def validate_results(
    predictions: pd.DataFrame,
    ground_truth: pd.DataFrame,
    keywords: pd.Series,
) -> dict:
    """Compare predictions against ground truth, return comprehensive report.

    Returns dict with:
        - "per_category": dict of per-category metrics
        - "overall": overall accuracy
        - "mismatches": list of all mismatches
    """
    mismatches = []
    per_category = {}

    for col in CLASSIFICATION_COLUMNS:
        if col not in predictions.columns or col not in ground_truth.columns:
            continue

        counts = {"correct": 0, "incorrect": 0, "false_positive": 0, "false_negative": 0}
        gt_filled = 0

        for idx in ground_truth.index:
            if idx not in predictions.index:
                continue

            pred_val = predictions.loc[idx, col]
            gt_val = ground_truth.loc[idx, col]

            result = compare_cell(pred_val, gt_val, col)
            counts[result] += 1

            if not (pd.isna(gt_val) or gt_val is None or str(gt_val).strip() == ""):
                gt_filled += 1

            if result != "correct":
                mismatches.append({
                    "index": idx,
                    "keyword": str(keywords.loc[idx]) if idx in keywords.index else "?",
                    "column": col,
                    "predicted": pred_val if not pd.isna(pred_val) else None,
                    "ground_truth": gt_val if not pd.isna(gt_val) else None,
                    "error_type": result,
                })

        total = sum(counts.values())
        correct = counts["correct"]
        true_positive = correct - (total - gt_filled - counts["false_positive"])
        # Precision: of those we classified, how many were correct
        predicted_positive = gt_filled - counts["false_negative"] + counts["false_positive"]
        precision = true_positive / predicted_positive if predicted_positive > 0 else 0.0
        # Recall: of those that should be classified, how many did we get
        recall = (gt_filled - counts["false_negative"] - counts["incorrect"]) / gt_filled if gt_filled > 0 else 0.0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0

        per_category[col] = {
            "total_rows": total,
            "gt_filled": gt_filled,
            "correct": correct,
            "incorrect": counts["incorrect"],
            "false_positive": counts["false_positive"],
            "false_negative": counts["false_negative"],
            "accuracy": correct / total if total > 0 else 0.0,
            "precision": precision,
            "recall": recall,
            "f1": f1,
        }

    # Overall accuracy
    total_cells = sum(c["total_rows"] for c in per_category.values())
    total_correct = sum(c["correct"] for c in per_category.values())
    overall_accuracy = total_correct / total_cells if total_cells > 0 else 0.0

    return {
        "per_category": per_category,
        "overall_accuracy": overall_accuracy,
        "total_cells": total_cells,
        "total_correct": total_correct,
        "total_errors": total_cells - total_correct,
        "mismatches": mismatches,
    }


def print_summary(report: dict) -> None:
    """Print a formatted summary table of validation results."""
    print("\n" + "=" * 85)
    print("VALIDATION REPORT")
    print("=" * 85)
    print(
        f"{'Category':<20} {'Accuracy':>8} {'Precision':>9} {'Recall':>8} "
        f"{'F1':>6} {'Errors':>7} {'GT filled':>10}"
    )
    print("-" * 85)

    for col in CLASSIFICATION_COLUMNS:
        if col not in report["per_category"]:
            continue
        m = report["per_category"][col]
        print(
            f"{col:<20} {m['accuracy']:>7.1%} {m['precision']:>9.1%} "
            f"{m['recall']:>7.1%} {m['f1']:>6.1%} {m['incorrect'] + m['false_positive'] + m['false_negative']:>7} "
            f"{m['gt_filled']:>10}"
        )

    print("-" * 85)
    print(
        f"{'OVERALL':<20} {report['overall_accuracy']:>7.1%} "
        f"{'':>9} {'':>8} {'':>6} {report['total_errors']:>7} "
        f"{'':>10}"
    )
    print("=" * 85)


def mismatches_to_dataframe(mismatches: list[dict]) -> pd.DataFrame:
    """Convert mismatch list to a DataFrame for Excel export."""
    if not mismatches:
        return pd.DataFrame(columns=["index", "keyword", "column", "predicted", "ground_truth", "error_type"])
    return pd.DataFrame(mismatches)

"""CLI entry point for the SEO Keyword Classifier."""

import argparse
import logging
import os
import sys

from dotenv import load_dotenv
import pandas as pd

load_dotenv()

from src.utils import (
    load_and_normalize,
    extract_dimensions,
    split_keywords_and_ground_truth,
    select_few_shot_examples,
    CLASSIFICATION_COLUMNS,
    DIMENSION_COLUMNS,
)
from src.classifier import KeywordClassifier
from src.validator import validate_results, print_summary, mismatches_to_dataframe


def setup_logging(log_file: str | None = None) -> None:
    """Configure logging to console and optionally to file."""
    handlers: list[logging.Handler] = [logging.StreamHandler(sys.stdout)]

    if log_file:
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        handlers.append(logging.FileHandler(log_file, encoding="utf-8"))

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
        handlers=handlers,
    )


def save_results(
    df_original: pd.DataFrame,
    predictions: pd.DataFrame,
    dimensions: pd.DataFrame,
    mismatches: list[dict],
    output_path: str,
) -> None:
    """Save classified keywords and mismatch report to Excel."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # Build output DataFrame: original keyword + predictions + dimensions
    output_df = df_original[["Fráze"]].copy()
    for col in CLASSIFICATION_COLUMNS:
        output_df[col] = predictions[col]
    for col in DIMENSION_COLUMNS:
        output_df[col] = dimensions[col]

    mismatch_df = mismatches_to_dataframe(mismatches)

    with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
        output_df.to_excel(writer, sheet_name="Klasifikace", index=False)
        if not mismatch_df.empty:
            mismatch_df.to_excel(writer, sheet_name="Porovnání", index=False)

    logging.getLogger(__name__).info("Results saved to %s", output_path)


def main():
    parser = argparse.ArgumentParser(
        description="SEO Keyword Classifier — classifies Czech keywords into thematic categories using Claude API."
    )
    parser.add_argument(
        "--input", default="data/Pavel_Ungr_Analyza.xlsx",
        help="Input Excel file path (default: data/Pavel_Ungr_Analyza.xlsx)",
    )
    parser.add_argument(
        "--output", default="output/classified_keywords.xlsx",
        help="Output Excel file path (default: output/classified_keywords.xlsx)",
    )
    parser.add_argument(
        "--batch-size", type=int, default=50,
        help="Keywords per API call (default: 50)",
    )
    parser.add_argument(
        "--model", default="claude-sonnet-4-20250514",
        help="Anthropic model to use (default: claude-sonnet-4-20250514)",
    )
    parser.add_argument(
        "--api-key", default=None,
        help="Anthropic API key (or set ANTHROPIC_API_KEY env var)",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Only process the first batch (saves API credits for debugging)",
    )
    parser.add_argument(
        "--validate-only", action="store_true",
        help="Skip classification — validate an existing output file against ground truth",
    )
    parser.add_argument(
        "--log-file", default="output/classifier.log",
        help="Log file path (default: output/classifier.log)",
    )
    args = parser.parse_args()

    setup_logging(args.log_file)
    logger = logging.getLogger(__name__)

    # Enable debug logging for classifier in dry-run mode
    if args.dry_run:
        logging.getLogger("src.classifier").setLevel(logging.DEBUG)

    # --- Step 1: Load and normalize data ---
    logger.info("Loading data from %s", args.input)
    df = load_and_normalize(args.input)
    keywords, ground_truth = split_keywords_and_ground_truth(df)
    dimensions = extract_dimensions(keywords)
    logger.info("Loaded %d keywords, extracted %d dimension rows", len(keywords), dimensions.dropna(how="all").shape[0])

    # --- Step 2: Classify or load existing ---
    if args.validate_only:
        logger.info("Validate-only mode: loading existing predictions from %s", args.output)
        existing = pd.read_excel(args.output, sheet_name="Klasifikace")
        predictions = existing[CLASSIFICATION_COLUMNS]
    else:
        few_shot = select_few_shot_examples(df, n=12)
        classifier = KeywordClassifier(
            api_key=args.api_key,
            model=args.model,
            batch_size=args.batch_size,
        )

        if args.dry_run:
            logger.info("DRY RUN — processing only the first batch")

        predictions = classifier.classify_all(keywords, few_shot, dry_run=args.dry_run)

    # --- Step 3: Validate against ground truth ---
    if args.dry_run:
        # For dry run, only validate the rows we actually classified
        classified_mask = predictions.notna().any(axis=1) | ground_truth.notna().any(axis=1)
        classified_indices = predictions.index[:args.batch_size]
        report = validate_results(
            predictions.loc[classified_indices],
            ground_truth.loc[classified_indices],
            keywords.loc[classified_indices],
        )
    else:
        report = validate_results(predictions, ground_truth, keywords)

    print_summary(report)

    # --- Step 4: Save results ---
    if not args.validate_only:
        save_results(df, predictions, dimensions, report["mismatches"], args.output)

    logger.info("Done. Overall accuracy: %.1f%%", report["overall_accuracy"] * 100)


if __name__ == "__main__":
    main()

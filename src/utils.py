"""Data loading, normalization, and batch utilities."""

import re
import logging

import pandas as pd

logger = logging.getLogger(__name__)

KEYWORD_COLUMN = "Fráze"
SHEET_NAME = "Analýza"

CLASSIFICATION_COLUMNS = [
    "Typ zboží",
    "Výrobce",
    "Značka auta",
    "Typ auta",
    "Typ pneumatik",
    "Cena",
    "Město",
    "Informační",
]

DIMENSION_COLUMNS = ["Šířka", "Výška profilu", "Průměr ráfku"]

# Column name -> {bad_value: corrected_value}
TYPO_MAP = {
    "Informační": {"rezenze": "recenze"},
}

# Regex for tire dimensions like "215 60 15", "205/55/16", "165-70-r13"
_DIMENSION_PATTERN = re.compile(
    r"(?<!\d)(\d{3})\s*[/\-\s]\s*(\d{2,3})\s*[/\-\s]\s*[rR]?(\d{2})(?!\d)"
)


def load_and_normalize(filepath: str) -> pd.DataFrame:
    """Load the Excel file and normalize classification values.

    - Strips trailing whitespace from classification columns ("alu " -> "alu")
    - Applies known typo corrections ("rezenze" -> "recenze")
    """
    df = pd.read_excel(filepath, sheet_name=SHEET_NAME)
    logger.info("Loaded %d rows from sheet '%s'", len(df), SHEET_NAME)

    # Strip trailing/leading whitespace from string classification columns
    for col in CLASSIFICATION_COLUMNS:
        if col in df.columns:
            mask = df[col].notna()
            df.loc[mask, col] = df.loc[mask, col].astype(str).str.strip()

    # Apply typo corrections
    for col, corrections in TYPO_MAP.items():
        if col in df.columns:
            for bad, good in corrections.items():
                count = (df[col] == bad).sum()
                if count > 0:
                    df[col] = df[col].replace(bad, good)
                    logger.info("Fixed typo in '%s': '%s' -> '%s' (%d rows)", col, bad, good, count)

    return df


def extract_dimensions(keywords: pd.Series) -> pd.DataFrame:
    """Extract tire dimensions (width/height/diameter) from keyword text using regex.

    Returns a DataFrame with columns matching DIMENSION_COLUMNS,
    indexed the same as the input Series. NaN where no dimensions found.
    """
    results = []
    for kw in keywords:
        match = _DIMENSION_PATTERN.search(str(kw))
        if match:
            results.append({
                "Šířka": int(match.group(1)),
                "Výška profilu": int(match.group(2)),
                "Průměr ráfku": int(match.group(3)),
            })
        else:
            results.append({
                "Šířka": None,
                "Výška profilu": None,
                "Průměr ráfku": None,
            })

    return pd.DataFrame(results, index=keywords.index)


def split_keywords_and_ground_truth(
    df: pd.DataFrame,
) -> tuple[pd.Series, pd.DataFrame]:
    """Split DataFrame into keywords and ground truth classifications."""
    keywords = df[KEYWORD_COLUMN]
    ground_truth = df[CLASSIFICATION_COLUMNS].copy()
    return keywords, ground_truth


def batch_keywords(
    keywords: pd.Series, batch_size: int = 50
) -> list[list[tuple[int, str]]]:
    """Split keywords into batches, preserving original DataFrame indices.

    Returns list of batches, where each batch is a list of (index, keyword) tuples.
    """
    batches = []
    current_batch = []

    for idx, kw in keywords.items():
        current_batch.append((idx, str(kw)))
        if len(current_batch) >= batch_size:
            batches.append(current_batch)
            current_batch = []

    if current_batch:
        batches.append(current_batch)

    logger.info("Split %d keywords into %d batches (batch_size=%d)", len(keywords), len(batches), batch_size)
    return batches


def select_few_shot_examples(df: pd.DataFrame, n: int = 12) -> list[dict]:
    """Select diverse few-shot examples from the ground truth.

    Picks examples that cover different categories, multi-value cases,
    and edge cases for the best prompt performance.
    """
    # Hand-picked indices for maximum diversity (based on data exploration)
    # These cover: single category, multi-category, multi-value, all 8 category types
    selected_indices = [
        0,     # "pneumatiky" -> Typ zboží: pneumatiky (simple single)
        1,     # "autobaterie 60" -> Typ zboží: baterie
        78,    # "disky na auto" -> Typ zboží: alu, plech (multi-value typ)
        11,    # "osobní pneumatiky" -> Typ zboží: pneumatiky, Typ auta: osobní
        66,    # "letní pneu barum bravuris" -> pneumatiky, Barum, letní (3 categories)
        232,   # "zimní pneu testy" -> pneumatiky, zimní, test (informační)
        419,   # "zimní pneu škoda octavia" -> pneumatiky, Škoda Octavia, zimní
        361,   # "zimní pneu na octavii" -> pneumatiky, Octavia, zimní
        449,   # "pneumatiky praha" -> pneumatiky, Praha (město)
        104,   # "nejlevnější pneu barum" -> pneumatiky, Barum, nejlevnější
        1208,  # "zimní pneu protektor" -> pneumatiky, zimní+protektor (multi-value)
        211,   # "autobaterie banner 72ah" -> baterie, Banner
    ]

    # Limit to n
    selected_indices = selected_indices[:n]

    examples = []
    for idx in selected_indices:
        if idx >= len(df):
            continue
        row = df.iloc[idx]
        classifications = {}
        for col in CLASSIFICATION_COLUMNS:
            val = row[col]
            if pd.notna(val):
                classifications[col] = str(val)

        examples.append({
            "keyword": str(row[KEYWORD_COLUMN]),
            "classifications": classifications,
        })

    logger.info("Selected %d few-shot examples", len(examples))
    return examples

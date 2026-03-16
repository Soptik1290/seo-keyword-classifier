"""Batch keyword classification via Anthropic API."""

import time
import logging

import pandas as pd
import anthropic

from .prompts import (
    SYSTEM_PROMPT,
    KeywordClassification,
    ALLOWED_VALUES,
    FIELD_TO_COLUMN,
    build_user_prompt,
)
from .utils import CLASSIFICATION_COLUMNS, batch_keywords

logger = logging.getLogger(__name__)

# Fields in KeywordClassification that hold classification values
_CLASSIFICATION_FIELDS = list(FIELD_TO_COLUMN.keys())

# Approximate output tokens per keyword classification (~150 tokens each)
_TOKENS_PER_KEYWORD = 150

# Tool definition for structured output via tool_use (works with all Claude models)
_CLASSIFY_TOOL = {
    "name": "save_classifications",
    "description": "Ulož klasifikace klíčových slov. Zavolej tuto funkci s výsledky klasifikace.",
    "input_schema": {
        "type": "object",
        "properties": {
            "classifications": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "keyword": {"type": "string", "description": "Přesný text klíčového slova"},
                        "typ_zbozi": {"type": ["string", "null"], "description": "Typ zboží"},
                        "vyrobce": {"type": ["string", "null"], "description": "Výrobce"},
                        "znacka_auta": {"type": ["string", "null"], "description": "Značka auta"},
                        "typ_auta": {"type": ["string", "null"], "description": "Typ auta"},
                        "typ_pneumatik": {"type": ["string", "null"], "description": "Typ pneumatik"},
                        "cena": {"type": ["string", "null"], "description": "Cenový záměr"},
                        "mesto": {"type": ["string", "null"], "description": "Město"},
                        "informacni": {"type": ["string", "null"], "description": "Informační záměr"},
                    },
                    "required": ["keyword"],
                },
            },
        },
        "required": ["classifications"],
    },
}


def _parse_tool_response(response) -> list[KeywordClassification]:
    """Extract KeywordClassification objects from API tool_use response."""
    classifications = []
    for block in response.content:
        if block.type == "tool_use" and block.name == "save_classifications":
            data = block.input
            for item in data.get("classifications", []):
                cls = KeywordClassification(
                    keyword=item.get("keyword", ""),
                    typ_zbozi=item.get("typ_zbozi"),
                    vyrobce=item.get("vyrobce"),
                    znacka_auta=item.get("znacka_auta"),
                    typ_auta=item.get("typ_auta"),
                    typ_pneumatik=item.get("typ_pneumatik"),
                    cena=item.get("cena"),
                    mesto=item.get("mesto"),
                    informacni=item.get("informacni"),
                )
                classifications.append(cls)
    return classifications


class KeywordClassifier:
    """Classifies SEO keywords in batches using Claude API."""

    def __init__(
        self,
        api_key: str | None = None,
        model: str = "claude-sonnet-4-20250514",
        batch_size: int = 25,
        max_retries: int = 3,
    ):
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = model
        self.batch_size = batch_size
        self.max_retries = max_retries

    def classify_batch(
        self,
        keywords: list[tuple[int, str]],
        few_shot: list[dict],
    ) -> list[KeywordClassification]:
        """Classify a single batch of keywords via one API call.

        Uses tool_use with forced tool choice for structured JSON output.
        If the response is truncated (max_tokens), automatically splits
        the batch in half and retries.
        """
        user_prompt = build_user_prompt(keywords, few_shot)
        max_tokens = len(keywords) * _TOKENS_PER_KEYWORD + 512  # dynamic + buffer

        response = self.client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_prompt}],
            tools=[_CLASSIFY_TOOL],
            tool_choice={"type": "tool", "name": "save_classifications"},
        )

        # Debug: log raw response structure
        logger.debug("Response stop_reason: %s, max_tokens: %d", response.stop_reason, max_tokens)
        for i, block in enumerate(response.content):
            logger.debug("Block %d: type=%s", i, block.type)
            if block.type == "tool_use":
                input_str = str(block.input)
                logger.debug("  Tool input preview: %s", input_str[:300])

        # Handle truncated response — split batch in half and retry
        if response.stop_reason == "max_tokens":
            if len(keywords) <= 5:
                logger.error("Response truncated even with %d keywords. Skipping batch.", len(keywords))
                return []

            mid = len(keywords) // 2
            logger.warning(
                "Response truncated (max_tokens). Splitting batch of %d into %d + %d.",
                len(keywords), mid, len(keywords) - mid,
            )
            first_half = self.classify_batch(keywords[:mid], few_shot)
            second_half = self.classify_batch(keywords[mid:], few_shot)
            return first_half + second_half

        classifications = _parse_tool_response(response)

        # Validate and clean returned values
        classifications = [self._validate_classification(c) for c in classifications]

        return classifications

    def classify_all(
        self,
        keywords: pd.Series,
        few_shot: list[dict],
        dry_run: bool = False,
    ) -> pd.DataFrame:
        """Classify all keywords in batches. Returns DataFrame with classification columns.

        Args:
            keywords: Series of keyword strings with original DataFrame indices.
            few_shot: Few-shot examples for the prompt.
            dry_run: If True, only process the first batch.
        """
        batches = batch_keywords(keywords, self.batch_size)

        if dry_run:
            batches = batches[:1]
            logger.info("Dry-run mode: processing only the first batch (%d keywords)", len(batches[0]))

        all_classifications: dict[int, KeywordClassification] = {}
        total = len(batches)

        for i, batch in enumerate(batches):
            logger.info("Processing batch %d/%d (%d keywords)...", i + 1, total, len(batch))

            classifications = self._call_with_retry(batch, few_shot)

            # Map classifications back to original indices
            if len(classifications) == len(batch):
                for (idx, _kw), cls in zip(batch, classifications):
                    all_classifications[idx] = cls
            else:
                # Fallback: try to match by keyword text
                logger.warning(
                    "Batch %d: expected %d classifications, got %d. Matching by keyword.",
                    i + 1, len(batch), len(classifications),
                )
                kw_to_idx = {kw: idx for idx, kw in batch}
                for cls in classifications:
                    idx = kw_to_idx.get(cls.keyword)
                    if idx is not None:
                        all_classifications[idx] = cls
                    else:
                        logger.warning("Could not match keyword: '%s'", cls.keyword)

            # Brief pause between batches to avoid rate limits
            if i < total - 1:
                time.sleep(1)

        # Convert to DataFrame
        return self._to_dataframe(all_classifications, keywords.index)

    def _call_with_retry(
        self,
        batch: list[tuple[int, str]],
        few_shot: list[dict],
        attempt: int = 0,
    ) -> list[KeywordClassification]:
        """Call classify_batch with exponential backoff retry logic."""
        try:
            return self.classify_batch(batch, few_shot)
        except anthropic.RateLimitError:
            if attempt >= self.max_retries:
                raise
            wait = 2 ** attempt * 10  # 10s, 20s, 40s
            logger.warning("Rate limited. Waiting %ds before retry %d/%d...", wait, attempt + 1, self.max_retries)
            time.sleep(wait)
            return self._call_with_retry(batch, few_shot, attempt + 1)
        except anthropic.APIStatusError as e:
            if e.status_code >= 500 and attempt < self.max_retries:
                wait = 5 * (attempt + 1)
                logger.warning("Server error %d. Waiting %ds before retry %d/%d...", e.status_code, wait, attempt + 1, self.max_retries)
                time.sleep(wait)
                return self._call_with_retry(batch, few_shot, attempt + 1)
            raise
        except anthropic.APIError:
            if attempt < self.max_retries:
                logger.warning("API error. Retrying %d/%d...", attempt + 1, self.max_retries)
                time.sleep(5)
                return self._call_with_retry(batch, few_shot, attempt + 1)
            raise

    def _validate_classification(self, cls: KeywordClassification) -> KeywordClassification:
        """Validate classification values against allowed values.

        Sets invalid values to None and logs warnings.
        """
        for field_name in _CLASSIFICATION_FIELDS:
            value = getattr(cls, field_name)
            if value is None:
                continue

            allowed = ALLOWED_VALUES.get(field_name, [])
            if not allowed:
                continue

            # For multi-value fields, check each part
            if field_name in ("typ_pneumatik", "cena"):
                parts = [p.strip() for p in value.split(",")]
                valid_parts = []
                for part in parts:
                    if part in allowed:
                        valid_parts.append(part)
                    else:
                        logger.warning(
                            "Invalid value '%s' for field '%s' in keyword '%s'. Dropping.",
                            part, field_name, cls.keyword,
                        )
                if valid_parts:
                    setattr(cls, field_name, ", ".join(valid_parts))
                else:
                    setattr(cls, field_name, None)
            else:
                # Single value — check directly
                if value not in allowed:
                    logger.warning(
                        "Invalid value '%s' for field '%s' in keyword '%s'. Setting to null.",
                        value, field_name, cls.keyword,
                    )
                    setattr(cls, field_name, None)

        return cls

    def _to_dataframe(
        self,
        classifications: dict[int, KeywordClassification],
        full_index: pd.Index,
    ) -> pd.DataFrame:
        """Convert classification results to a DataFrame aligned with the original index."""
        rows = []
        for idx in full_index:
            cls = classifications.get(idx)
            if cls is None:
                rows.append({col: None for col in CLASSIFICATION_COLUMNS})
            else:
                row = {}
                for field_name, col_name in FIELD_TO_COLUMN.items():
                    row[col_name] = getattr(cls, field_name)
                rows.append(row)

        return pd.DataFrame(rows, index=full_index, columns=CLASSIFICATION_COLUMNS)

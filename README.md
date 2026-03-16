# SEO Keyword Auto-Classifier

Automated classification of SEO keywords into thematic categories using Claude API (Anthropic). The tool batch-processes thousands of keywords, assigns categories, and validates results against human-labeled ground truth.

Built as a practical demonstration for an AI Specialist role — solving the most time-consuming part of SEO keyword analysis: manual sorting of search queries into thematic groups.

## Results

Tested on a dataset of 1,859 Czech keywords for a tire & battery e-shop (najdi-pneu.cz), compared against manual classification by an SEO specialist:

| Category | Accuracy | Precision | Recall | F1 | Errors |
|-----------|----------|-----------|--------|------|-------|
| Product Type | 91.8% | 93.3% | 97.4% | 95.3% | 153 |
| Manufacturer | 99.6% | 98.7% | 97.9% | 98.3% | 7 |
| Car Brand | 99.7% | 98.7% | 98.2% | 98.4% | 5 |
| Vehicle Type | 99.0% | 65.3% | 94.1% | 77.1% | 19 |
| Tire Type/Season | 98.7% | 94.3% | 98.8% | 96.5% | 24 |
| Price Intent | 98.1% | 73.1% | 90.7% | 81.0% | 36 |
| City | 100.0% | 100.0% | 100.0% | 100.0% | 0 |
| Informational | 97.6% | 69.0% | 74.8% | 71.8% | 44 |
| **Overall** | **98.1%** | | | | **288** |

- 38 API calls (batch size 50), total runtime ~25 minutes
- Model: `claude-sonnet-4-20250514`

## How It Works

```
Excel (keywords) → Normalization → Batch API calls (Claude) → Validation vs. ground truth → Excel output
```

1. **Data loading** — Reads the Excel file ("Analýza" sheet), normalizes values (fixes typos, strips trailing spaces)
2. **Classification** — Keywords are sent in batches to Claude API with a Czech prompt containing allowed values for each category and few-shot examples
3. **Dimension extraction** — Tire dimensions (e.g. 215/60/15) are extracted via regex, not through the LLM
4. **Validation** — Comparison against ground truth: accuracy, precision, recall, F1 per category
5. **Output** — Excel file with two sheets: classifications + mismatch report

## Classification Categories

| Category | Description | Examples |
|-----------|-------------|---------|
| Product Type | Type of product | tires, batteries, alloy wheels, steel wheels |
| Manufacturer | Product brand | Barum, Michelin, Varta, Continental |
| Car Brand | Automobile brand | Škoda Octavia, BMW, Ford |
| Vehicle Type | Type of vehicle | passenger, truck, motorcycle |
| Tire Type | Season / special type | winter, summer, all-season, retread |
| Price Intent | Price-related intent | cheap, sale, cheapest, free shipping |
| City | Location | Praha, Brno, Ostrava |
| Informational | Informational intent | test, review, replacement, labeling |

## Installation

```bash
pip install -r requirements.txt
```

Create a `.env` file with your API key:

```
ANTHROPIC_API_KEY=sk-ant-api03-...
```

## Usage

```bash
# Full run — classify all 1,859 keywords
python main.py

# Dry run — first batch only (25 keywords), saves API credits while debugging
python main.py --dry-run

# Custom input/output
python main.py --input data/my_file.xlsx --output output/result.xlsx

# Validate existing output against ground truth (no API calls)
python main.py --validate-only

# Choose model and batch size
python main.py --model claude-sonnet-4-20250514 --batch-size 25
```

### CLI Arguments

| Argument | Default | Description |
|----------|---------|-------------|
| `--input` | `data/Pavel_Ungr_Analyza.xlsx` | Input Excel file |
| `--output` | `output/classified_keywords.xlsx` | Output Excel file |
| `--batch-size` | `25` | Keywords per API call |
| `--model` | `claude-sonnet-4-20250514` | Claude API model |
| `--api-key` | env `ANTHROPIC_API_KEY` | API key (or via .env) |
| `--dry-run` | – | Process only the first batch |
| `--validate-only` | – | Skip classification, validate only |
| `--log-file` | `output/classifier.log` | Log file path |

## Project Structure

```
├── main.py                  # CLI entry point
├── src/
│   ├── utils.py             # Data loading, normalization, batching, regex dimension extraction
│   ├── prompts.py           # Czech system prompt, Pydantic models, allowed values
│   ├── classifier.py        # Batch processing via Anthropic API (tool_use)
│   └── validator.py         # Ground truth comparison, metrics, mismatch report
├── data/
│   └── Pavel_Ungr_Analyza.xlsx   # Dataset with ground truth (1,859 keywords)
├── output/
│   ├── classified_keywords.xlsx  # Classification output
│   └── classifier.log            # Log file
├── requirements.txt
└── .env                     # API key (not in git)
```

## Technical Approach

### Prompt Engineering
- System prompt written in **Czech** — keywords and categories are all Czech
- Explicit list of allowed values for each of 8 categories
- 12 few-shot examples selected for maximum diversity (covering all categories, multi-value cases, edge cases)
- Disambiguation rules for tricky cases (e.g. "škoda octavia" → "Škoda Octavia" vs. just "octavia" → "Octavia")

### Structured Output
- Uses `tool_use` with `tool_choice` for guaranteed JSON output from any Claude model
- Post-processing validation: invalid values are logged and set to null
- Automatic batch splitting on token limit truncation

### Quality Control
- Cell-by-cell comparison against human-labeled ground truth
- Per-category metrics: accuracy, precision, recall, F1
- Mismatch export to a separate Excel sheet for manual review
- File logging for diagnostics

## Make.com Integration

The tool is designed as the core engine for a Make.com automation workflow:

```
Google Sheets → HTTP webhook → Python classification → Google Sheets output → Slack notification
```

The Python script runs as a standalone service; Make.com handles orchestration.

## Tech Stack

- Python 3.12+
- pandas + openpyxl (data processing)
- anthropic SDK (Claude API)
- python-dotenv (configuration)

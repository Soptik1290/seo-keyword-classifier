# SEO Keyword Auto-Classifier

## Project Goal

Build a Python tool that automatically classifies SEO keywords into thematic categories using an LLM API. This solves the most time-consuming part of SEO keyword analysis — manual categorization of thousands of keywords.

The tool will be wrapped in a Make.com automation workflow as the delivery format.

## Context

This is a practical task for a job application (AI Specialist position at Keypers/Proficio — SEO agency in Prague). The task specifically asks: "How would you automate the sorting of keywords into thematic groups? How would you ensure quality control / error removal?"

## What We're Building

### Phase 1: Python Classification Script
- Input: CSV/XLSX with a column of raw keywords (e.g., "zimní pneumatiky barum", "autobaterie 60", "alu disky škoda octavia")
- Processing: Send keywords in batches to an LLM API (Claude or OpenAI) with a structured prompt
- Output: Same file enriched with classification columns
- Validation: Compare LLM output against human-labeled ground truth to measure accuracy

### Phase 2: Make.com Integration
- The Python script will be called from a Make.com scenario
- Flow: Google Sheets input → Python/API classification → Google Sheets output
- This part will be documented/screenshotted, not necessarily fully coded here

## Dataset

File: `data/Pavel_Ungr_Analyza.xlsx` (copy from uploads)
- Sheet "Analýza" contains 1,859 keywords for a tire/battery e-shop (najdi-pneu.cz)
- Already human-classified — we use this as ground truth to validate our automation

### Classification Categories (from the ground truth)

| Category | Czech Name | Fill Rate | # Unique Values | Description |
|----------|-----------|-----------|-----------------|-------------|
| Product Type | Typ zboží | 94% | 8 | pneumatiky, baterie, alu, plech, disky, příslušenství |
| Manufacturer | Výrobce | 13% | 78 | Michelin, Barum, Continental, Varta, Bosch... |
| Car Brand | Značka auta | 12% | 37 | Škoda, BMW, Ford, Audi, VW... |
| Car Type | Typ auta | 2% | 13 | osobní, nákladní, motocykl, traktor... |
| Tire Season | Typ pneumatik | 22% | 18 | letní, zimní, celoroční, offroad... |
| Price Intent | Cena | 6% | 17 | levné, akce, nejlevnější, bazar... |
| City | Město | 2% | 20 | Praha, Brno, Ostrava, Plzeň... |
| Informational | Informační | 6% | 16 | test, recenze, výměna, značení... |

### Key Insight for Classification Logic
- **Typ zboží** (Product Type) is the most important — 94% fill rate, should always be classified
- **Výrobce** and **Značka auta** are filled only when the keyword explicitly mentions a brand
- **Město** only when a city name appears in the keyword
- Many categories are NaN by design — not every keyword contains every dimension
- Some categories can have multiple values (e.g., "zimní, protektor")

## Technical Approach

### Batch Processing
- Don't send 1,859 keywords one by one — batch them (e.g., 50 per API call)
- Use structured output (JSON) from the LLM for reliable parsing

### Prompt Strategy
- Provide the list of allowed values for each category
- Include few-shot examples from the ground truth
- Instruct the model to return null/empty when a category doesn't apply
- Use Czech language in prompts since keywords are Czech

### Validation Pipeline
1. Run classifier on the full dataset
2. Compare each cell with ground truth
3. Calculate accuracy per category
4. Log mismatches for review

### Error Handling & Quality Control
- Schema validation: ensure LLM returns only allowed category values
- Confidence scoring: flag low-confidence classifications for human review
- Batch retry: re-process failed batches
- Comparison report: show accuracy metrics vs. human-labeled data

## File Structure

```
project/
├── CLAUDE.md              # This file
├── PROJECT_CONTEXT.md     # Full context from planning conversation
├── data/
│   └── Pavel_Ungr_Analyza.xlsx  # Source dataset with ground truth
├── src/
│   ├── classifier.py      # Main classification logic
│   ├── prompts.py         # LLM prompt templates
│   ├── validator.py       # Compare output vs ground truth
│   └── utils.py           # Data loading, batch helpers
├── output/
│   └── classified_keywords.xlsx  # Result file
└── requirements.txt
```

## Tech Stack
- Python 3.12+
- pandas, openpyxl (data handling)
- anthropic or openai SDK (LLM API)
- The user has access to Claude API and/or OpenAI API

## Important Notes
- All keywords and categories are in **Czech language**
- The LLM prompt must be in Czech for best results
- The ground truth has some inconsistencies (e.g., "alu" vs "alu " with trailing space) — handle normalization
- Some ground truth values contain multiple categories separated by comma (e.g., "zimní, protektor")
- The goal is NOT 100% accuracy — it's to show the approach is viable and saves significant time vs. manual work

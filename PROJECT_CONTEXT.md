# Project Context: SEO Keyword Auto-Classifier

## Background — The Job Application

**Company:** Keypers (SEO brand of Proficio group)
**Position:** AI Specialist
**Job listing:** https://www.startupjobs.cz/nabidka/101737/ai-specialist

### What they're looking for:
- Working with LLMs via API (not just ChatGPT window)
- Building automations in Make.com / n8n
- Python scripting for data processing & API integration
- "Vibe coding" and rapid prototyping of internal tools
- SEO/GEO context understanding

### The 3 tasks in the application:
1. **Keyword Analysis Automation** ← WE ARE DOING THIS ONE PRACTICALLY
2. **Bulk Translation Pipeline** (described only)
3. **AI Discoverability Monitoring** (described only)

---

## Task 1: Keyword Analysis — Full Brief

From the PDF assignment:

> "Analýza klíčových slov je základním dokumentem využívaným v rámci SEO rozvoje klientů. Jedná se o tabulku, kde jsou jednotlivé výrazy členěny do tematických celků. Právě třídění dotazů do tematických celků je časově nejvíce náročnou činností."
>
> "Jakými způsoby byste postupoval ve snaze o automatizaci tohoto třídění? A jakými způsoby byste zajistil kontroly/odstranění chybovosti?"

**Translation:** Keyword analysis is a fundamental document used in SEO development. It's a table where individual search terms are organized into thematic groups. The sorting of queries into thematic groups is the most time-consuming activity. How would you automate this? How would you ensure quality control?

**Reference article:** https://www.marketingminer.com/cs/blog/analyza-klicovych-slov

---

## The Dataset: Pavel Ungr's Keyword Analysis

**File:** `data/Pavel_Ungr_Analyza.xlsx`
**Source:** Example analysis from the Marketing Miner blog article (publicly available)
**Domain:** najdi-pneu.cz (tire and battery e-shop)

### Sheet Structure:

**Sheet "Sběr dat"** (Data Collection) — 5,260 raw keywords from various sources:
- Vlastní web a návrhy (own website + suggestions)
- Konkurence (competitors)  
- Google Webmaster Tools
- Google Analytics
- Online návrhy (online suggestions)
- Schválené (approved)

**Sheet "Analýza"** (Analysis) — 1,859 cleaned & classified keywords with columns:
- `Fráze` — the keyword itself
- `Vstupní stránka` — landing page URL
- `AdWords` — search volume from AdWords
- `Konkurence` — competition percentage
- `Sklik` — search volume from Sklik (Czech ad system)
- `S. konkurence` — Sklik competition
- `Hledanost` — actual search volume
- `Konkurence2` — competition score (0-1)
- `Relevance` — relevance score (0-1)
- `Důležitost` — importance score (calculated)
- **Classification columns (our target):**
  - `Typ zboží` — Product type (94% filled)
  - `Výrobce` — Manufacturer (13% filled)
  - `Značka auta` — Car brand (12% filled)
  - `Typ auta` — Vehicle type (2% filled)
  - `Typ pneumatik` — Tire type/season (22% filled)
  - `Cena` — Price intent (6% filled)
  - `Město` — City (2% filled)
  - `Informační` — Informational intent (6% filled)
  - `Šířka`, `Výška profilu`, `Průměr ráfku` — Tire dimensions (numeric)
  - `Parametry` — Other parameters (2% filled)

### Complete Category Values (Ground Truth)

**Typ zboží (8 values):**
pneumatiky, baterie, alu, alu (with trailing space), alu/plech, disky, plech, příslušenství

**Výrobce (78 values):**
ABX, AEZ, AGM, AK Power, AKU, Akuma, Banner, Barum, Bear Power, Black Horse, Bosch, Bridgestone, Brit, Carfit, Carmani, Caryon, Combatt, Continental, Dare, Delkor, Delphi, Dezent, Dotz, Dunlop, Duracell, Enzo, Euro Power, Exide, Faam, Fiamm, Fiat, Firestone, Firstop, GS, Galaxy, Goodyear, Hagen, Kosei, Laurin a Klement, MAK, Maff, Mammut, Matador, Megalite, Meyle, Michelin, Midac, Milano, Moll, Motorcraft, Nexen, Nokian, Panasonic, Pema, Perion, Power, Proforce, RS, Rial, Rocket, Sailun, Sava, Semperit, Solite, Stabat, Starline, Starter Plus, Superstart, TAB, Tesla, Tollinger, Topla, Tudor, Turbine, Varta, Yuasa, Zap, Zenith

**Značka auta (37 values):**
Alfa Romeo, Audi, Avia, BMW, Citroen, Dacia, Daewoo, Enduro, Fabia, Felicia, Ford, Honda, Hyundai, Ifa, Kia, Lada, Mazda, Mercedes, Octavia, Opel, Peugeot, Praga V3S, Renault, Seat, Superb, Suzuki, Tatra, Toyota, Trabant, UAZ, UNC, Volkswagen, Škoda, Škoda Fabia, Škoda Felicia, Škoda Octavia, Škoda Superb

**Typ auta (13 values):**
ATV, bantam, dodávka, jeep, kolo, motocykl, motorka, multicar, nákladní, osobní, traktor, vozík, čtyřkolka

**Typ pneumatik (18 values):**
bezdušové, bezúdržbová, celoroční, dojezdová, gelová, hroty, letní, offroad, protektor, s hřeby, sportovní, univerzální, zimní, zimní+hroty, zimní+letní, zimní+protektor, závodní, šípové

**Cena (17 values):**
akce, bazar, cena, ceník, doprava zdarma, kvalitní, levné, levné+doprava zdarma, levné+výprodej, nejlepší, nejlevnější, nejlevnější+doprava zdarma, nejlevnější+výprodej, splátky, top, velkoobchod, výprodej

**Město (20 values):**
Beroun, Brno, Havířov, Hradec Králové, Jihlava, Karlovy Vary, Kladno, Liberec, Modletice, Olomouc, Opava, Ostopovice, Ostrava, Pardubice, Plzeň, Praha, Sviadnov, Vlachovo Březí, Česká Lípa, České Budějovice

**Informační (16 values):**
povinnost, péče, přezutí, recenze, rezenze, test, tlak, vlastnosti, vyhláška, využití, vzorek, výběr, výměna, výrobce, značení, časopis

### Sample Keywords with Classifications

```
"pneumatiky"                    → Typ zboží: pneumatiky
"autobaterie 60"                → Typ zboží: baterie
"215 60 15"                     → Typ zboží: pneumatiky (+ dimensions: 215/60/15)
"cena pneumatik"                → Typ zboží: pneumatiky, Cena: cena
"nejlepší letní pneu"           → Typ zboží: pneumatiky, Typ pneumatik: letní
"pneumatiky semperit"           → Typ zboží: pneumatiky, Výrobce: Semperit
"pneu zimni 215 55 16"         → Typ zboží: pneumatiky, Typ pneumatik: zimní
"alu disky škoda octavia"       → Typ zboží: alu, Značka auta: Škoda Octavia
"levné pneumatiky praha"        → Typ zboží: pneumatiky, Cena: levné, Město: Praha
"test zimních pneumatik"        → Informační: test, Typ pneumatik: zimní
"autobaterie varta 12v 74ah"   → Typ zboží: baterie, Výrobce: Varta
```

---

## Implementation Plan

### Step 1: Data Loading & Preparation
- Load the Excel file, extract "Analýza" sheet
- Clean data (normalize whitespace, handle "alu " vs "alu")
- Split into: input (just keywords) and ground truth (classifications)

### Step 2: LLM Classification
- Build a prompt that provides:
  - List of all allowed values per category
  - 10-15 few-shot examples from ground truth
  - Clear instructions: return JSON, use null when category doesn't apply
- Process keywords in batches of ~50
- Parse JSON responses, handle errors
- API: use Claude (anthropic SDK) or OpenAI — user has access to both

### Step 3: Validation & Accuracy Report
- Compare LLM output cell-by-cell against ground truth
- Calculate per-category accuracy
- Generate a summary report
- Flag mismatches for review

### Step 4: Output
- Write classified keywords to a new Excel file
- Include an accuracy comparison sheet

---

## How This Fits Into Make.com

The end-to-end workflow in Make.com would be:
1. **Trigger:** New file in Google Drive / Google Sheets updated
2. **Read:** Fetch keyword data from the source
3. **Process:** Call the Python classification script (via HTTP webhook or custom function)
4. **Write:** Save results back to Google Sheets / Drive
5. **Notify:** Send Slack/email notification with accuracy stats

The Python script is the core intelligence. Make.com is the orchestration layer.

---

## Notes for Development

- All prompts should be in **Czech** for best classification accuracy
- Watch out for rate limits when batch-processing 1,859 keywords
- The LLM doesn't need to extract tire dimensions (Šířka, Výška, Průměr) — those can be done with regex more reliably
- Some ground truth values have inconsistencies to be aware of:
  - "alu" vs "alu " (trailing space)
  - "rezenze" is likely a typo for "recenze"
  - Some Značka auta values overlap (e.g., "Fabia" vs "Škoda Fabia")
- Cost estimate: ~1,859 keywords / 50 per batch = ~37 API calls. Very affordable.

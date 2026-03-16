"""Czech prompt templates, Pydantic models, and allowed values for keyword classification."""

from typing import Optional

from pydantic import BaseModel


# ---------------------------------------------------------------------------
# Pydantic models for structured output via messages.parse()
# ---------------------------------------------------------------------------

class KeywordClassification(BaseModel):
    """Classification of a single SEO keyword."""
    keyword: str
    typ_zbozi: Optional[str] = None
    vyrobce: Optional[str] = None
    znacka_auta: Optional[str] = None
    typ_auta: Optional[str] = None
    typ_pneumatik: Optional[str] = None
    cena: Optional[str] = None
    mesto: Optional[str] = None
    informacni: Optional[str] = None


class BatchClassificationResult(BaseModel):
    """Classification results for a batch of keywords."""
    classifications: list[KeywordClassification]


# ---------------------------------------------------------------------------
# Field name mapping: Pydantic field -> Czech column name
# ---------------------------------------------------------------------------

FIELD_TO_COLUMN = {
    "typ_zbozi": "Typ zboží",
    "vyrobce": "Výrobce",
    "znacka_auta": "Značka auta",
    "typ_auta": "Typ auta",
    "typ_pneumatik": "Typ pneumatik",
    "cena": "Cena",
    "mesto": "Město",
    "informacni": "Informační",
}

COLUMN_TO_FIELD = {v: k for k, v in FIELD_TO_COLUMN.items()}


# ---------------------------------------------------------------------------
# Allowed values per category (for post-processing validation)
# ---------------------------------------------------------------------------

ALLOWED_VALUES = {
    "typ_zbozi": [
        "pneumatiky", "baterie", "alu", "alu, plech", "disky", "plech", "příslušenství",
    ],
    "vyrobce": [
        "ABX", "AEZ", "AGM", "AK Power", "AKU", "Akuma", "Banner", "Barum",
        "Bear Power", "Black Horse", "Bosch", "Bridgestone", "Brit", "Carfit",
        "Carmani", "Caryon", "Combatt", "Continental", "Dare", "Delkor", "Delphi",
        "Dezent", "Dotz", "Dunlop", "Duracell", "Enzo", "Euro Power", "Exide",
        "Faam", "Fiamm", "Fiat", "Firestone", "Firstop", "GS", "Galaxy",
        "Goodyear", "Hagen", "Kosei", "Laurin a Klement", "MAK", "Maff",
        "Mammut", "Matador", "Megalite", "Meyle", "Michelin", "Midac", "Milano",
        "Moll", "Motorcraft", "Nexen", "Nokian", "Panasonic", "Pema", "Perion",
        "Power", "Proforce", "RS", "Rial", "Rocket", "Sailun", "Sava",
        "Semperit", "Solite", "Stabat", "Starline", "Starter Plus", "Superstart",
        "TAB", "Tesla", "Tollinger", "Topla", "Tudor", "Turbine", "Varta",
        "Yuasa", "Zap", "Zenith",
    ],
    "znacka_auta": [
        "Alfa Romeo", "Audi", "Avia", "BMW", "Citroen", "Dacia", "Daewoo",
        "Enduro", "Fabia", "Felicia", "Ford", "Honda", "Hyundai", "Ifa", "Kia",
        "Lada", "Mazda", "Mercedes", "Octavia", "Opel", "Peugeot", "Praga V3S",
        "Renault", "Seat", "Superb", "Suzuki", "Tatra", "Toyota", "Trabant",
        "UAZ", "UNC", "Volkswagen", "Škoda", "Škoda Fabia", "Škoda Felicia",
        "Škoda Octavia", "Škoda Superb",
    ],
    "typ_auta": [
        "ATV", "bantam", "dodávka", "jeep", "kolo", "motocykl", "motorka",
        "multicar", "nákladní", "osobní", "traktor", "vozík", "čtyřkolka",
    ],
    "typ_pneumatik": [
        "bezdušové", "bezúdržbová", "celoroční", "dojezdová", "gelová", "hroty",
        "letní", "offroad", "protektor", "s hřeby", "sportovní", "univerzální",
        "zimní", "závodní", "šípové",
    ],
    "cena": [
        "akce", "bazar", "cena", "ceník", "doprava zdarma", "kvalitní", "levné",
        "nejlepší", "nejlevnější", "splátky", "top", "velkoobchod", "výprodej",
    ],
    "mesto": [
        "Beroun", "Brno", "Havířov", "Hradec Králové", "Jihlava", "Karlovy Vary",
        "Kladno", "Liberec", "Modletice", "Olomouc", "Opava", "Ostopovice",
        "Ostrava", "Pardubice", "Plzeň", "Praha", "Sviadnov", "Vlachovo Březí",
        "Česká Lípa", "České Budějovice",
    ],
    "informacni": [
        "povinnost", "péče", "přezutí", "recenze", "test", "tlak", "vlastnosti",
        "vyhláška", "využití", "vzorek", "výběr", "výměna", "výrobce", "značení",
        "časopis",
    ],
}


# ---------------------------------------------------------------------------
# System prompt (Czech)
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """\
Jsi odborný SEO klasifikátor klíčových slov pro český e-shop s pneumatikami a autobateriemi (najdi-pneu.cz).

Tvým úkolem je klasifikovat každé klíčové slovo do 8 kategorií. Pro každou kategorii vrať jednu z povolených hodnot, nebo null pokud kategorie na dané klíčové slovo neplatí.

## Kategorie a povolené hodnoty

### 1. typ_zbozi (Typ zboží — typ produktu)
Povolené hodnoty: pneumatiky, baterie, alu, alu, plech, disky, plech, příslušenství
- „pneumatiky" = pneu, pneumatiky, gumy, guma na auto, zimní/letní pneu
- „baterie" = autobaterie, akumulátory, baterie do auta
- „alu" = hliníkové disky, alu kola, litá kola, litá
- „alu, plech" = použij když klíčové slovo mluví obecně o „discích" bez specifikace materiálu (alu nebo plech)
- „disky" = obecný výraz pro disky
- „plech" = plechové disky, ocelové disky
- „příslušenství" = řetězy, sněhové řetězy, doplňky

### 2. vyrobce (Výrobce — značka výrobce produktu)
Povolené hodnoty: ABX, AEZ, AGM, AK Power, AKU, Akuma, Banner, Barum, Bear Power, Black Horse, Bosch, Bridgestone, Brit, Carfit, Carmani, Caryon, Combatt, Continental, Dare, Delkor, Delphi, Dezent, Dotz, Dunlop, Duracell, Enzo, Euro Power, Exide, Faam, Fiamm, Fiat, Firestone, Firstop, GS, Galaxy, Goodyear, Hagen, Kosei, Laurin a Klement, MAK, Maff, Mammut, Matador, Megalite, Meyle, Michelin, Midac, Milano, Moll, Motorcraft, Nexen, Nokian, Panasonic, Pema, Perion, Power, Proforce, RS, Rial, Rocket, Sailun, Sava, Semperit, Solite, Stabat, Starline, Starter Plus, Superstart, TAB, Tesla, Tollinger, Topla, Tudor, Turbine, Varta, Yuasa, Zap, Zenith
- Vyplň pouze pokud klíčové slovo explicitně zmiňuje název výrobce.

### 3. znacka_auta (Značka auta)
Povolené hodnoty: Alfa Romeo, Audi, Avia, BMW, Citroen, Dacia, Daewoo, Enduro, Fabia, Felicia, Ford, Honda, Hyundai, Ifa, Kia, Lada, Mazda, Mercedes, Octavia, Opel, Peugeot, Praga V3S, Renault, Seat, Superb, Suzuki, Tatra, Toyota, Trabant, UAZ, UNC, Volkswagen, Škoda, Škoda Fabia, Škoda Felicia, Škoda Octavia, Škoda Superb
- DŮLEŽITÉ pravidlo pro Škoda modely:
  - „škoda octavia" nebo „škoda octavie" v klíčovém slově → použij „Škoda Octavia"
  - jen „octavia" nebo „octavie" bez „škoda" → použij „Octavia"
  - „škoda fabia" → „Škoda Fabia"; jen „fabia" → „Fabia"
  - „škoda felicia" → „Škoda Felicia"; jen „felicia" → „Felicia"
  - „škoda superb" → „Škoda Superb"; jen „superb" → „Superb"
  - jen „škoda" bez modelu → „Škoda"

### 4. typ_auta (Typ auta — typ vozidla)
Povolené hodnoty: ATV, bantam, dodávka, jeep, kolo, motocykl, motorka, multicar, nákladní, osobní, traktor, vozík, čtyřkolka
- Vyplň pouze pokud klíčové slovo explicitně zmiňuje typ vozidla.

### 5. typ_pneumatik (Typ pneumatik — sezóna nebo speciální typ)
Povolené hodnoty: bezdušové, bezúdržbová, celoroční, dojezdová, gelová, hroty, letní, offroad, protektor, s hřeby, sportovní, univerzální, zimní, závodní, šípové
- Pokud klíčové slovo zmiňuje více typů, kombinuj je čárkou: „zimní, protektor" nebo „zimní, hroty"
- „bezúdržbová" a „gelová" se vztahují k bateriím, ne k pneumatikám.

### 6. cena (Cena — cenový záměr uživatele)
Povolené hodnoty: akce, bazar, cena, ceník, doprava zdarma, kvalitní, levné, nejlepší, nejlevnější, splátky, top, velkoobchod, výprodej
- Pokud klíčové slovo zmiňuje více cenových záměrů, kombinuj: „levné, doprava zdarma" nebo „nejlevnější, výprodej"

### 7. mesto (Město)
Povolené hodnoty: Beroun, Brno, Havířov, Hradec Králové, Jihlava, Karlovy Vary, Kladno, Liberec, Modletice, Olomouc, Opava, Ostopovice, Ostrava, Pardubice, Plzeň, Praha, Sviadnov, Vlachovo Březí, Česká Lípa, České Budějovice
- Vyplň pouze pokud klíčové slovo explicitně zmiňuje město.
- Pozor na zkratky: „cb" = „České Budějovice", „hk" = „Hradec Králové", „kv" = „Karlovy Vary"

### 8. informacni (Informační záměr)
Povolené hodnoty: povinnost, péče, přezutí, recenze, test, tlak, vlastnosti, vyhláška, využití, vzorek, výběr, výměna, výrobce, značení, časopis

## Pravidla
1. Většina kategorií bude null — ne každé klíčové slovo obsahuje informaci o výrobci, městě atd.
2. typ_zbozi by měl být vyplněn téměř vždy (pokud je jasné, o jaký typ produktu jde).
3. Používej POUZE povolené hodnoty. Pokud si nejsi jistý, vrať null.
4. Ignoruj číselné rozměry pneumatik (např. „215 60 15", „205/55 r16") — ty se zpracovávají zvlášť.
5. Pro více hodnot v jedné kategorii je odděl čárkou a mezerou: „zimní, protektor".
6. Vrať přesně tolik klasifikací, kolik je klíčových slov na vstupu.
"""


# ---------------------------------------------------------------------------
# User prompt builder
# ---------------------------------------------------------------------------

def build_user_prompt(
    keywords: list[tuple[int, str]],
    few_shot_examples: list[dict],
) -> str:
    """Build the user message for a batch of keywords.

    Args:
        keywords: List of (index, keyword_text) tuples.
        few_shot_examples: List of dicts with "keyword" and "classifications" keys.
    """
    # Few-shot examples section
    parts = ["## Příklady klasifikace\n"]
    for ex in few_shot_examples:
        cls = ex["classifications"]
        # Map Czech column names to Pydantic field names for the prompt
        cls_items = []
        for col_name, value in cls.items():
            field_name = COLUMN_TO_FIELD.get(col_name, col_name)
            cls_items.append(f"{field_name}: \"{value}\"")
        cls_str = ", ".join(cls_items)
        parts.append(f"Klíčové slovo: \"{ex['keyword']}\"")
        parts.append(f"→ {cls_str}")
        # Show null fields explicitly for first few examples
        parts.append("")

    # Keywords to classify
    parts.append("\n## Klíčová slova ke klasifikaci\n")
    for idx, kw in keywords:
        parts.append(f"- {kw}")

    parts.append(
        "\nKlasifikuj každé klíčové slovo výše. Pro každé vrať objekt s polem "
        "\"keyword\" (přesně text klíčového slova) a klasifikačními poli. "
        "Kategorie které se neaplikují nastav na null."
    )

    return "\n".join(parts)

# Lalka Knowledge Graph

**Lalka Knowledge Graph** to eksperymentalny projekt wykorzystujący dane z Polska Bibliografia Literacka (PBL) do przedstawienia informacji o powieści **„Lalka” Bolesława Prusa i jej adaptacjach** w postaci grafu wiedzy.

Projekt pokazuje, w jaki sposób dane bibliograficzne mogą zostać przekształcone z tradycyjnej struktury rekordów w model relacji między utworami, osobami, adaptacjami i innymi obiektami bibliograficznymi.

## Cel projektu

Celem projektu jest eksperymentalne wykorzystanie danych PBL do budowy grafu wiedzy, który pozwala spojrzeć na informacje bibliograficzne nie tylko jako na zbiór rekordów, ale jako na **sieć powiązanych obiektów i relacji**.

Na przykładzie „Lalki” projekt łączy:

* utwór literacki,
* jego twórcę,
* adaptacje ekranowe,
* rekordy bibliograficzne dotyczące adaptacji,
* autorów rekordów,
* źródła bibliograficzne.

Projekt ma charakter badawczo-eksperymentalny. Jego celem nie jest zastąpienie istniejącej struktury PBL, lecz sprawdzenie, jak można wykorzystać istniejące dane do budowy alternatywnego modelu ich prezentacji.

## Źródło danych

Podstawowym źródłem danych jest **Polska Bibliografia Literacka**:

https://pbl.ibl.poznan.pl/

Dane wykorzystane w projekcie pochodzą z bazy PBL i zostały wyodrębnione na potrzeby eksperymentu z grafem wiedzy.

Projekt nie modyfikuje danych źródłowych PBL. Dane są przekształcane do kolejnych warstw przeznaczonych do analizy i wizualizacji.

## Struktura projektu

```text
lalka-knowledge-graph/
│
├── data/
│   ├── lalka_graph.json
│   └── lalka_presentation_graph.json
│
├── scripts/
│   ├── extract_lalka.py
│   ├── inspect_lalka.py
│   └── build_presentation_graph.py
│
├── docs/
│   └── ...
│
└── README.md
```

### `data/lalka_graph.json`

Pełniejszy graf danych wyodrębnionych z PBL.

Zawiera m.in. techniczne typy obiektów i relacje wynikające ze struktury danych PBL.

### `data/lalka_presentation_graph.json`

Uproszczona **warstwa prezentacyjna** grafu.

Jej zadaniem jest przekształcenie technicznej struktury PBL w model łatwiejszy do wykorzystania podczas wizualizacji i eksploracji.

## Model grafu

W warstwie prezentacyjnej wykorzystywane są m.in. następujące typy węzłów:

* `Work` – utwór literacki,
* `Person` – osoba,
* `Adaptation` – adaptacja,
* `Publication` – publikacja,
* `Event` – wydarzenie,
* `RelatedRecord` – powiązany rekord,
* `Publisher` – wydawca,
* `Source` – źródło bibliograficzne.

Najważniejsze relacje to:

```text
CREATED_BY
ADAPTED_AS
RELATED_TO
AUTHORED_BY
PUBLISHED_BY
FROM_SOURCE
HAS_RECORD
```

Przykładowa struktura:

```text
Lalka
  │
  ├── CREATED_BY ──→ Bolesław Prus
  │
  ├── ADAPTED_AS ──→ Lalka
  │                    │
  │                    └── HAS_RECORD ──→ rekord bibliograficzny
  │
  └── ADAPTED_AS ──→ Lalka (TV)
                       │
                       └── HAS_RECORD ──→ rekord bibliograficzny
```

Część relacji w warstwie prezentacyjnej wynika bezpośrednio ze struktury PBL, natomiast niektóre relacje zostały **zweryfikowane i dodane ręcznie**, jeśli nie można było ich jednoznacznie odtworzyć z hierarchii rekordów.

## Warstwy danych

Projekt rozdziela dane źródłowe od sposobu ich prezentacji.

```text
PBL
 │
 ▼
Ekstrakcja danych
 │
 ▼
lalka_graph.json
 │
 ▼
warstwa prezentacyjna
 │
 ▼
lalka_presentation_graph.json
 │
 ▼
wizualizacja
```

Takie rozdzielenie pozwala zachować oryginalny graf i niezależnie eksperymentować z jego prezentacją.

## Wizualizacja

Wizualizacja interaktywnego grafu jest obecnie rozwijana.

Docelowo projekt będzie umożliwiał eksplorowanie zależności między „Lalką”, jej adaptacjami oraz powiązanymi rekordami bibliograficznymi bez konieczności bezpośredniej pracy z surowymi danymi PBL.

## Status projektu

Projekt jest w fazie eksperymentalnej.

Obecnie przygotowane są:

* ekstrakcja danych dotyczących „Lalki” z PBL,
* podstawowy graf danych,
* inspekcja i analiza struktury danych,
* warstwa prezentacyjna grafu,
* ręczna weryfikacja wybranych relacji dotyczących adaptacji.

Kolejnym etapem jest przygotowanie interaktywnej wizualizacji grafu.

## Dlaczego PBL jako graf?

Tradycyjny rekord bibliograficzny opisuje konkretny obiekt i jego właściwości. Dane PBL zawierają jednak również informacje o relacjach między rekordami, osobami, utworami, źródłami i innymi elementami.

Graf wiedzy pozwala potraktować te relacje jako podstawowy element modelu:

```text
obiekt → relacja → obiekt
```

Dzięki temu możliwe jest przejście od pytania:

> „Co znajduje się w tym rekordzie?”

do pytań takich jak:

> „Jakie obiekty są powiązane z tym utworem?”

> „Jakie adaptacje zostały zarejestrowane w PBL?”

> „Jakie rekordy bibliograficzne dotyczą konkretnej adaptacji?”

Projekt jest próbą sprawdzenia, jak taka zmiana perspektywy wpływa na sposób eksplorowania danych bibliograficznych.

## Technologie

Projekt wykorzystuje m.in.:

* Python,
* SQL,
* JSON,
* NetworkX,
* dane z bazy PBL,
* GitHub / GitHub Pages.

## Źródło danych i kontekst bibliograficzny

Polska Bibliografia Literacka jest prowadzona przez Pracownię Bibliografii Bieżącej Instytutu Badań Literackich PAN.

Projekt wykorzystuje dane PBL jako materiał do eksperymentu z modelowaniem i wizualizacją danych bibliograficznych.


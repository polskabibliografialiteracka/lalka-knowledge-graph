# Lalka Knowledge Graph

**Lalka Knowledge Graph** to eksperymentalny projekt wykorzystujący dane z **Polskiej Bibliografii Literackiej (PBL)** do przedstawienia informacji o powieści **„Lalka” Bolesława Prusa i jej adaptacjach** w postaci grafu wiedzy.

Projekt pokazuje, w jaki sposób dane bibliograficzne mogą zostać przekształcone z tradycyjnej struktury rekordów w model oparty na relacjach między utworami, osobami, adaptacjami i innymi obiektami bibliograficznymi.

## Interaktywna wizualizacja

Graf można obejrzeć bezpośrednio w przeglądarce:

**[Lalka Knowledge Graph – interaktywna wizualizacja](https://polskabibliografialiteracka.github.io/lalka-knowledge-graph/lalka_graph.html)**

Wizualizacja jest udostępniona za pomocą GitHub Pages.

## Cel projektu

Celem projektu jest eksperymentalne wykorzystanie danych PBL do budowy grafu wiedzy, który pozwala spojrzeć na informacje bibliograficzne nie tylko jako na zbiór rekordów, ale jako na **sieć powiązanych obiektów i relacji**.

Na przykładzie „Lalki” projekt łączy m.in.:

* utwór literacki,
* jego twórcę,
* adaptacje ekranowe,
* rekordy bibliograficzne dotyczące adaptacji,
* autorów rekordów,
* źródła bibliograficzne.

Projekt ma charakter badawczo-eksperymentalny. Jego celem nie jest zastąpienie istniejącej struktury PBL, lecz sprawdzenie, jak istniejące dane bibliograficzne można wykorzystać do budowy alternatywnego modelu ich prezentacji i eksploracji.

## Źródło danych

Podstawowym źródłem danych jest **Polska Bibliografia Literacka (PBL)**:

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
│   ├── index.html
│   └── lalka_graph.html
│
└── README.md
```

### `data/lalka_graph.json`

Pełniejszy graf danych wyodrębnionych z PBL.

Zawiera techniczne typy obiektów oraz relacje wynikające ze struktury danych źródłowych.

### `data/lalka_presentation_graph.json`

Uproszczona **warstwa prezentacyjna** grafu.

Jej zadaniem jest przekształcenie technicznej struktury PBL w model łatwiejszy do wykorzystania podczas wizualizacji i eksploracji.

Warstwa prezentacyjna nie zastępuje grafu źródłowego. Jest jego interpretacją przygotowaną na potrzeby konkretnego sposobu prezentacji danych.

## Model grafu

W warstwie prezentacyjnej wykorzystywany jest uproszczony zestaw typów węzłów:

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

Przykładowa struktura grafu:

```text
Lalka
 │
 ├── CREATED_BY ──→ Bolesław Prus
 │
 ├── ADAPTED_AS ──→ Lalka
 │                      │
 │                      └── HAS_RECORD ──→ rekord bibliograficzny
 │
 └── ADAPTED_AS ──→ Lalka (TV)
                        │
                        └── HAS_RECORD ──→ rekord bibliograficzny
```

W przypadku rekordów podrzędnych zachowywana jest informacja o ich pochodzeniu z hierarchii PBL, ale relacja techniczna `CHILD_OF` nie jest prezentowana użytkownikowi jako element modelu.

Część relacji w warstwie prezentacyjnej wynika bezpośrednio ze struktury PBL. Niektóre relacje dotyczące adaptacji zostały **zweryfikowane i dodane ręcznie**, ponieważ nie można było ich jednoznacznie odtworzyć z samej hierarchii rekordów.

Informacja o ręcznie dodanych relacjach jest zachowywana w metadanych grafu.

## Warstwy danych

Projekt rozdziela dane źródłowe od sposobu ich prezentacji:

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
Warstwa prezentacyjna
 │
 ▼
lalka_presentation_graph.json
 │
 ▼
Wizualizacja
```

Takie rozdzielenie pozwala zachować oryginalny graf i niezależnie eksperymentować z jego interpretacją oraz sposobem prezentacji.

## Wizualizacja

Interaktywna wizualizacja wykorzystuje dane z warstwy prezentacyjnej.

Jej zadaniem jest umożliwienie użytkownikowi eksplorowania zależności między:

* „Lalką” jako utworem,
* Bolesławem Prusem,
* adaptacjami ekranowymi,
* rekordami bibliograficznymi,
* autorami rekordów,
* źródłami bibliograficznymi.

**[Otwórz interaktywny graf](https://polskabibliografialiteracka.github.io/lalka-knowledge-graph/lalka_graph.html)**

## Status projektu

Projekt znajduje się w fazie eksperymentalnej.

Obecnie przygotowane są:

* ekstrakcja danych dotyczących „Lalki” z PBL,
* podstawowy graf danych,
* inspekcja i analiza struktury danych,
* warstwa prezentacyjna grafu,
* ręczna weryfikacja wybranych relacji dotyczących adaptacji,
* interaktywna wizualizacja dostępna przez GitHub Pages.

Projekt jest rozwijany iteracyjnie. Model grafu oraz sposób jego wizualizacji mogą ulegać zmianom wraz z kolejnymi etapami eksperymentu.

## Dlaczego PBL jako graf?

Tradycyjny rekord bibliograficzny opisuje konkretny obiekt i jego właściwości. Dane PBL zawierają jednak również informacje o relacjach między rekordami, osobami, utworami, źródłami i innymi elementami.

Graf wiedzy pozwala potraktować te relacje jako jeden z podstawowych elementów modelu:

```text
obiekt → relacja → obiekt
```

Dzięki temu możliwe jest przejście od pytania:

> „Co znajduje się w tym rekordzie?”

do pytań takich jak:

> „Jakie obiekty są powiązane z tym utworem?”

> „Jakie adaptacje zostały zarejestrowane w PBL?”

> „Jakie rekordy bibliograficzne dotyczą konkretnej adaptacji?”

Projekt jest próbą sprawdzenia, jak zmiana perspektywy — od rekordów do sieci relacji — wpływa na sposób eksplorowania danych bibliograficznych.

## Technologie

Projekt wykorzystuje m.in.:

* Python,
* SQL,
* JSON,
* NetworkX,
* dane z bazy PBL,
* HTML/JavaScript,
* GitHub,
* GitHub Pages.

## Źródło danych i kontekst bibliograficzny

**Polska Bibliografia Literacka** jest prowadzona przez **Pracownię Bibliografii Bieżącej Instytutu Badań Literackich PAN**.

Projekt wykorzystuje dane PBL jako materiał do eksperymentu z modelowaniem, przekształcaniem i wizualizacją danych bibliograficznych.

Źródło danych:

**Polska Bibliografia Literacka**
https://pbl.ibl.poznan.pl/

## Autor

Projekt został przygotowany jako eksperyment dotyczący możliwości wykorzystania danych bibliograficznych PBL do budowy i wizualizacji grafu wiedzy.

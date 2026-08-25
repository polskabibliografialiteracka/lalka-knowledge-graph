"""
Build the Lalka Knowledge Graph from extracted PBL data.

The graph distinguishes between:

- LiteraryWork
- Creator
- Author
- Publisher
- PBLSection
- bibliographic record types

Important modelling rule:

    CHILD_OF

is the only relationship used to represent the PBL record hierarchy.

For example:

    Lalka [LiteraryWork]
        |
        +-- CHILD_OF --> review/article/book/etc.
                            |
                            +-- AUTHOR_OF --> Jan Kowalski

Bolesław Prus is connected through:

    Lalka [LiteraryWork]
        |
        +-- CREATED_BY --> Bolesław Prus

This means that the author of a review is NOT incorrectly treated
as the creator of Lalka, and Bolesław Prus is NOT incorrectly treated
as the author of the review.

Input files:

    data/lalka_records_raw.json
    data/lalka_authors_raw.json
    data/lalka_creators_raw.json
    data/lalka_publishers_raw.json

Output:

    data/lalka_graph.json
"""


from __future__ import annotations

import json
from pathlib import Path
from collections import defaultdict


# =============================================================================
# Configuration
# =============================================================================

LALKA_ID = 109715

INPUT_DIR = Path(__file__).resolve().parents[1] / "data"

OUTPUT_FILE = INPUT_DIR / "lalka_graph.json"


# =============================================================================
# Record type mapping
# =============================================================================

# PBL "ZA_TYPE" values are mapped to semantic graph node types.
#
# The mapping can be extended when additional PBL record types are identified.

RECORD_TYPE_MAP = {
    "KS": "BookRecord",
    "FI": "ScreenAdaptation",
    "SZ": "TheatreRecord",
    "AU": "BroadcastRecord",
    "IR": "EventRecord",
    "PU": "PublicationRecord",
    "IZA": "OtherRecord",
}


# =============================================================================
# Utilities
# =============================================================================

def load_json(path: Path):
    """Load UTF-8 JSON file."""

    with open(
        path,
        "r",
        encoding="utf-8",
    ) as file:

        return json.load(file)


def save_json(data, path: Path):
    """Save UTF-8 JSON."""

    with open(
        path,
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            data,
            file,
            ensure_ascii=False,
            indent=2,
        )


def record_node_id(record_id: int) -> str:
    """Return graph node ID for a PBL record."""

    return f"record:{int(record_id)}"


def author_node_id(author_id: int) -> str:
    """Return graph node ID for a PBL author."""

    return f"author:{int(author_id)}"


def creator_node_id(creator_id: int) -> str:
    """Return graph node ID for a PBL creator."""

    return f"creator:{int(creator_id)}"


def publisher_node_id(publisher_id: int) -> str:
    """Return graph node ID for a PBL publisher."""

    return f"publisher:{int(publisher_id)}"


def section_node_id(section_id: int) -> str:
    """Return graph node ID for a PBL section."""

    return f"section:{int(section_id)}"


def clean_value(value):
    """Convert pandas/JSON-like nulls into None where needed."""

    if value is None:
        return None

    return value


def get_record_type(record: dict) -> str:
    """
    Convert PBL ZA_TYPE into a graph node type.

    Unknown types are preserved as OtherRecord.
    """

    pbl_type = record.get("ZA_TYPE")

    if pbl_type is None:
        return "OtherRecord"

    pbl_type = str(pbl_type).strip().upper()

    return RECORD_TYPE_MAP.get(
        pbl_type,
        "OtherRecord",
    )


def get_record_label(record: dict) -> str:
    """Create a readable label for a PBL record."""

    title = record.get("ZA_TYTUL")

    if title is None:
        title = ""

    title = str(title).strip()

    if not title:
        title = f"Record {record.get('ZA_ZAPIS_ID')}"

    return title


def make_edge(
    source: str,
    target: str,
    relationship: str,
    **properties,
) -> dict:
    """Create a graph edge."""

    edge = {
        "source": source,
        "target": target,
        "relationship": relationship,
    }

    for key, value in properties.items():

        if value is not None:
            edge[key] = value

    return edge


# =============================================================================
# Graph builder
# =============================================================================

class GraphBuilder:
    """Build the Lalka knowledge graph."""

    def __init__(self):

        self.nodes = {}
        self.edges = []

        # Prevent accidental duplicate edges.
        self.edge_keys = set()

    # -------------------------------------------------------------------------
    # Nodes
    # -------------------------------------------------------------------------

    def add_node(
        self,
        node_id: str,
        node_type: str,
        label: str,
        **properties,
    ):
        """Add a node if it does not already exist."""

        if node_id in self.nodes:

            # Update properties if the node already exists.
            self.nodes[node_id]["properties"].update(
                {
                    key: value
                    for key, value in properties.items()
                    if value is not None
                }
            )

            return

        self.nodes[node_id] = {
            "id": node_id,
            "type": node_type,
            "label": label,
            "properties": {
                key: value
                for key, value in properties.items()
                if value is not None
            },
        }

    # -------------------------------------------------------------------------
    # Edges
    # -------------------------------------------------------------------------

    def add_edge(
        self,
        source: str,
        target: str,
        relationship: str,
        **properties,
    ):
        """
        Add an edge.

        Duplicate edges are ignored.
        """

        edge_key = (
            source,
            target,
            relationship,
        )

        if edge_key in self.edge_keys:
            return

        self.edge_keys.add(edge_key)

        self.edges.append(
            make_edge(
                source,
                target,
                relationship,
                **properties,
            )
        )

    # -------------------------------------------------------------------------
    # Record nodes
    # -------------------------------------------------------------------------

    def add_record_node(
        self,
        record: dict,
    ):
        """Add a PBL record node."""

        record_id = record.get("ZA_ZAPIS_ID")

        if record_id is None:
            return

        record_id = int(record_id)

        node_id = record_node_id(
            record_id
        )

        node_type = get_record_type(
            record
        )

        label = get_record_label(
            record
        )

        properties = {
            "pbl_id": record_id,

            "pbl_type":
                record.get("ZA_TYPE"),

            "parent_id":
                record.get("ZAPIS_NADRZEDNY"),

            "section_id":
                record.get("DZ_DZIAL_ID"),

            "section_name":
                record.get("DZ_NAZWA"),

            "source_id":
                record.get("ZR_ZRODLO_ID"),

            "source":
                record.get("ZR_TYTUL"),

            "source_year":
                record.get("ZA_ZRODLO_ROK"),

            "source_number":
                record.get("ZA_ZRODLO_NR"),

            "source_pages":
                record.get("ZA_ZRODLO_STR"),

            "series":
                record.get("ZA_SERIA_WYDAWNICZA"),

            "coauthors_description":
                record.get("ZA_OPIS_WSPOLTWORCOW"),

            "publishers_description":
                record.get("ZA_WYDAWNICTWA"),

            "publication_year":
                record.get("ZA_ROK_WYDANIA"),

            "physical_description":
                record.get("ZA_OPIS_FIZYCZNY_KSIAZKI"),

            "annotation":
                record.get("ZA_ADNOTACJE"),

            "event_description":
                record.get("ZA_OPIS_IMPREZY"),

            "organizer":
                record.get("ZA_ORGANIZATOR"),
        }

        self.add_node(
            node_id=node_id,
            node_type=node_type,
            label=label,
            **properties,
        )

    # -------------------------------------------------------------------------
    # Record hierarchy
    # -------------------------------------------------------------------------

    def add_record_hierarchy(
        self,
        records: list[dict],
    ):
        """
        Build the PBL hierarchy.

        IMPORTANT:

        CHILD_OF is the only relationship created here.

        We deliberately do NOT create ABOUT_WORK.

        If:

            record A.za_za_zapis_id = record B.za_zapis_id

        then:

            A CHILD_OF B
        """

        record_ids = {
            int(record["ZA_ZAPIS_ID"])
            for record in records
            if record.get("ZA_ZAPIS_ID") is not None
        }

        for record in records:

            child_id = record.get(
                "ZA_ZAPIS_ID"
            )

            parent_id = record.get(
                "ZAPIS_NADRZEDNY"
            )

            if child_id is None:
                continue

            if parent_id is None:
                continue

            child_id = int(child_id)
            parent_id = int(parent_id)

            # Only create hierarchy edges when both records
            # are present in the extracted graph.
            if parent_id not in record_ids:
                continue

            self.add_edge(
                source=record_node_id(
                    child_id
                ),
                target=record_node_id(
                    parent_id
                ),
                relationship="CHILD_OF",
            )

    # -------------------------------------------------------------------------
    # Authors
    # -------------------------------------------------------------------------

    def add_author_relationships(
        self,
        authors: list[dict],
    ):
        """
        Add authors of individual records.

        Relationship direction:

            Author
                |
                +-- AUTHOR_OF --> Record
        """

        for author in authors:

            record_id = author.get(
                "ZAPIS_ID"
            )

            author_id = author.get(
                "AUTOR_ID"
            )

            if record_id is None or author_id is None:
                continue

            record_id = int(record_id)
            author_id = int(author_id)

            node_id = author_node_id(
                author_id
            )

            first_name = (
                author.get("IMIE")
                or ""
            )

            last_name = (
                author.get("NAZWISKO")
                or ""
            )

            label = (
                f"{first_name} {last_name}"
            ).strip()

            if not label:
                label = (
                    f"Author {author_id}"
                )

            self.add_node(
                node_id=node_id,
                node_type="Author",
                label=label,
                pbl_id=author_id,
                first_name=first_name,
                last_name=last_name,
            )

            self.add_edge(
                source=node_id,
                target=record_node_id(
                    record_id
                ),
                relationship="AUTHOR_OF",
            )

    # -------------------------------------------------------------------------
    # Creators
    # -------------------------------------------------------------------------

    def add_creator_relationships(
        self,
        creators: list[dict],
    ):
        """
        Add creators of individual records.

        Relationship direction:

            Record
                |
                +-- CREATED_BY --> Creator

        This relationship is record-specific.

        A creator assigned to Lalka is NOT automatically assigned
        to every review, article, book, etc. that is attached to Lalka.
        """

        for creator in creators:

            record_id = creator.get(
                "ZAPIS_ID"
            )

            creator_id = creator.get(
                "TWORCA_ID"
            )

            if record_id is None or creator_id is None:
                continue

            record_id = int(record_id)
            creator_id = int(creator_id)

            node_id = creator_node_id(
                creator_id
            )

            first_name = (
                creator.get("IMIE")
                or ""
            )

            last_name = (
                creator.get("NAZWISKO")
                or ""
            )

            label = (
                f"{first_name} {last_name}"
            ).strip()

            if not label:
                label = (
                    f"Creator {creator_id}"
                )

            self.add_node(
                node_id=node_id,
                node_type="Creator",
                label=label,
                pbl_id=creator_id,
                first_name=first_name,
                last_name=last_name,
            )

            self.add_edge(
                source=record_node_id(
                    record_id
                ),
                target=node_id,
                relationship="CREATED_BY",
            )

    # -------------------------------------------------------------------------
    # Publishers
    # -------------------------------------------------------------------------

    def add_publisher_relationships(
        self,
        publishers: list[dict],
    ):
        """
        Add publishers.

        Relationship direction:

            Record
                |
                +-- PUBLISHED_BY --> Publisher
        """

        for publisher in publishers:

            record_id = publisher.get(
                "ZAPIS_ID"
            )

            publisher_id = publisher.get(
                "WYDAWNICTWO_ID"
            )

            if (
                record_id is None
                or publisher_id is None
            ):
                continue

            record_id = int(record_id)
            publisher_id = int(publisher_id)

            node_id = publisher_node_id(
                publisher_id
            )

            name = (
                publisher.get("NAZWA")
                or ""
            ).strip()

            if not name:
                name = (
                    f"Publisher {publisher_id}"
                )

            self.add_node(
                node_id=node_id,
                node_type="Publisher",
                label=name,
                pbl_id=publisher_id,
                city=publisher.get("MIASTO"),
            )

            self.add_edge(
                source=record_node_id(
                    record_id
                ),
                target=node_id,
                relationship="PUBLISHED_BY",
            )

    # -------------------------------------------------------------------------
    # Source relationships
    # -------------------------------------------------------------------------

    def add_source_relationships(
        self,
        records: list[dict],
    ):
        """
        Add PBL source nodes.

        Relationship:

            Record
                |
                +-- FROM_SOURCE --> Source
        """

        source_records = {}

        for record in records:

            record_id = record.get(
                "ZA_ZAPIS_ID"
            )

            source_id = record.get(
                "ZR_ZRODLO_ID"
            )

            if (
                record_id is None
                or source_id is None
            ):
                continue

            source_id = int(source_id)

            source_records[
                source_id
            ] = record

        for source_id, record in source_records.items():

            source_node = (
                f"source:{source_id}"
            )

            source_title = (
                record.get("ZR_TYTUL")
                or f"Source {source_id}"
            )

            self.add_node(
                node_id=source_node,
                node_type="PBLSource",
                label=str(source_title),
                pbl_id=source_id,
            )

        for record in records:

            record_id = record.get(
                "ZA_ZAPIS_ID"
            )

            source_id = record.get(
                "ZR_ZRODLO_ID"
            )

            if (
                record_id is None
                or source_id is None
            ):
                continue

            self.add_edge(
                source=record_node_id(
                    int(record_id)
                ),
                target=f"source:{int(source_id)}",
                relationship="FROM_SOURCE",
            )

    # -------------------------------------------------------------------------
    # PBL sections
    # -------------------------------------------------------------------------

    def add_section_relationships(
        self,
        records: list[dict],
    ):
        """
        Add PBL section nodes.

        Relationship:

            Record
                |
                +-- IN_SECTION --> PBLSection
        """

        sections = {}

        for record in records:

            section_id = record.get(
                "DZ_DZIAL_ID"
            )

            section_name = record.get(
                "DZ_NAZWA"
            )

            record_id = record.get(
                "ZA_ZAPIS_ID"
            )

            if (
                section_id is None
                or record_id is None
            ):
                continue

            section_id = int(
                section_id
            )

            sections[
                section_id
            ] = section_name

        for section_id, section_name in sections.items():

            if not section_name:
                section_name = (
                    f"Section {section_id}"
                )

            self.add_node(
                node_id=section_node_id(
                    section_id
                ),
                node_type="PBLSection",
                label=str(section_name),
                pbl_id=section_id,
            )

        for record in records:

            record_id = record.get(
                "ZA_ZAPIS_ID"
            )

            section_id = record.get(
                "DZ_DZIAL_ID"
            )

            if (
                record_id is None
                or section_id is None
            ):
                continue

            self.add_edge(
                source=record_node_id(
                    int(record_id)
                ),
                target=section_node_id(
                    int(section_id)
                ),
                relationship="IN_SECTION",
            )

    # -------------------------------------------------------------------------
    # Lalka-specific relationships
    # -------------------------------------------------------------------------

    def add_lalka_relationships(
        self,
        records: list[dict],
    ):
        """
        Add the LiteraryWork node representing Lalka.

        The Lalka record itself is a PBL record, but in the graph
        it is represented semantically as LiteraryWork.

        Its relationship with Bolesław Prus is based on the actual
        creator relation extracted from PBL.
        """

        lalka_node = record_node_id(
            LALKA_ID
        )

        if lalka_node not in self.nodes:
            return

        # Change the semantic type of the root record.
        self.nodes[lalka_node][
            "type"
        ] = "LiteraryWork"

        self.nodes[lalka_node][
            "label"
        ] = "Lalka"

    # -------------------------------------------------------------------------
    # Validation
    # -------------------------------------------------------------------------

    def validate(
        self,
    ):
        """Validate graph consistency."""

        errors = []

        node_ids = set(
            self.nodes.keys()
        )

        for edge in self.edges:

            source = edge[
                "source"
            ]

            target = edge[
                "target"
            ]

            if source not in node_ids:

                errors.append(
                    f"Missing source node: {source}"
                )

            if target not in node_ids:

                errors.append(
                    f"Missing target node: {target}"
                )

        # Check root.
        lalka_node = record_node_id(
            LALKA_ID
        )

        if lalka_node not in node_ids:

            errors.append(
                "Lalka root node is missing."
            )

        # Check that ABOUT_WORK does not exist.
        about_work_edges = [
            edge
            for edge in self.edges
            if edge["relationship"]
            == "ABOUT_WORK"
        ]

        if about_work_edges:

            errors.append(
                "Graph contains ABOUT_WORK edges. "
                "Hierarchy should use CHILD_OF only."
            )

        if errors:

            print()
            print(
                "GRAPH VALIDATION ERRORS:"
            )

            for error in errors:

                print(
                    f"  - {error}"
                )

            raise RuntimeError(
                "Graph validation failed."
            )

    # -------------------------------------------------------------------------
    # Export
    # -------------------------------------------------------------------------

    def to_dict(self):
        """Return serializable graph dictionary."""

        return {
            "metadata": {
                "project":
                    "Lalka Knowledge Graph",

                "source":
                    "Polska Bibliografia Literacka",

                "root":
                    record_node_id(
                        LALKA_ID
                    ),

                "model": {
                    "hierarchy_relationship":
                        "CHILD_OF",

                    "author_relationship":
                        "AUTHOR_OF",

                    "creator_relationship":
                        "CREATED_BY",

                    "publisher_relationship":
                        "PUBLISHED_BY",

                    "source_relationship":
                        "FROM_SOURCE",

                    "section_relationship":
                        "IN_SECTION",
                },

                "counts": {
                    "nodes":
                        len(self.nodes),

                    "edges":
                        len(self.edges),
                },
            },

            "nodes":
                list(
                    self.nodes.values()
                ),

            "edges":
                self.edges,
        }


# =============================================================================
# Main
# =============================================================================

def main():

    print(
        "Building Lalka Knowledge Graph..."
    )

    # -------------------------------------------------------------------------
    # Load extracted data
    # -------------------------------------------------------------------------

    print(
        "Loading extracted data..."
    )

    records = load_json(
        INPUT_DIR
        / "lalka_records_raw.json"
    )

    authors = load_json(
        INPUT_DIR
        / "lalka_authors_raw.json"
    )

    creators = load_json(
        INPUT_DIR
        / "lalka_creators_raw.json"
    )

    publishers = load_json(
        INPUT_DIR
        / "lalka_publishers_raw.json"
    )

    print(
        f"  Records: {len(records)}"
    )

    print(
        f"  Author relations: {len(authors)}"
    )

    print(
        f"  Creator relations: {len(creators)}"
    )

    print(
        f"  Publisher relations: {len(publishers)}"
    )

    # -------------------------------------------------------------------------
    # Filter invalid records
    # -------------------------------------------------------------------------

    valid_records = []
    excluded_records = []

    for record in records:

        section_name = record.get(
            "DZ_NAZWA"
        )

        if section_name == "-- do ustalenia --":

            excluded_records.append(
                record
            )

        else:

            valid_records.append(
                record
            )

    print(
        f"  Valid records: {len(valid_records)}"
    )

    print(
        f"  Excluded records: "
        f"{len(excluded_records)}"
    )

    # -------------------------------------------------------------------------
    # Keep only relations belonging to valid records
    # -------------------------------------------------------------------------

    valid_record_ids = {
        int(record["ZA_ZAPIS_ID"])
        for record in valid_records
        if record.get("ZA_ZAPIS_ID") is not None
    }

    authors = [
        author
        for author in authors
        if author.get("ZAPIS_ID") is not None
        and int(author["ZAPIS_ID"])
        in valid_record_ids
    ]

    creators = [
        creator
        for creator in creators
        if creator.get("ZAPIS_ID") is not None
        and int(creator["ZAPIS_ID"])
        in valid_record_ids
    ]

    publishers = [
        publisher
        for publisher in publishers
        if publisher.get("ZAPIS_ID") is not None
        and int(publisher["ZAPIS_ID"])
        in valid_record_ids
    ]

    # -------------------------------------------------------------------------
    # Build graph
    # -------------------------------------------------------------------------

    graph = GraphBuilder()

    print(
        "Building record nodes..."
    )

    for record in valid_records:

        graph.add_record_node(
            record
        )

    print(
        "Building record hierarchy..."
    )

    graph.add_record_hierarchy(
        valid_records
    )

    print(
        "Building author relationships..."
    )

    graph.add_author_relationships(
        authors
    )

    print(
        "Building creator relationships..."
    )

    graph.add_creator_relationships(
        creators
    )

    print(
        "Building publisher relationships..."
    )

    graph.add_publisher_relationships(
        publishers
    )

    print(
        "Building source relationships..."
    )

    graph.add_source_relationships(
        valid_records
    )

    print(
        "Building PBL section relationships..."
    )

    graph.add_section_relationships(
        valid_records
    )

    print(
        "Building Lalka-specific relationships..."
    )

    graph.add_lalka_relationships(
        valid_records
    )

    # -------------------------------------------------------------------------
    # Validation
    # -------------------------------------------------------------------------

    print(
        "Validating graph..."
    )

    graph.validate()

    # -------------------------------------------------------------------------
    # Save
    # -------------------------------------------------------------------------

    graph_data = graph.to_dict()

    save_json(
        graph_data,
        OUTPUT_FILE,
    )

    print()
    print(
        "Graph built successfully."
    )

    print(
        f"  Nodes: {len(graph.nodes)}"
    )

    print(
        f"  Edges: {len(graph.edges)}"
    )

    print(
        f"  Output: {OUTPUT_FILE}"
    )


if __name__ == "__main__":
    main()
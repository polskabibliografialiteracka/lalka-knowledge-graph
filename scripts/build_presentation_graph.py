"""
Build the presentation layer of the Lalka Knowledge Graph.

This script transforms the full PBL graph into a simplified,
user-oriented graph intended for visualization.

The source graph remains unchanged.

Source:
    data/lalka_graph.json

Output:
    data/lalka_presentation_graph.json

Presentation model
------------------

Node types:

    Work
    Person
    Adaptation
    Publication
    Event
    Publisher
    Source

Presentation relationships:

    CREATED_BY
    ADAPTED_AS
    HAS_RECORD
    RELATED_TO
    AUTHORED_BY
    PUBLISHED_BY
    FROM_SOURCE

Important modelling decision
----------------------------

PBL uses CHILD_OF to represent the internal hierarchy of records.

For the presentation layer, CHILD_OF is not exposed directly.

Instead:

    Lalka
        |
        | ADAPTED_AS
        v
    Adaptation
        |
        | HAS_RECORD
        v
    Publication

All bibliographic record types are represented in the presentation
layer as Publication:

    BookRecord
    PublicationRecord
    OtherRecord

The original PBL type is preserved in the `original_type` field.

This distinction allows the presentation layer to use a simple,
user-oriented model while preserving the technical information
from the source PBL graph.

The original PBL identifiers and metadata are preserved.

Some presentation relationships are manually verified when
they cannot be reconstructed reliably from the PBL hierarchy.
"""


from __future__ import annotations

import json
from pathlib import Path
from collections import defaultdict


# =============================================================================
# CONFIGURATION
# =============================================================================

LALKA_ID = "record:109715"

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = SCRIPT_DIR.parent

INPUT_FILE = PROJECT_DIR / "data" / "lalka_graph.json"
OUTPUT_FILE = PROJECT_DIR / "data" / "lalka_presentation_graph.json"


# =============================================================================
# MANUALLY VERIFIED RELATIONSHIPS
# =============================================================================

"""
These records have been manually verified as screen adaptations
of Lalka.

The relationships are added only to the presentation layer.

The source PBL graph is not modified.
"""

MANUAL_LALKA_ADAPTATIONS = [
    "record:304249",
    "record:136679",
]


# =============================================================================
# PRESENTATION TYPE MAPPING
# =============================================================================

"""
Mapping from technical PBL/source graph types to the simplified
presentation model.

The presentation layer deliberately groups all bibliographic
record types under the single Publication type.

The original technical type remains available in `original_type`.
"""

PRESENTATION_TYPE_MAP = {
    "LiteraryWork": "Work",

    "ScreenAdaptation": "Adaptation",
    "TheatreRecord": "Adaptation",
    "BroadcastRecord": "Adaptation",

    "BookRecord": "Publication",
    "PublicationRecord": "Publication",
    "OtherRecord": "Publication",

    "EventRecord": "Event",
}


# =============================================================================
# UTILITIES
# =============================================================================

def load_json(path: Path):
    """Load UTF-8 JSON."""

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


def node_id(node):
    """Return node ID."""

    return node.get("id")


def node_type(node):
    """Return source graph node type."""

    return node.get(
        "type",
        "Unknown",
    )


def node_label(node):
    """Return human-readable node label."""

    return (
        node.get("label")
        or node.get("name")
        or node.get("title")
        or node_id(node)
    )


def edge_relationship(edge):
    """Return source graph relationship type."""

    return (
        edge.get("relationship")
        or edge.get("type")
        or edge.get("label")
        or "UNKNOWN"
    )


# =============================================================================
# PRESENTATION TYPE
# =============================================================================

def get_presentation_type(original_type):
    """
    Convert a source graph node type into a presentation type.

    All bibliographic record types are represented as Publication.
    """

    if original_type in {
        "Creator",
        "Author",
    }:
        return "Person"

    if original_type == "Publisher":
        return "Publisher"

    if original_type == "PBLSource":
        return "Source"

    return PRESENTATION_TYPE_MAP.get(
        original_type,
        "Publication",
    )


# =============================================================================
# PRESENTATION GRAPH BUILDER
# =============================================================================

class PresentationGraphBuilder:
    """Build a simplified presentation graph."""

    def __init__(
        self,
        source_graph,
    ):

        self.source_graph = source_graph

        self.nodes = {}
        self.edges = []

        # Prevent duplicate presentation relationships.
        self.edge_keys = set()

        # ---------------------------------------------------------------------
        # Source graph indexes
        # ---------------------------------------------------------------------

        self.source_nodes = {
            node_id(node): node
            for node in source_graph.get(
                "nodes",
                [],
            )
        }

        self.source_edges = (
            source_graph.get(
                "edges",
                [],
            )
        )

        self.incoming = defaultdict(list)
        self.outgoing = defaultdict(list)

        self._build_edge_indexes()

    # =========================================================================
    # INDEXES
    # =========================================================================

    def _build_edge_indexes(self):
        """Build incoming and outgoing source graph indexes."""

        for edge in self.source_edges:

            source = edge.get("source")
            target = edge.get("target")

            if not source or not target:
                continue

            self.outgoing[source].append(edge)
            self.incoming[target].append(edge)

    # =========================================================================
    # NODES
    # =========================================================================

    def add_node(
        self,
        node_id_value,
        presentation_type_value,
        label,
        original_node=None,
        **properties,
    ):
        """
        Add a presentation node.

        Original PBL properties are preserved.
        """

        if node_id_value in self.nodes:
            return

        original_type = None

        if original_node:
            original_type = original_node.get("type")

        node_properties = {}

        if original_node:

            original_properties = (
                original_node.get("properties")
                or {}
            )

            node_properties.update(
                original_properties
            )

        node_properties.update(
            {
                key: value
                for key, value in properties.items()
                if value is not None
            }
        )

        self.nodes[node_id_value] = {
            "id": node_id_value,
            "type": presentation_type_value,
            "label": label,
            "properties": node_properties,
            "presentation_type": presentation_type_value,
            "original_type": original_type,
        }

    # =========================================================================
    # EDGES
    # =========================================================================

    def add_edge(
        self,
        source,
        target,
        relationship,
        **properties,
    ):
        """Add a presentation relationship."""

        edge_key = (
            source,
            target,
            relationship,
        )

        if edge_key in self.edge_keys:
            return

        self.edge_keys.add(
            edge_key
        )

        edge = {
            "source": source,
            "target": target,
            "relationship": relationship,
        }

        for key, value in properties.items():

            if value is not None:
                edge[key] = value

        self.edges.append(edge)

    # =========================================================================
    # ROOT WORK
    # =========================================================================

    def add_root(self):
        """Add Lalka as the central Work node."""

        root = self.source_nodes.get(
            LALKA_ID
        )

        if not root:

            raise RuntimeError(
                "Lalka root node was not found "
                "in the source graph."
            )

        self.add_node(
            node_id_value=LALKA_ID,
            presentation_type_value="Work",
            label="Lalka",
            original_node=root,
            role="central_work",
        )

    # =========================================================================
    # WORK CREATORS
    # =========================================================================

    def add_root_creators(self):
        """
        Add creators directly connected to Lalka.

        Only actual CREATED_BY relationships of Lalka
        are used.
        """

        for edge in self.outgoing.get(
            LALKA_ID,
            [],
        ):

            if edge_relationship(edge) != "CREATED_BY":
                continue

            creator_id = edge.get("target")

            creator = self.source_nodes.get(
                creator_id
            )

            if not creator:
                continue

            if node_type(creator) != "Creator":
                continue

            self.add_node(
                node_id_value=creator_id,
                presentation_type_value="Person",
                label=node_label(creator),
                original_node=creator,
                role="work_creator",
            )

            self.add_edge(
                source=LALKA_ID,
                target=creator_id,
                relationship="CREATED_BY",
                relation_source="pbl",
            )

    # =========================================================================
    # DIRECT LALKA RECORDS
    # =========================================================================

    def get_direct_lalka_records(self):
        """
        Return records directly attached to Lalka through CHILD_OF.

        Source relationship:

            child -- CHILD_OF --> Lalka
        """

        records = []

        for edge in self.incoming.get(
            LALKA_ID,
            [],
        ):

            if edge_relationship(edge) != "CHILD_OF":
                continue

            child_id = edge.get("source")

            child = self.source_nodes.get(
                child_id
            )

            if not child:
                continue

            if child_id == LALKA_ID:
                continue

            records.append(child)

        return records

    # =========================================================================
    # RECORD CLASSIFICATION
    # =========================================================================

    def record_role(
        self,
        presentation_type_value,
    ):
        """Return presentation role for a record."""

        if presentation_type_value == "Adaptation":
            return "adaptation"

        if presentation_type_value == "Publication":
            return "publication"

        if presentation_type_value == "Event":
            return "event"

        return "publication"

    # =========================================================================
    # DIRECT RECORD RELATIONSHIP
    # =========================================================================

    def record_relationship(
        self,
        presentation_type_value,
    ):
        """
        Determine the relationship between Lalka
        and a direct child record.

        Direct adaptations receive ADAPTED_AS.

        Other direct records remain RELATED_TO.
        """

        if presentation_type_value == "Adaptation":
            return "ADAPTED_AS"

        return "RELATED_TO"

    # =========================================================================
    # DIRECT RECORDS
    # =========================================================================

    def add_direct_records(self):
        """
        Add records directly connected to Lalka.

        Adaptations are promoted to the presentation layer.

        All bibliographic record types are represented as Publication.
        """

        direct_records = (
            self.get_direct_lalka_records()
        )

        for record in direct_records:

            record_id = node_id(record)

            if not record_id:
                continue

            original_type = node_type(record)

            presentation_type_value = (
                get_presentation_type(
                    original_type
                )
            )

            role = self.record_role(
                presentation_type_value
            )

            self.add_node(
                node_id_value=record_id,
                presentation_type_value=(
                    presentation_type_value
                ),
                label=node_label(record),
                original_node=record,
                role=role,
                root_relation="direct_child_of_lalka",
            )

            self.add_edge(
                source=LALKA_ID,
                target=record_id,
                relationship=(
                    self.record_relationship(
                        presentation_type_value
                    )
                ),
                relation_source="pbl_hierarchy",
                source_relationship="CHILD_OF",
            )

    # =========================================================================
    # MANUAL ADAPTATIONS
    # =========================================================================

    def add_manual_adaptations(self):
        """
        Add manually verified screen adaptations of Lalka.

        These relationships belong to the presentation layer only.

        The source PBL graph is not modified.
        """

        for adaptation_id in (
            MANUAL_LALKA_ADAPTATIONS
        ):

            adaptation = self.source_nodes.get(
                adaptation_id
            )

            if not adaptation:

                print(
                    "WARNING: Manual adaptation "
                    f"not found: {adaptation_id}"
                )

                continue

            self.add_node(
                node_id_value=adaptation_id,
                presentation_type_value="Adaptation",
                label=node_label(adaptation),
                original_node=adaptation,
                role="screen_adaptation",
                root_relation="manually_verified",
            )

            self.add_edge(
                source=LALKA_ID,
                target=adaptation_id,
                relationship="ADAPTED_AS",
                relation_source="manual",
            )

    # =========================================================================
    # ADAPTATION CHILD RECORDS
    # =========================================================================

    def get_adaptation_child_records(
        self,
        adaptation_id,
    ):
        """
        Return records directly attached to an adaptation.

        Source relationship:

            child -- CHILD_OF --> adaptation

        This is intentionally limited to direct children.
        """

        records = []

        for edge in self.incoming.get(
            adaptation_id,
            [],
        ):

            if edge_relationship(edge) != "CHILD_OF":
                continue

            child_id = edge.get("source")

            child = self.source_nodes.get(
                child_id
            )

            if not child:
                continue

            if child_id == adaptation_id:
                continue

            records.append(child)

        return records

    # =========================================================================
    # ADD ADAPTATION CHILD RECORDS
    # =========================================================================

    def add_adaptation_child_records(self):
        """
        Add bibliographic records belonging directly to
        screen adaptations.

        Example:

            record:304249
                |
                | HAS_RECORD
                v
            record:401079

            record:136679
                |
                | HAS_RECORD
                v
            record:136684

        These records are represented as Publication objects
        in the presentation layer, regardless of their original
        PBL record type.
        """

        adaptation_ids = [
            node_id_value
            for node_id_value, node in self.nodes.items()
            if node.get("presentation_type") == "Adaptation"
        ]

        for adaptation_id in adaptation_ids:

            child_records = (
                self.get_adaptation_child_records(
                    adaptation_id
                )
            )

            for child in child_records:

                child_id = node_id(child)

                if not child_id:
                    continue

                original_type = node_type(child)

                presentation_type_value = (
                    get_presentation_type(
                        original_type
                    )
                )

                role = self.record_role(
                    presentation_type_value
                )

                self.add_node(
                    node_id_value=child_id,
                    presentation_type_value=(
                        presentation_type_value
                    ),
                    label=node_label(child),
                    original_node=child,
                    role=role,
                    root_relation="child_of_adaptation",
                    parent_presentation_id=adaptation_id,
                )

                self.add_edge(
                    source=adaptation_id,
                    target=child_id,
                    relationship="HAS_RECORD",
                    relation_source="pbl_hierarchy",
                    source_relationship="CHILD_OF",
                )

    # =========================================================================
    # RELATED METADATA
    # =========================================================================

    def add_related_metadata(self):
        """
        Add selected metadata for records already present
        in the presentation graph.

        This prevents uncontrolled graph expansion.
        """

        presentation_record_ids = [
            node_id_value
            for node_id_value, node in self.nodes.items()
            if node.get(
                "presentation_type"
            ) in {
                "Adaptation",
                "Publication",
                "Event",
            }
        ]

        for record_id in presentation_record_ids:

            self.add_metadata_for_record(
                record_id
            )

    # =========================================================================
    # METADATA
    # =========================================================================

    def add_metadata_for_record(
        self,
        record_id,
    ):
        """
        Add authors, publishers and sources for a record.

        Only metadata already explicitly represented in the
        source graph is used.
        """

        # ---------------------------------------------------------------------
        # AUTHORS
        # ---------------------------------------------------------------------

        for edge in self.incoming.get(
            record_id,
            [],
        ):

            if edge_relationship(edge) != "AUTHOR_OF":
                continue

            author_id = edge.get("source")

            author = self.source_nodes.get(
                author_id
            )

            if not author:
                continue

            if node_type(author) != "Author":
                continue

            self.add_node(
                node_id_value=author_id,
                presentation_type_value="Person",
                label=node_label(author),
                original_node=author,
                role="record_author",
            )

            self.add_edge(
                source=record_id,
                target=author_id,
                relationship="AUTHORED_BY",
                relation_source="pbl",
            )

        # ---------------------------------------------------------------------
        # PUBLISHERS
        # ---------------------------------------------------------------------

        for edge in self.outgoing.get(
            record_id,
            [],
        ):

            if edge_relationship(edge) != "PUBLISHED_BY":
                continue

            publisher_id = edge.get("target")

            publisher = self.source_nodes.get(
                publisher_id
            )

            if not publisher:
                continue

            if node_type(publisher) != "Publisher":
                continue

            self.add_node(
                node_id_value=publisher_id,
                presentation_type_value="Publisher",
                label=node_label(publisher),
                original_node=publisher,
                role="record_publisher",
            )

            self.add_edge(
                source=record_id,
                target=publisher_id,
                relationship="PUBLISHED_BY",
                relation_source="pbl",
            )

        # ---------------------------------------------------------------------
        # SOURCES
        # ---------------------------------------------------------------------

        for edge in self.outgoing.get(
            record_id,
            [],
        ):

            if edge_relationship(edge) != "FROM_SOURCE":
                continue

            source_id = edge.get("target")

            source = self.source_nodes.get(
                source_id
            )

            if not source:
                continue

            if node_type(source) != "PBLSource":
                continue

            self.add_node(
                node_id_value=source_id,
                presentation_type_value="Source",
                label=node_label(source),
                original_node=source,
                role="bibliographic_source",
            )

            self.add_edge(
                source=record_id,
                target=source_id,
                relationship="FROM_SOURCE",
                relation_source="pbl",
            )

    # =========================================================================
    # STATISTICS
    # =========================================================================

    def build_statistics(self):
        """Return presentation graph statistics."""

        node_counts = defaultdict(int)
        edge_counts = defaultdict(int)

        for node in self.nodes.values():

            node_counts[
                node.get("presentation_type")
            ] += 1

        for edge in self.edges:

            edge_counts[
                edge.get("relationship")
            ] += 1

        return {
            "nodes": len(self.nodes),
            "edges": len(self.edges),

            "node_types": dict(
                sorted(
                    node_counts.items()
                )
            ),

            "relationships": dict(
                sorted(
                    edge_counts.items()
                )
            ),
        }

    # =========================================================================
    # EXPORT
    # =========================================================================

    def to_dict(self):
        """Return serializable presentation graph."""

        statistics = self.build_statistics()

        return {
            "metadata": {
                "project":
                    "Lalka Knowledge Graph",

                "layer":
                    "presentation",

                "source":
                    "Polska Bibliografia Literacka",

                "source_graph":
                    "lalka_graph.json",

                "root":
                    LALKA_ID,

                "description":
                    (
                        "A simplified presentation layer of the "
                        "Lalka Knowledge Graph designed for interactive "
                        "visual exploration."
                    ),

                "model": {
                    "node_types": [
                        "Work",
                        "Person",
                        "Adaptation",
                        "Publication",
                        "Event",
                        "Publisher",
                        "Source",
                    ],

                    "relationships": [
                        "CREATED_BY",
                        "ADAPTED_AS",
                        "HAS_RECORD",
                        "RELATED_TO",
                        "AUTHORED_BY",
                        "PUBLISHED_BY",
                        "FROM_SOURCE",
                    ],
                },

                "manual_relationships": {
                    "adaptations": (
                        MANUAL_LALKA_ADAPTATIONS
                    ),
                },

                "statistics":
                    statistics,
            },

            "nodes":
                list(
                    self.nodes.values()
                ),

            "edges":
                self.edges,
        }


# =============================================================================
# MAIN
# =============================================================================

def main():

    print(
        "Building Lalka presentation graph..."
    )

    # -------------------------------------------------------------------------
    # CHECK INPUT
    # -------------------------------------------------------------------------

    if not INPUT_FILE.exists():

        raise FileNotFoundError(
            "Source graph not found:\n"
            f"{INPUT_FILE}"
        )

    # -------------------------------------------------------------------------
    # LOAD SOURCE GRAPH
    # -------------------------------------------------------------------------

    print()
    print(
        "Loading source graph..."
    )

    source_graph = load_json(
        INPUT_FILE
    )

    source_nodes = source_graph.get(
        "nodes",
        []
    )

    source_edges = source_graph.get(
        "edges",
        []
    )

    print(
        f"  Source nodes: {len(source_nodes)}"
    )

    print(
        f"  Source edges: {len(source_edges)}"
    )

    # -------------------------------------------------------------------------
    # CREATE BUILDER
    # -------------------------------------------------------------------------

    graph = PresentationGraphBuilder(
        source_graph
    )

    # -------------------------------------------------------------------------
    # CENTRAL WORK
    # -------------------------------------------------------------------------

    print()
    print(
        "Adding central work..."
    )

    graph.add_root()

    # -------------------------------------------------------------------------
    # WORK CREATOR
    # -------------------------------------------------------------------------

    print(
        "Adding work creators..."
    )

    graph.add_root_creators()

    # -------------------------------------------------------------------------
    # DIRECT RECORDS
    # -------------------------------------------------------------------------

    print(
        "Adding records directly connected to Lalka..."
    )

    direct_records = (
        graph.get_direct_lalka_records()
    )

    print(
        f"  Direct records: "
        f"{len(direct_records)}"
    )

    graph.add_direct_records()

    # -------------------------------------------------------------------------
    # MANUAL ADAPTATIONS
    # -------------------------------------------------------------------------

    print(
        "Adding manually verified adaptations..."
    )

    graph.add_manual_adaptations()

    # -------------------------------------------------------------------------
    # ADAPTATION CHILD RECORDS
    # -------------------------------------------------------------------------

    print(
        "Adding records belonging to adaptations..."
    )

    graph.add_adaptation_child_records()

    # -------------------------------------------------------------------------
    # RELATED METADATA
    # -------------------------------------------------------------------------

    print(
        "Adding related metadata..."
    )

    graph.add_related_metadata()

    # -------------------------------------------------------------------------
    # EXPORT
    # -------------------------------------------------------------------------

    presentation_graph = (
        graph.to_dict()
    )

    save_json(
        presentation_graph,
        OUTPUT_FILE,
    )

    # -------------------------------------------------------------------------
    # SUMMARY
    # -------------------------------------------------------------------------

    statistics = (
        presentation_graph[
            "metadata"
        ]["statistics"]
    )

    print()
    print(
        "=" * 80
    )

    print(
        "PRESENTATION GRAPH BUILT"
    )

    print(
        "=" * 80
    )

    print(
        f"Nodes: {statistics['nodes']}"
    )

    print(
        f"Edges: {statistics['edges']}"
    )

    print()
    print(
        "Node types:"
    )

    for node_type_value, count in (
        statistics[
            "node_types"
        ].items()
    ):

        print(
            f"  {node_type_value}: "
            f"{count}"
        )

    print()
    print(
        "Relationships:"
    )

    for relationship, count in (
        statistics[
            "relationships"
        ].items()
    ):

        print(
            f"  {relationship}: "
            f"{count}"
        )

    print()
    print(
        f"Output: {OUTPUT_FILE}"
    )


# =============================================================================
# ENTRY POINT
# =============================================================================

if __name__ == "__main__":
    main()
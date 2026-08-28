
"""
Inspect the Lalka presentation graph.

Input:
    data/lalka_presentation_graph.json

Usage:

    python inspect_presentation_graph.py

        Inspect the Lalka root and its immediate presentation
        relationships.

    python inspect_presentation_graph.py search Lalka

        Search presentation graph nodes.

    python inspect_presentation_graph.py record:304249

        Inspect a specific node.

    python inspect_presentation_graph.py types

        Show node counts by presentation type.

    python inspect_presentation_graph.py relationships

        Show relationship counts.

    python inspect_presentation_graph.py related

        Show all RelatedRecord nodes connected directly to Lalka.
"""


from __future__ import annotations

import json
import sys
from pathlib import Path
from collections import defaultdict


# =============================================================================
# CONFIGURATION
# =============================================================================

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = SCRIPT_DIR.parent

GRAPH_FILE = (
    PROJECT_DIR
    / "data"
    / "lalka_presentation_graph.json"
)

LALKA_ID = "record:109715"


# =============================================================================
# LOAD GRAPH
# =============================================================================

def load_graph():

    with open(
        GRAPH_FILE,
        "r",
        encoding="utf-8",
    ) as file:

        return json.load(file)


# =============================================================================
# BASIC HELPERS
# =============================================================================

def get_nodes(graph):

    return graph.get(
        "nodes",
        [],
    )


def get_edges(graph):

    return graph.get(
        "edges",
        [],
    )


def node_id(node):

    return node.get("id")


def node_label(node):

    return (
        node.get("label")
        or node.get("name")
        or node.get("title")
        or node_id(node)
    )


def node_type(node):

    return (
        node.get("type")
        or node.get("presentation_type")
        or "Unknown"
    )


def edge_type(edge):

    return (
        edge.get("relationship")
        or edge.get("type")
        or edge.get("label")
        or "UNKNOWN"
    )


# =============================================================================
# INDEXES
# =============================================================================

def build_node_index(nodes):

    return {
        node_id(node): node
        for node in nodes
    }


def build_relationship_indexes(edges):

    incoming = defaultdict(list)
    outgoing = defaultdict(list)

    for edge in edges:

        source = edge.get("source")
        target = edge.get("target")

        if not source or not target:
            continue

        outgoing[source].append(edge)
        incoming[target].append(edge)

    return incoming, outgoing


# =============================================================================
# DISPLAY
# =============================================================================

def print_header(title):

    print()
    print("=" * 80)
    print(title)
    print("=" * 80)


def print_node(node):

    print(
        f"{node_label(node)} "
        f"[{node_type(node)}] "
        f"(id={node_id(node)})"
    )

    original_type = node.get(
        "original_type"
    )

    presentation_type = node.get(
        "presentation_type"
    )

    if original_type:
        print(
            f"  Original type: "
            f"{original_type}"
        )

    if presentation_type:
        print(
            f"  Presentation type: "
            f"{presentation_type}"
        )

    properties = node.get(
        "properties"
    )

    if isinstance(
        properties,
        dict,
    ):

        for key, value in properties.items():

            if value is None:
                continue

            print(
                f"  {key}: {value}"
            )


def print_edge(
    edge,
    direction,
    nodes_by_id,
):

    if direction == "out":

        other_id = edge.get(
            "target"
        )

        arrow = "→"

    else:

        other_id = edge.get(
            "source"
        )

        arrow = "←"

    other = nodes_by_id.get(
        other_id
    )

    relationship = edge_type(
        edge
    )

    relation_source = edge.get(
        "relation_source"
    )

    if other:

        text = (
            f"{arrow} "
            f"{relationship} "
            f"{node_label(other)} "
            f"[{node_type(other)}] "
            f"(id={other_id})"
        )

    else:

        text = (
            f"{arrow} "
            f"{relationship} "
            f"[missing node] "
            f"(id={other_id})"
        )

    if relation_source:

        text += (
            f" "
            f"(source={relation_source})"
        )

    print(
        f"  {text}"
    )


# =============================================================================
# ROOT INSPECTION
# =============================================================================

def inspect_lalka(
    nodes_by_id,
    incoming,
    outgoing,
):

    node = nodes_by_id.get(
        LALKA_ID
    )

    if not node:

        print(
            "ERROR: Lalka node was not found."
        )

        return

    print_header(
        "LALKA — PRESENTATION GRAPH"
    )

    print_node(
        node
    )

    out_edges = outgoing.get(
        LALKA_ID,
        []
    )

    in_edges = incoming.get(
        LALKA_ID,
        []
    )

    # -------------------------------------------------------------------------
    # Group outgoing relationships
    # -------------------------------------------------------------------------

    groups = defaultdict(list)

    for edge in out_edges:

        groups[
            edge_type(edge)
        ].append(edge)

    print_header(
        "OUTGOING RELATIONSHIPS"
    )

    for relationship in sorted(
        groups
    ):

        group = groups[
            relationship
        ]

        print()
        print(
            f"{relationship} "
            f"({len(group)})"
        )

        for edge in group:

            print_edge(
                edge,
                "out",
                nodes_by_id,
            )

    # -------------------------------------------------------------------------
    # Incoming
    # -------------------------------------------------------------------------

    if in_edges:

        print_header(
            "INCOMING RELATIONSHIPS"
        )

        for edge in in_edges:

            print_edge(
                edge,
                "in",
                nodes_by_id,
            )

    # -------------------------------------------------------------------------
    # Summary
    # -------------------------------------------------------------------------

    print_header(
        "SUMMARY"
    )

    print(
        f"Node: {node_label(node)}"
    )

    print(
        f"Type: {node_type(node)}"
    )

    print(
        f"ID: {LALKA_ID}"
    )

    print(
        f"Outgoing relationships: "
        f"{len(out_edges)}"
    )

    print(
        f"Incoming relationships: "
        f"{len(in_edges)}"
    )

    neighbors = set()

    for edge in out_edges:

        neighbors.add(
            edge.get("target")
        )

    for edge in in_edges:

        neighbors.add(
            edge.get("source")
        )

    print(
        f"Direct neighboring nodes: "
        f"{len(neighbors)}"
    )


# =============================================================================
# SINGLE NODE INSPECTION
# =============================================================================

def inspect_node(
    target_id,
    nodes_by_id,
    incoming,
    outgoing,
):

    node = nodes_by_id.get(
        target_id
    )

    print_header(
        "NODE INSPECTION"
    )

    if not node:

        print(
            f"ERROR: Node not found: "
            f"{target_id}"
        )

        return

    print_node(
        node
    )

    out_edges = outgoing.get(
        target_id,
        []
    )

    in_edges = incoming.get(
        target_id,
        []
    )

    if out_edges:

        print_header(
            "OUTGOING RELATIONSHIPS"
        )

        groups = defaultdict(list)

        for edge in out_edges:

            groups[
                edge_type(edge)
            ].append(edge)

        for relationship in sorted(
            groups
        ):

            print()
            print(
                f"{relationship} "
                f"({len(groups[relationship])})"
            )

            for edge in groups[
                relationship
            ]:

                print_edge(
                    edge,
                    "out",
                    nodes_by_id,
                )

    else:

        print_header(
            "OUTGOING RELATIONSHIPS"
        )

        print(
            "  (none)"
        )

    if in_edges:

        print_header(
            "INCOMING RELATIONSHIPS"
        )

        groups = defaultdict(list)

        for edge in in_edges:

            groups[
                edge_type(edge)
            ].append(edge)

        for relationship in sorted(
            groups
        ):

            print()
            print(
                f"{relationship} "
                f"({len(groups[relationship])})"
            )

            for edge in groups[
                relationship
            ]:

                print_edge(
                    edge,
                    "in",
                    nodes_by_id,
                )


# =============================================================================
# SEARCH
# =============================================================================

def search_nodes(
    query,
    nodes,
):

    query_lower = query.lower()

    matches = []

    for node in nodes:

        values = [
            node_id(node),
            node_label(node),
            node_type(node),
            node.get("original_type"),
        ]

        text = " ".join(
            str(value)
            for value in values
            if value is not None
        )

        if query_lower in text.lower():

            matches.append(
                node
            )

    print_header(
        f"SEARCH: {query}"
    )

    print(
        f"Found: {len(matches)}"
    )

    for node in matches:

        print(
            f"  {node_label(node)} "
            f"[{node_type(node)}] "
            f"(id={node_id(node)})"
        )


# =============================================================================
# TYPE STATISTICS
# =============================================================================

def show_types(nodes):

    counts = defaultdict(int)

    for node in nodes:

        counts[
            node_type(node)
        ] += 1

    print_header(
        "NODE TYPES"
    )

    for type_name, count in sorted(
        counts.items()
    ):

        print(
            f"{type_name}: {count}"
        )


# =============================================================================
# RELATIONSHIP STATISTICS
# =============================================================================

def show_relationships(edges):

    counts = defaultdict(int)

    for edge in edges:

        counts[
            edge_type(edge)
        ] += 1

    print_header(
        "RELATIONSHIPS"
    )

    for relationship, count in sorted(
        counts.items()
    ):

        print(
            f"{relationship}: {count}"
        )


# =============================================================================
# RELATED RECORDS
# =============================================================================

def show_related_records(
    nodes,
    edges,
    nodes_by_id,
):

    print_header(
        "RECORDS RELATED TO LALKA"
    )

    related = []

    for edge in edges:

        if (
            edge.get("source")
            != LALKA_ID
        ):
            continue

        if edge_type(edge) not in {
            "RELATED_TO",
            "ADAPTED_AS",
        }:
            continue

        target_id = edge.get(
            "target"
        )

        target = nodes_by_id.get(
            target_id
        )

        if not target:
            continue

        related.append(
            (
                edge_type(edge),
                target,
            )
        )

    if not related:

        print(
            "  (none)"
        )

        return

    # -------------------------------------------------------------------------
    # Group by presentation type
    # -------------------------------------------------------------------------

    groups = defaultdict(list)

    for relationship, node in related:

        groups[
            (
                relationship,
                node_type(node),
            )
        ].append(
            node
        )

    for (
        relationship,
        type_name,
    ), group in sorted(
        groups.items(),
        key=lambda item: (
            item[0][0],
            item[0][1],
        ),
    ):

        print()
        print(
            f"{relationship} → "
            f"{type_name} "
            f"({len(group)})"
        )

        for node in sorted(
            group,
            key=lambda n: node_label(n).lower()
        ):

            properties = (
                node.get("properties")
                or {}
            )

            original_type = node.get(
                "original_type"
            )

            pbl_id = properties.get(
                "pbl_id"
            )

            print(
                f"  - {node_label(node)}"
            )

            print(
                f"      id: {node_id(node)}"
            )

            print(
                f"      PBL type: "
                f"{original_type}"
            )

            if pbl_id:

                print(
                    f"      PBL ID: "
                    f"{pbl_id}"
                )

            section = properties.get(
                "section_name"
            )

            if section:

                print(
                    f"      Section: "
                    f"{section}"
                )

            source = properties.get(
                "source"
            )

            if source:

                print(
                    f"      Source: "
                    f"{source}"
                )

            year = properties.get(
                "source_year"
            )

            if year:

                print(
                    f"      Year: "
                    f"{year}"
                )


# =============================================================================
# MANUAL ADAPTATION CHECK
# =============================================================================

def show_adaptations(
    nodes,
    edges,
    nodes_by_id,
):

    print_header(
        "MANUALLY VERIFIED ADAPTATIONS"
    )

    found = []

    for edge in edges:

        if (
            edge.get("source")
            == LALKA_ID
            and edge_type(edge)
            == "ADAPTED_AS"
        ):

            target_id = edge.get(
                "target"
            )

            target = nodes_by_id.get(
                target_id
            )

            if target:

                found.append(
                    (
                        target,
                        edge,
                    )
                )

    if not found:

        print(
            "  No ADAPTED_AS relationships found."
        )

        return

    for target, edge in found:

        print()

        print(
            f"  {node_label(target)}"
        )

        print(
            f"    ID: {node_id(target)}"
        )

        print(
            f"    Type: {node_type(target)}"
        )

        print(
            f"    Original type: "
            f"{target.get('original_type')}"
        )

        print(
            f"    Relationship source: "
            f"{edge.get('relation_source')}"
        )

        properties = (
            target.get("properties")
            or {}
        )

        for key in [
            "pbl_id",
            "source",
            "source_year",
            "source_number",
            "source_pages",
            "annotation",
        ]:

            value = properties.get(
                key
            )

            if value is not None:

                print(
                    f"    {key}: {value}"
                )


# =============================================================================
# VALIDATION
# =============================================================================

def validate_graph(
    nodes,
    edges,
):

    print_header(
        "GRAPH VALIDATION"
    )

    node_ids = {
        node_id(node)
        for node in nodes
    }

    errors = []

    # -------------------------------------------------------------------------
    # Missing nodes
    # -------------------------------------------------------------------------

    for edge in edges:

        source = edge.get(
            "source"
        )

        target = edge.get(
            "target"
        )

        if source not in node_ids:

            errors.append(
                f"Missing source node: "
                f"{source}"
            )

        if target not in node_ids:

            errors.append(
                f"Missing target node: "
                f"{target}"
            )

    # -------------------------------------------------------------------------
    # Duplicate edges
    # -------------------------------------------------------------------------

    seen = set()

    duplicates = []

    for edge in edges:

        key = (
            edge.get("source"),
            edge_type(edge),
            edge.get("target"),
        )

        if key in seen:

            duplicates.append(
                key
            )

        else:

            seen.add(
                key
            )

    # -------------------------------------------------------------------------
    # Root
    # -------------------------------------------------------------------------

    if LALKA_ID not in node_ids:

        errors.append(
            "Lalka root node is missing."
        )

    # -------------------------------------------------------------------------
    # Results
    # -------------------------------------------------------------------------

    if errors:

        print(
            f"Errors: {len(errors)}"
        )

        for error in errors[:20]:

            print(
                f"  - {error}"
            )

    else:

        print(
            "✓ All edge endpoints exist"
        )

    if duplicates:

        print(
            f"WARNING: "
            f"{len(duplicates)} duplicate edges"
        )

    else:

        print(
            "✓ No duplicate edges"
        )


# =============================================================================
# MAIN
# =============================================================================

def main():

    print(
        "Inspecting Lalka presentation graph..."
    )

    # -------------------------------------------------------------------------
    # Check file
    # -------------------------------------------------------------------------

    if not GRAPH_FILE.exists():

        print()
        print(
            "ERROR: Presentation graph not found:"
        )

        print(
            f"  {GRAPH_FILE}"
        )

        sys.exit(1)

    # -------------------------------------------------------------------------
    # Load
    # -------------------------------------------------------------------------

    graph = load_graph()

    nodes = get_nodes(
        graph
    )

    edges = get_edges(
        graph
    )

    print(
        f"  Nodes: {len(nodes)}"
    )

    print(
        f"  Edges: {len(edges)}"
    )

    nodes_by_id = build_node_index(
        nodes
    )

    incoming, outgoing = (
        build_relationship_indexes(
            edges
        )
    )

    # -------------------------------------------------------------------------
    # No argument
    # -------------------------------------------------------------------------

    if len(sys.argv) == 1:

        inspect_lalka(
            nodes_by_id,
            incoming,
            outgoing,
        )

        return

    # -------------------------------------------------------------------------
    # Command
    # -------------------------------------------------------------------------

    command = sys.argv[1].lower()

    # -------------------------------------------------------------------------
    # Search
    # -------------------------------------------------------------------------

    if command == "search":

        if len(sys.argv) < 3:

            print(
                "Usage:"
            )

            print(
                "  python "
                "inspect_presentation_graph.py "
                "search <query>"
            )

            sys.exit(1)

        query = " ".join(
            sys.argv[2:]
        )

        search_nodes(
            query,
            nodes,
        )

        return

    # -------------------------------------------------------------------------
    # Types
    # -------------------------------------------------------------------------

    if command == "types":

        show_types(
            nodes
        )

        return

    # -------------------------------------------------------------------------
    # Relationships
    # -------------------------------------------------------------------------

    if command == "relationships":

        show_relationships(
            edges
        )

        return

    # -------------------------------------------------------------------------
    # Related
    # -------------------------------------------------------------------------

    if command == "related":

        show_related_records(
            nodes,
            edges,
            nodes_by_id,
        )

        return

    # -------------------------------------------------------------------------
    # Adaptations
    # -------------------------------------------------------------------------

    if command == "adaptations":

        show_adaptations(
            nodes,
            edges,
            nodes_by_id,
        )

        return

    # -------------------------------------------------------------------------
    # Validation
    # -------------------------------------------------------------------------

    if command == "validate":

        validate_graph(
            nodes,
            edges,
        )

        return

    # -------------------------------------------------------------------------
    # Direct node inspection
    # -------------------------------------------------------------------------

    inspect_node(
        sys.argv[1],
        nodes_by_id,
        incoming,
        outgoing,
    )


# =============================================================================
# ENTRY POINT
# =============================================================================

if __name__ == "__main__":

    main()



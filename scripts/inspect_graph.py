import json
import sys
from pathlib import Path
from collections import defaultdict


# =============================================================================
# CONFIG
# =============================================================================

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = SCRIPT_DIR.parent
GRAPH_FILE = PROJECT_DIR / "data" / "lalka_graph.json"

LALKA_ID = "record:109715"


# =============================================================================
# LOAD GRAPH
# =============================================================================

def load_graph():
    with open(GRAPH_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def get_nodes(graph):
    """
    Supports the current graph format:
        {
            "nodes": [...],
            "edges": [...]
        }
    """
    return graph.get("nodes", [])


def get_edges(graph):
    return graph.get("edges", [])


def node_id(node):
    return node.get("id")


def node_label(node):
    return node.get("label") or node.get("name") or node.get("title") or node_id(node)


def node_type(node):
    return node.get("type", "Unknown")


# =============================================================================
# INDEXES
# =============================================================================

def build_node_index(nodes):
    return {node_id(node): node for node in nodes}


def build_relationship_indexes(edges):
    incoming = defaultdict(list)
    outgoing = defaultdict(list)

    for edge in edges:
        source = edge.get("source")
        target = edge.get("target")

        if source and target:
            outgoing[source].append(edge)
            incoming[target].append(edge)

    return incoming, outgoing


# =============================================================================
# DISPLAY HELPERS
# =============================================================================

def edge_type(edge):
    return edge.get("type") or edge.get("label") or edge.get("relationship") or "UNKNOWN"


def other_node_id(edge, direction):
    if direction == "out":
        return edge.get("target")
    return edge.get("source")


def print_node(node):
    print(f"{node_label(node)} [{node_type(node)}] (id={node_id(node)})")

    # Print useful metadata if present
    metadata = node.get("properties") or node.get("metadata")

    if isinstance(metadata, dict):
        for key, value in metadata.items():
            print(f"  {key}: {value}")


def print_relationships(
    title,
    edges,
    direction,
    nodes_by_id,
    group_by_type=True,
    max_items=None
):
    print()
    print(title)
    print("-" * len(title))

    if not edges:
        print("  (none)")
        return

    groups = defaultdict(list)

    for edge in edges:
        groups[edge_type(edge)].append(edge)

    if group_by_type:
        for rel_type in sorted(groups):
            group = groups[rel_type]

            print(f"\n  {rel_type} ({len(group)})")

            items = group if max_items is None else group[:max_items]

            for edge in items:
                other_id = other_node_id(edge, direction)
                other = nodes_by_id.get(other_id)

                if other:
                    print(
                        f"    → {node_label(other)} "
                        f"[{node_type(other)}] (id={other_id})"
                    )
                else:
                    print(f"    → [missing node] (id={other_id})")

            if max_items is not None and len(group) > max_items:
                print(f"    ... and {len(group) - max_items} more")

    else:
        for edge in edges:
            other_id = other_node_id(edge, direction)
            other = nodes_by_id.get(other_id)

            if other:
                print(
                    f"  {edge_type(edge)} → "
                    f"{node_label(other)} [{node_type(other)}] "
                    f"(id={other_id})"
                )
            else:
                print(
                    f"  {edge_type(edge)} → "
                    f"[missing node] (id={other_id})"
                )


# =============================================================================
# LALKA INSPECTION
# =============================================================================

def inspect_lalka(nodes_by_id, incoming, outgoing):
    node = nodes_by_id.get(LALKA_ID)

    if not node:
        print("ERROR: Lalka node was not found.")
        return

    print()
    print("=" * 80)
    print("ROOT NODE")
    print("=" * 80)

    print_node(node)

    out_edges = outgoing.get(LALKA_ID, [])
    in_edges = incoming.get(LALKA_ID, [])

    print_relationships(
        "OUTGOING RELATIONSHIPS",
        out_edges,
        "out",
        nodes_by_id
    )

    print_relationships(
        "INCOMING RELATIONSHIPS",
        in_edges,
        "in",
        nodes_by_id
    )

    print()
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)

    print(f"Node: {node_label(node)}")
    print(f"Type: {node_type(node)}")
    print(f"ID: {LALKA_ID}")
    print(f"Outgoing relationships: {len(out_edges)}")
    print(f"Incoming relationships: {len(in_edges)}")
    print(
        f"Direct neighboring nodes: "
        f"{len(set(
            [e.get('target') for e in out_edges] +
            [e.get('source') for e in in_edges]
        ))}"
    )

    print()
    print("Relationship counts:")

    counts = defaultdict(int)

    for edge in out_edges:
        counts[edge_type(edge)] += 1

    for rel_type, count in sorted(counts.items()):
        print(f"  {rel_type}: {count}")

    semantic_checks(node, out_edges, in_edges, nodes_by_id)


# =============================================================================
# SINGLE NODE INSPECTION
# =============================================================================

def inspect_node(target_id, nodes_by_id, incoming, outgoing):
    node = nodes_by_id.get(target_id)

    print()
    print("=" * 80)
    print("NODE INSPECTION")
    print("=" * 80)

    if not node:
        print(f"ERROR: Node not found: {target_id}")
        return

    print_node(node)

    out_edges = outgoing.get(target_id, [])
    in_edges = incoming.get(target_id, [])

    print_relationships(
        "OUTGOING RELATIONSHIPS",
        out_edges,
        "out",
        nodes_by_id
    )

    print_relationships(
        "INCOMING RELATIONSHIPS",
        in_edges,
        "in",
        nodes_by_id
    )

    print()
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)

    print(f"Node: {node_label(node)}")
    print(f"Type: {node_type(node)}")
    print(f"ID: {target_id}")
    print(f"Outgoing relationships: {len(out_edges)}")
    print(f"Incoming relationships: {len(in_edges)}")

    neighbors = set()

    for edge in out_edges:
        neighbors.add(edge.get("target"))

    for edge in in_edges:
        neighbors.add(edge.get("source"))

    print(f"Direct neighboring nodes: {len(neighbors)}")

    print()
    print("Outgoing relationship counts:")

    counts = defaultdict(int)

    for edge in out_edges:
        counts[edge_type(edge)] += 1

    if counts:
        for rel_type, count in sorted(counts.items()):
            print(f"  {rel_type}: {count}")
    else:
        print("  (none)")

    semantic_checks(node, out_edges, in_edges, nodes_by_id)


# =============================================================================
# SEMANTIC CHECKS
# =============================================================================

def semantic_checks(node, out_edges, in_edges, nodes_by_id):
    """
    Small sanity checks for the model we agreed on.

    These are deliberately conservative. They report possible problems;
    they do not modify the graph.
    """

    print()
    print("=" * 80)
    print("SEMANTIC CHECKS")
    print("=" * 80)

    node_id_value = node_id(node)
    node_type_value = node_type(node)

    # -------------------------------------------------------------------------
    # Check 1: LiteraryWork should not have CHILD_OF pointing to records
    # -------------------------------------------------------------------------

    child_of_out = [
        e for e in out_edges
        if edge_type(e) == "CHILD_OF"
    ]

    if node_type_value == "LiteraryWork" and child_of_out:
        print(
            f"WARNING: LiteraryWork has {len(child_of_out)} "
            f"outgoing CHILD_OF relationship(s)."
        )

        for edge in child_of_out[:10]:
            target = nodes_by_id.get(edge.get("target"))

            if target:
                print(
                    f"  - CHILD_OF → {node_label(target)} "
                    f"[{node_type(target)}]"
                )
    else:
        print("✓ No invalid CHILD_OF relationship from LiteraryWork")

    # -------------------------------------------------------------------------
    # Check 2: BookRecord / OtherRecord ABOUT_WORK → LiteraryWork
    # -------------------------------------------------------------------------

    about_work_out = [
        e for e in out_edges
        if edge_type(e) == "ABOUT_WORK"
    ]

    if node_type_value in {"BookRecord", "OtherRecord"} and about_work_out:

        invalid = []

        for edge in about_work_out:
            target = nodes_by_id.get(edge.get("target"))

            if not target or node_type(target) != "LiteraryWork":
                invalid.append(edge)

        if invalid:
            print(
                f"WARNING: {len(invalid)} ABOUT_WORK relationship(s) "
                f"do not point to LiteraryWork."
            )

            for edge in invalid[:10]:
                target = nodes_by_id.get(edge.get("target"))

                if target:
                    print(
                        f"  - ABOUT_WORK → {node_label(target)} "
                        f"[{node_type(target)}]"
                    )
                else:
                    print(
                        f"  - ABOUT_WORK → missing node "
                        f"{edge.get('target')}"
                    )
        else:
            print(
                "✓ ABOUT_WORK relationship(s) point to LiteraryWork"
            )

    # -------------------------------------------------------------------------
    # Check 3: duplicate edges
    # -------------------------------------------------------------------------

    seen = set()
    duplicates = []

    for edge in out_edges + in_edges:
        key = (
            edge.get("source"),
            edge_type(edge),
            edge.get("target")
        )

        if key in seen:
            duplicates.append(key)
        else:
            seen.add(key)

    if duplicates:
        print(
            f"WARNING: {len(duplicates)} duplicate relationship(s) "
            f"detected around this node."
        )
    else:
        print("✓ No duplicate relationships around this node")

    # -------------------------------------------------------------------------
    # Check 4: missing nodes
    # -------------------------------------------------------------------------

    missing = []

    for edge in out_edges:
        if edge.get("target") not in nodes_by_id:
            missing.append(edge.get("target"))

    for edge in in_edges:
        if edge.get("source") not in nodes_by_id:
            missing.append(edge.get("source"))

    if missing:
        print(
            f"WARNING: {len(missing)} relationship(s) point to "
            f"missing nodes."
        )
    else:
        print("✓ All neighboring nodes exist")


# =============================================================================
# FIND NODES
# =============================================================================

def find_nodes(query, nodes):
    query_lower = query.lower()

    matches = []

    for node in nodes:
        text = " ".join(
            str(value)
            for value in [
                node_id(node),
                node_label(node),
                node_type(node)
            ]
            if value is not None
        )

        if query_lower in text.lower():
            matches.append(node)

    return matches


def search_nodes(query, nodes):
    print()
    print("=" * 80)
    print(f"SEARCH: {query}")
    print("=" * 80)

    matches = find_nodes(query, nodes)

    print(f"Found: {len(matches)}")

    for node in matches:
        print(
            f"  {node_label(node)} "
            f"[{node_type(node)}] "
            f"(id={node_id(node)})"
        )


# =============================================================================
# MAIN
# =============================================================================

def main():
    print("Inspecting Lalka Knowledge Graph...")

    if not GRAPH_FILE.exists():
        print()
        print(f"ERROR: Graph file not found:")
        print(f"  {GRAPH_FILE}")
        sys.exit(1)

    graph = load_graph()

    nodes = get_nodes(graph)
    edges = get_edges(graph)

    print(f"  Nodes: {len(nodes)}")
    print(f"  Edges: {len(edges)}")

    nodes_by_id = build_node_index(nodes)
    incoming, outgoing = build_relationship_indexes(edges)

    # -------------------------------------------------------------------------
    # No argument → inspect Lalka
    # -------------------------------------------------------------------------

    if len(sys.argv) == 1:
        inspect_lalka(
            nodes_by_id,
            incoming,
            outgoing
        )
        return

    # -------------------------------------------------------------------------
    # Argument
    # -------------------------------------------------------------------------

    argument = sys.argv[1]

    # Search mode:
    #
    # python inspect_graph.py search Lalka
    #
    if argument.lower() == "search":

        if len(sys.argv) < 3:
            print("Usage:")
            print("  python inspect_graph.py search <query>")
            sys.exit(1)

        query = " ".join(sys.argv[2:])
        search_nodes(query, nodes)

        return

    # Direct node inspection:
    #
    # python inspect_graph.py record:1359644
    #
    inspect_node(
        argument,
        nodes_by_id,
        incoming,
        outgoing
    )


if __name__ == "__main__":
    main()
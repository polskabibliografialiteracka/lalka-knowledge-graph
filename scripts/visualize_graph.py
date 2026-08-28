"""
Visualize Lalka Presentation Graph
==================================

Creates an interactive HTML visualization of the presentation graph.

Input:
    data/lalka_presentation_graph.json

Optional visual asset:
    assets/pbl-logo.png

Output:
    docs/lalka_graph.html
"""

from pathlib import Path
import json
import html
import base64

from bs4 import BeautifulSoup
from pyvis.network import Network


# =============================================================================
# PATHS
# =============================================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

DATA_FILE = PROJECT_ROOT / "data" / "lalka_presentation_graph.json"
LOGO_FILE = PROJECT_ROOT / "assets" / "pbl-logo.png"

OUTPUT_DIR = PROJECT_ROOT / "docs"
OUTPUT_FILE = OUTPUT_DIR / "lalka_graph.html"


# =============================================================================
# VISUAL SETTINGS
# =============================================================================

BACKGROUND = "#f8f6f2"
TEXT_COLOR = "#50504f"
EDGE_COLOR = "#b9b3aa"

COLORS = {
    "Work": "#50504f",
    "Adaptation": "#e94a58",
    "Person": "#a54f99",
    "Publication": "#19978e",
    "RelatedRecord": "#f3b65a",
    "Source": "#87745e",
    "Publisher": "#d8a461",
}


# =============================================================================
# NODE SIZES
# =============================================================================

NODE_SIZES = {
    "Work": 38,
    "Adaptation": 25,
    "Person": 19,
    "Publication": 18,
    "RelatedRecord": 10,
    "Source": 14,
    "Publisher": 13,
}


# =============================================================================
# RELATIONSHIP LABELS
# =============================================================================

RELATIONSHIP_LABELS = {
    "ADAPTED_AS": "adaptacja",
    "AUTHORED_BY": "autor",
    "CREATED_BY": "twórca",
    "FROM_SOURCE": "źródło",
    "PUBLISHED_BY": "wydawca",
    "RELATED_TO": "powiązane",
}


# =============================================================================
# HUMAN-READABLE LABELS
# =============================================================================

TYPE_LABELS = {
    "Work": "Utwór",
    "Adaptation": "Adaptacja",
    "Person": "Osoba",
    "Publication": "Publikacja",
    "RelatedRecord": "Rekord powiązany",
    "Source": "Źródło",
    "Publisher": "Wydawca",
}


# =============================================================================
# HELPERS
# =============================================================================

def load_graph():
    """Load presentation graph JSON."""

    if not DATA_FILE.exists():
        raise FileNotFoundError(
            f"Graph file not found:\n{DATA_FILE}"
        )

    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def get_node_type(node):
    """Return normalized node type."""

    return (
        node.get("type")
        or node.get("node_type")
        or node.get("category")
        or "Other"
    )


def clean_html(text):
    """
    Convert HTML-formatted PBL text into readable plain text.
    """

    if not text:
        return ""

    soup = BeautifulSoup(str(text), "html.parser")

    for br in soup.find_all("br"):
        br.replace_with("\n")

    for tag in soup.find_all(["div", "p", "li"]):
        tag.insert_before("\n")
        tag.insert_after("\n")

    text = soup.get_text("\n", strip=True)

    lines = []

    for line in text.splitlines():

        line = " ".join(line.split())

        if line:
            lines.append(line)

    return "\n".join(lines)


def get_node_title(node):
    """
    Return human-readable node title.
    """

    node_id = str(node.get("id", ""))
    node_type = get_node_type(node)

    # -------------------------------------------------------------------------
    # Central work
    # -------------------------------------------------------------------------

    if node_id == "record:109715":
        return "Lalka"

    # -------------------------------------------------------------------------
    # Adaptations
    # -------------------------------------------------------------------------

    if node_id == "record:304249":
        return "Lalka (prem. 1968)"

    if node_id == "record:136679":
        return "Lalka (TV) – Lalka (prem. 1977)"

    # -------------------------------------------------------------------------
    # People
    # -------------------------------------------------------------------------

    for key in (
        "name",
        "person_name",
        "full_name",
        "display_name",
        "label",
        "title",
    ):

        value = node.get(key)

        if value:

            value = str(value)

            if not value.isdigit() and not value.startswith("record:"):
                return value

    # -------------------------------------------------------------------------
    # Records
    # -------------------------------------------------------------------------

    for key in (
        "title",
        "name",
        "display_name",
        "label",
    ):

        value = node.get(key)

        if value:
            return clean_html(value)

    # -------------------------------------------------------------------------
    # Fallback labels
    # -------------------------------------------------------------------------

    fallback = {
        "RelatedRecord": "Rekord",
        "Publication": "Publikacja",
        "Source": "Źródło",
        "Publisher": "Wydawca",
        "Person": "Osoba",
        "Work": "Utwór",
        "Adaptation": "Adaptacja",
    }

    return fallback.get(node_type, "Obiekt")


def get_person_name(node):
    """
    Return human-readable person name.
    """

    for key in (
        "name",
        "person_name",
        "full_name",
        "display_name",
        "label",
        "title",
    ):

        value = node.get(key)

        if value:

            value = str(value)

            if (
                not value.isdigit()
                and not value.startswith("record:")
            ):
                return clean_html(value)

    # Known PBL creator
    node_id = str(node.get("id", ""))

    if node_id == "record:3426":
        return "Bolesław Prus"

    return None


def get_metadata(node):
    """
    Return metadata for details panel.
    """

    metadata = []

    # -------------------------------------------------------------------------
    # PBL ID
    # -------------------------------------------------------------------------

    pbl_id = node.get("pbl_id")

    if pbl_id is None:

        node_id = str(node.get("id", ""))

        if node_id.startswith("record:"):
            pbl_id = node_id.replace("record:", "")

    # -------------------------------------------------------------------------
    # PBL type
    # -------------------------------------------------------------------------

    pbl_type = (
        node.get("pbl_type")
        or node.get("record_type")
    )

    # -------------------------------------------------------------------------
    # Author / creator
    # -------------------------------------------------------------------------

    author = (
        node.get("author_name")
        or node.get("creator_name")
        or node.get("author")
        or node.get("creator")
    )

    if author:

        author = str(author)

        if author.isdigit():

            if author == "3426":
                author = "Bolesław Prus"
            else:
                author = None

        elif author.startswith("record:"):

            if author == "record:3426":
                author = "Bolesław Prus"
            else:
                author = None

    # -------------------------------------------------------------------------
    # Other metadata
    # -------------------------------------------------------------------------

    section = node.get("section")

    source = (
        node.get("source")
        or node.get("source_title")
        or node.get("publication")
    )

    year = node.get("year")

    if pbl_id:
        metadata.append(("PBL ID", str(pbl_id)))

    if pbl_type:
        metadata.append(("Typ PBL", clean_html(pbl_type)))

    if author:
        metadata.append(("Autor", clean_html(author)))

    if section:
        metadata.append(("Dział", clean_html(section)))

    if source:
        metadata.append(("Źródło", clean_html(source)))

    if year is not None:

        try:

            year_float = float(year)

            if year_float.is_integer():
                year = str(int(year_float))

        except (ValueError, TypeError):
            pass

        metadata.append(("Rok", str(year)))

    return metadata


def get_description(node):
    """
    Return cleaned description / annotation.
    """

    description = (
        node.get("description")
        or node.get("note")
        or node.get("content")
        or node.get("abstract")
        or ""
    )

    return clean_html(description)


def prepare_node(node):
    """
    Prepare node data for JavaScript.
    """

    return {
        "id": str(node.get("id")),
        "title": get_node_title(node),
        "type": get_node_type(node),
        "type_label": TYPE_LABELS.get(
            get_node_type(node),
            "Obiekt"
        ),
        "metadata": get_metadata(node),
        "description": get_description(node),
    }


# =============================================================================
# MAIN
# =============================================================================

def main():

    print("Building Lalka graph visualization...")

    # =========================================================================
    # LOAD GRAPH
    # =========================================================================

    print("\nLoading presentation graph...")

    graph_data = load_graph()

    nodes = graph_data.get("nodes", [])
    edges = graph_data.get("edges", [])

    print(f"  Nodes: {len(nodes)}")
    print(f"  Edges: {len(edges)}")

    # =========================================================================
    # CREATE NETWORK
    # =========================================================================

    net = Network(
        height="100vh",
        width="100%",
        directed=True,
        bgcolor=BACKGROUND,
        font_color=TEXT_COLOR,
        select_menu=False,
        filter_menu=False,
        cdn_resources="in_line",
    )

    # =========================================================================
    # PHYSICS
    # =========================================================================

    net.set_options(
        """
        {
          "interaction": {
            "hover": true,
            "navigationButtons": true,
            "keyboard": {
              "enabled": true
            },
            "multiselect": false
          },

          "physics": {
            "enabled": true,

            "barnesHut": {
              "gravitationalConstant": -6500,
              "centralGravity": 0.25,
              "springLength": 180,
              "springConstant": 0.035,
              "damping": 0.85,
              "avoidOverlap": 1
            },

            "stabilization": {
              "enabled": true,
              "iterations": 1000,
              "updateInterval": 50
            }
          },

          "nodes": {
            "shape": "dot",

            "font": {
              "face": "Arial",
              "color": "#50504f",
              "size": 16
            },

            "borderWidth": 2,
            "borderWidthSelected": 3,

            "shadow": {
              "enabled": true,
              "color": "rgba(80,80,79,0.15)",
              "size": 8,
              "x": 2,
              "y": 3
            }
          },

          "edges": {
            "color": {
              "color": "#b9b3aa",
              "highlight": "#50504f",
              "hover": "#87745e"
            },

            "width": 1.2,
            "selectionWidth": 2.5,

            "smooth": {
              "enabled": true,
              "type": "dynamic"
            },

            "arrows": {
              "to": {
                "enabled": true,
                "scaleFactor": 0.45
              }
            },

            "font": {
              "face": "Arial",
              "size": 11,
              "color": "#87745e",
              "strokeWidth": 3,
              "strokeColor": "#f8f6f2"
            }
          }
        }
        """
    )

    # =========================================================================
    # ADD NODES
    # =========================================================================

    node_lookup = {}
    details_data = {}

    for node in nodes:

        node_id = str(node.get("id"))

        node_type = get_node_type(node)
        title = get_node_title(node)

        color = COLORS.get(
            node_type,
            TEXT_COLOR
        )

        size = NODE_SIZES.get(
            node_type,
            15
        )

        # Prepare details separately
        details_data[node_id] = prepare_node(node)

        # ---------------------------------------------------------------------
        # CENTRAL LALKA
        # ---------------------------------------------------------------------

        if node_id == "record:109715":

            net.add_node(
                node_id,

                label="Lalka",

                title="",

                color={
                    "background": COLORS["Work"],
                    "border": "#ffffff",
                    "highlight": {
                        "background": COLORS["Work"],
                        "border": "#ffffff"
                    }
                },

                size=48,

                borderWidth=4,

                font={
                    "color": "#ffffff",
                    "size": 24,
                    "face": "Arial",
                    "bold": True
                },

                shape="dot",
            )

        # ---------------------------------------------------------------------
        # RELATED RECORD
        # ---------------------------------------------------------------------

        elif node_type == "RelatedRecord":

            net.add_node(
                node_id,

                label="",

                title="",

                color={
                    "background": color,
                    "border": "#ffffff",
                    "highlight": {
                        "background": color,
                        "border": "#50504f"
                    }
                },

                size=size,

                borderWidth=1.5,

                shape="dot",
            )

        # ---------------------------------------------------------------------
        # OTHER NODES
        # ---------------------------------------------------------------------

        else:

            net.add_node(
                node_id,

                label=title,

                title="",

                color={
                    "background": color,
                    "border": "#ffffff",
                    "highlight": {
                        "background": color,
                        "border": "#50504f"
                    }
                },

                size=size,

                borderWidth=2,

                shape="dot",
            )

        node_lookup[node_id] = node

    # =========================================================================
    # ADD EDGES
    # =========================================================================

    for index, edge in enumerate(edges):

        source = str(
            edge.get("source")
            or edge.get("from")
        )

        target = str(
            edge.get("target")
            or edge.get("to")
        )

        relationship = (
            edge.get("relationship")
            or edge.get("type")
            or edge.get("label")
            or ""
        )

        relationship_label = RELATIONSHIP_LABELS.get(
            relationship,
            relationship
        )

        if (
            source not in node_lookup
            or target not in node_lookup
        ):
            continue

        net.add_edge(
            source,
            target,

            id=f"edge_{index}",

            label=relationship_label,

            title="",

            relationship=relationship,
        )

    # =========================================================================
    # OUTPUT DIRECTORY
    # =========================================================================

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    print("\nWriting HTML...")

    generated_html = net.generate_html()

    # =========================================================================
    # LOGO
    # =========================================================================

    logo_html = ""

    if LOGO_FILE.exists():

        try:

            with open(LOGO_FILE, "rb") as f:
                logo_data = base64.b64encode(
                    f.read()
                ).decode("ascii")

            logo_html = f"""
            <img
                id="pbl-logo"
                src="data:image/png;base64,{logo_data}"
                alt="Polska Bibliografia Literacka"
            >
            """

        except Exception as exc:

            print(
                f"\nWARNING: Could not load PBL logo: {exc}"
            )

    else:

        print(
            "\nWARNING: PBL logo not found:"
        )

        print(LOGO_FILE)

    # =========================================================================
    # LEGEND
    # =========================================================================

    legend_items = []

    for node_type, color in COLORS.items():

        label = TYPE_LABELS.get(
            node_type,
            node_type
        )

        legend_items.append(
            f"""
            <div class="legend-item">
                <span
                    class="legend-dot"
                    style="background:{color};"
                ></span>

                <span>{html.escape(label)}</span>
            </div>
            """
        )

    legend_html = "".join(
        legend_items
    )

    # =========================================================================
    # DETAILS DATA
    # =========================================================================

    details_json = json.dumps(
        details_data,
        ensure_ascii=False
    )

    # =========================================================================
    # CUSTOM CSS
    # =========================================================================

    custom_css = """
<style>

* {
    box-sizing: border-box;
}

body {
    margin: 0;
    padding: 0;
    background: #f8f6f2;
    font-family: Arial, Helvetica, sans-serif;
    overflow: hidden;
}

#mynetwork {
    position: absolute !important;
    inset: 0;
    background: #f8f6f2 !important;
}


/* =========================================================================
   HEADER
   ========================================================================= */

#graph-header {
    position: fixed;
    top: 26px;
    left: 32px;
    z-index: 1000;
    pointer-events: none;
}

#graph-title {
    margin: 0;
    color: #50504f;
    font-size: 27px;
    font-weight: 600;
    letter-spacing: -0.3px;
}

#graph-subtitle {
    margin-top: 5px;
    color: #87745e;
    font-size: 13px;
    letter-spacing: 0.2px;
}


/* =========================================================================
   LOGO
   ========================================================================= */

#pbl-logo {
    position: fixed;
    top: 25px;
    right: 30px;

    z-index: 1000;

    max-width: 155px;
    max-height: 65px;

    object-fit: contain;
}


/* =========================================================================
   LEGEND
   ========================================================================= */

#legend {
    position: fixed;

    left: 28px;
    bottom: 28px;

    z-index: 1000;

    padding: 15px 18px;

    background: rgba(248, 246, 242, 0.94);

    border: 1px solid rgba(135, 116, 94, 0.20);

    border-radius: 10px;

    box-shadow:
        0 5px 20px rgba(80,80,79,0.08);

    color: #50504f;

    font-size: 12px;
}

.legend-title {
    margin-bottom: 9px;

    font-size: 11px;
    font-weight: 700;

    text-transform: uppercase;
    letter-spacing: 0.7px;

    color: #87745e;
}

.legend-item {
    display: flex;

    align-items: center;

    margin: 6px 0;

    white-space: nowrap;
}

.legend-dot {
    width: 10px;
    height: 10px;

    margin-right: 8px;

    border-radius: 50%;
}


/* =========================================================================
   DETAILS PANEL
   ========================================================================= */

#details-panel {
    position: fixed;

    top: 100px;
    right: 28px;

    width: 380px;
    max-height: calc(100vh - 150px);

    z-index: 2000;

    display: none;

    padding: 22px;

    overflow-y: auto;

    background: rgba(255,255,255,0.98);

    border: 1px solid rgba(80,80,79,0.14);

    border-radius: 12px;

    box-shadow:
        0 12px 35px rgba(80,80,79,0.16);
}

#details-close {
    position: absolute;

    top: 11px;
    right: 14px;

    border: none;

    background: transparent;

    color: #87745e;

    font-size: 22px;

    cursor: pointer;

    line-height: 1;
}

#details-close:hover {
    color: #50504f;
}


/* =========================================================================
   NODE DETAILS
   ========================================================================= */

.node-type {
    margin-bottom: 8px;

    color: #87745e;

    font-size: 10px;
    font-weight: 700;

    text-transform: uppercase;
    letter-spacing: 1px;
}

.node-title {
    margin-bottom: 18px;

    padding-right: 20px;

    color: #50504f;

    font-size: 19px;
    font-weight: 600;

    line-height: 1.3;
}

.node-metadata {
    border-top: 1px solid #ebe7e0;
}

.detail-row {
    display: grid;

    grid-template-columns: 80px 1fr;

    gap: 12px;

    padding: 9px 0;

    border-bottom: 1px solid #ebe7e0;

    font-size: 12px;

    line-height: 1.4;
}

.detail-label {
    color: #87745e;
    font-weight: 600;
}

.detail-value {
    color: #50504f;
    word-break: break-word;
}

.node-description {
    margin-top: 18px;
    padding-top: 15px;

    border-top: 1px solid #ebe7e0;

    color: #50504f;

    font-size: 13px;

    line-height: 1.55;

    white-space: pre-line;
}

.description-label {
    margin-bottom: 8px;

    color: #87745e;

    font-size: 10px;
    font-weight: 700;

    text-transform: uppercase;

    letter-spacing: 0.8px;
}


/* =========================================================================
   HINT
   ========================================================================= */

#interaction-hint {
    position: fixed;

    right: 28px;
    bottom: 28px;

    z-index: 1000;

    padding: 9px 13px;

    background: rgba(255,255,255,0.80);

    border-radius: 7px;

    color: #87745e;

    font-size: 11px;
}


/* =========================================================================
   SCROLLBAR
   ========================================================================= */

#details-panel::-webkit-scrollbar {
    width: 7px;
}

#details-panel::-webkit-scrollbar-track {
    background: transparent;
}

#details-panel::-webkit-scrollbar-thumb {
    background: #d8d1c7;
    border-radius: 5px;
}

</style>
"""

    # =========================================================================
    # CUSTOM HTML
    # =========================================================================

    custom_markup = """
<div id="graph-header">

    <h1 id="graph-title">
        Lalka
    </h1>

    <div id="graph-subtitle">
        Knowledge Graph · Polska Bibliografia Literacka
    </div>

</div>


__LOGO__


<div id="legend">

    <div class="legend-title">
        Typy obiektów
    </div>

    __LEGEND__

</div>


<div id="details-panel">

    <button
        id="details-close"
        aria-label="Zamknij"
    >
        ×
    </button>

    <div id="details-content"></div>

</div>


<div id="interaction-hint">
    Kliknij obiekt, aby zobaczyć szczegóły
</div>
"""

    custom_markup = custom_markup.replace(
        "__LOGO__",
        logo_html
    )

    custom_markup = custom_markup.replace(
        "__LEGEND__",
        legend_html
    )

    # =========================================================================
    # JAVASCRIPT
    #
    # IMPORTANT:
    # This is a normal string, NOT an f-string.
    # Therefore JavaScript braces do not need to be doubled.
    # =========================================================================

    custom_js = r"""
<script>

document.addEventListener(
    "DOMContentLoaded",
    function() {

        console.log(
            "Lalka Knowledge Graph interface loaded."
        );

        /* ================================================================
           DETAILS DATA
           ================================================================ */

        const detailsData =
            __DETAILS_DATA__;


        /* ================================================================
           DOM ELEMENTS
           ================================================================ */

        const detailsPanel =
            document.getElementById(
                "details-panel"
            );

        const detailsContent =
            document.getElementById(
                "details-content"
            );

        const detailsClose =
            document.getElementById(
                "details-close"
            );


        /* ================================================================
           ESCAPE HTML
           ================================================================ */

        function escapeHtml(value) {

            if (
                value === null ||
                value === undefined
            ) {
                return "";
            }

            return String(value)
                .replace(/&/g, "&amp;")
                .replace(/</g, "&lt;")
                .replace(/>/g, "&gt;")
                .replace(/"/g, "&quot;")
                .replace(/'/g, "&#039;");
        }


        /* ================================================================
           GET TYPE LABEL
           ================================================================ */

        function getTypeLabel(type) {

            const labels = {
                "Work": "Utwór",
                "Adaptation": "Adaptacja",
                "Person": "Osoba",
                "Publication": "Publikacja",
                "RelatedRecord": "Rekord powiązany",
                "Source": "Źródło",
                "Publisher": "Wydawca"
            };

            return labels[type] || type || "Obiekt";
        }


        /* ================================================================
           BUILD DETAILS HTML
           ================================================================ */

        function buildDetailsHtml(data) {

            if (!data) {
                return "";
            }

            let result = "";


            /* ------------------------------------------------------------
               TYPE
               ------------------------------------------------------------ */

            result +=
                '<div class="node-type">' +
                escapeHtml(
                    data.type_label ||
                    getTypeLabel(data.type)
                ) +
                '</div>';


            /* ------------------------------------------------------------
               TITLE
               ------------------------------------------------------------ */

            result +=
                '<div class="node-title">' +
                escapeHtml(
                    data.title || "Obiekt"
                ) +
                '</div>';


            /* ------------------------------------------------------------
               METADATA
               ------------------------------------------------------------ */

            if (
                data.metadata &&
                data.metadata.length
            ) {

                result +=
                    '<div class="node-metadata">';

                data.metadata.forEach(
                    function(row) {

                        if (
                            !row ||
                            row.length < 2
                        ) {
                            return;
                        }

                        result +=
                            '<div class="detail-row">' +

                            '<div class="detail-label">' +
                            escapeHtml(row[0]) +
                            '</div>' +

                            '<div class="detail-value">' +
                            escapeHtml(row[1]) +
                            '</div>' +

                            '</div>';
                    }
                );

                result +=
                    '</div>';
            }


            /* ------------------------------------------------------------
               DESCRIPTION
               ------------------------------------------------------------ */

            if (
                data.description &&
                data.description.trim()
            ) {

                result +=
                    '<div class="node-description">' +

                    '<div class="description-label">' +
                    'Opis' +
                    '</div>' +

                    escapeHtml(
                        data.description
                    ) +

                    '</div>';
            }


            return result;
        }


        /* ================================================================
           RESET GRAPH
           ================================================================ */

        function resetGraph() {

            if (
                typeof nodes === "undefined" ||
                typeof edges === "undefined"
            ) {
                return;
            }

            const currentNodes =
                nodes.get();

            const currentEdges =
                edges.get();


            const nodeUpdates = [];

            currentNodes.forEach(
                function(node) {

                    const originalColor =
                        node.color &&
                        node.color.background
                            ? node.color.background
                            : "#50504f";

                    const originalBorder =
                        node.color &&
                        node.color.border
                            ? node.color.border
                            : "#ffffff";

                    nodeUpdates.push({
                        id: node.id,

                        opacity: 1,

                        color: {
                            background:
                                originalColor,

                            border:
                                originalBorder
                        },

                        font: {
                            color:
                                node.id === "record:109715"
                                    ? "#ffffff"
                                    : "#50504f"
                        }
                    });
                }
            );


            const edgeUpdates = [];

            currentEdges.forEach(
                function(edge) {

                    edgeUpdates.push({
                        id: edge.id,

                        color: {
                            color: "#b9b3aa",
                            opacity: 1
                        },

                        width: 1.2
                    });
                }
            );


            nodes.update(
                nodeUpdates
            );

            edges.update(
                edgeUpdates
            );
        }


        /* ================================================================
           HIGHLIGHT NEIGHBORHOOD
           ================================================================ */

        function highlightNode(selectedId) {

            const currentNodes =
                nodes.get();

            const currentEdges =
                edges.get();


            const connectedNodeIds =
                new Set();

            connectedNodeIds.add(
                selectedId
            );


            const connectedEdgeIds =
                new Set();


            currentEdges.forEach(
                function(edge) {

                    if (
                        String(edge.from) ===
                            String(selectedId)
                        ||
                        String(edge.to) ===
                            String(selectedId)
                    ) {

                        connectedEdgeIds.add(
                            edge.id
                        );

                        connectedNodeIds.add(
                            edge.from
                        );

                        connectedNodeIds.add(
                            edge.to
                        );
                    }
                }
            );


            /* ------------------------------------------------------------
               NODES
               ------------------------------------------------------------ */

            const nodeUpdates = [];

            currentNodes.forEach(
                function(node) {

                    const isConnected =
                        connectedNodeIds.has(
                            node.id
                        );

                    nodeUpdates.push({
                        id: node.id,

                        opacity:
                            isConnected
                                ? 1
                                : 0.15,

                        font: {
                            color:
                                isConnected
                                    ? (
                                        node.id ===
                                        "record:109715"
                                            ? "#ffffff"
                                            : "#50504f"
                                      )
                                    : "rgba(80,80,79,0.15)"
                        }
                    });
                }
            );


            /* ------------------------------------------------------------
               EDGES
               ------------------------------------------------------------ */

            const edgeUpdates = [];

            currentEdges.forEach(
                function(edge) {

                    const isConnected =
                        connectedEdgeIds.has(
                            edge.id
                        );

                    edgeUpdates.push({
                        id: edge.id,

                        color: {
                            color:
                                isConnected
                                    ? "#50504f"
                                    : "#dcd8d1",

                            opacity:
                                isConnected
                                    ? 1
                                    : 0.10
                        },

                        width:
                            isConnected
                                ? 2.4
                                : 1
                    });
                }
            );


            nodes.update(
                nodeUpdates
            );

            edges.update(
                edgeUpdates
            );


            /* ------------------------------------------------------------
               DETAILS
               ------------------------------------------------------------ */

            const selectedData =
                detailsData[
                    String(selectedId)
                ];


            if (selectedData) {

                detailsContent.innerHTML =
                    buildDetailsHtml(
                        selectedData
                    );

                detailsPanel.style.display =
                    "block";

            } else {

                console.warn(
                    "No details found for node:",
                    selectedId
                );
            }
        }


        /* ================================================================
           CLOSE PANEL
           ================================================================ */

        detailsClose.addEventListener(
            "click",
            function() {

                detailsPanel.style.display =
                    "none";

                resetGraph();
            }
        );


        /* ================================================================
           NETWORK CLICK
           ================================================================ */

        network.on(
            "click",
            function(params) {

                if (
                    params.nodes &&
                    params.nodes.length > 0
                ) {

                    const selectedId =
                        params.nodes[0];

                    console.log(
                        "Selected node:",
                        selectedId
                    );

                    highlightNode(
                        selectedId
                    );

                } else {

                    detailsPanel.style.display =
                        "none";

                    resetGraph();
                }
            }
        );


        /* ================================================================
           DOUBLE CLICK
           ================================================================ */

        network.on(
            "doubleClick",
            function(params) {

                if (
                    params.nodes &&
                    params.nodes.length > 0
                ) {

                    network.focus(
                        params.nodes[0],
                        {
                            scale: 1.4,

                            animation: {
                                duration: 600,
                                easingFunction:
                                    "easeInOutQuad"
                            }
                        }
                    );
                }
            }
        );

    }
);

</script>
"""

    # =========================================================================
    # INSERT DATA INTO JAVASCRIPT
    # =========================================================================

    custom_js = custom_js.replace(
        "__DETAILS_DATA__",
        details_json
    )

    # =========================================================================
    # INSERT CUSTOM INTERFACE
    # =========================================================================

    custom_interface = (
        custom_css
        + custom_markup
        + custom_js
    )

    html_content = generated_html.replace(
        "</body>",
        custom_interface + "\n</body>"
    )

    # =========================================================================
    # WRITE FINAL HTML
    # =========================================================================

    with open(
        OUTPUT_FILE,
        "w",
        encoding="utf-8"
    ) as f:

        f.write(
            html_content
        )

    # =========================================================================
    # SUMMARY
    # =========================================================================

    print("\n" + "=" * 80)
    print("VISUALIZATION BUILT")
    print("=" * 80)

    print(
        f"Nodes: {len(nodes)}"
    )

    print(
        f"Edges: {len(edges)}"
    )

    print("\nLogo:")

    if LOGO_FILE.exists():

        print(
            f"  OK: {LOGO_FILE}"
        )

    else:

        print(
            "  NOT FOUND"
        )

    print("\nOutput:")

    print(
        f"  {OUTPUT_FILE}"
    )

    print(
        "\nOpen the HTML file in your browser."
    )


# =============================================================================
# RUN
# =============================================================================

if __name__ == "__main__":
    main()
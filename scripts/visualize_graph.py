from pathlib import Path
import base64
import html
import json

from bs4 import BeautifulSoup
from pyvis.network import Network


# ============================================================
# Paths
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

DATA_FILE = PROJECT_ROOT / "data" / "lalka_presentation_graph.json"
LOGO_FILE = PROJECT_ROOT / "assets" / "pbl-logo.png"
BACKGROUND_IMAGE_FILE = PROJECT_ROOT / "assets" / "lalka-background.jpg"

OUTPUT_DIR = PROJECT_ROOT / "docs"
OUTPUT_FILE = OUTPUT_DIR / "lalka_graph.html"


# ============================================================
# Visual settings
# ============================================================

BACKGROUND = "#f8f6f2"
TEXT_COLOR = "#50504f"
EDGE_COLOR = "#b9b3aa"


COLORS = {
    "Work": "#e2a84a",
    "Adaptation": "#d95b67",
    "Person": "#9a5b91",

    # Publication and RelatedRecord are intentionally
    # visually identical.
    "Publication": "#2a9b90",
    "RelatedRecord": "#2a9b90",

    "Source": "#8a7662",
    "Publisher": "#c99a5a",
}


# Publication and RelatedRecord intentionally
# have exactly the same visual size.

NODE_SIZES = {
    "Work": 38,
    "Adaptation": 29,
    "Person": 19,
    "Publication": 17,
    "RelatedRecord": 17,
    "Source": 12,
    "Publisher": 12,
}


# ============================================================
# Graph label lengths
# ============================================================

GRAPH_LABEL_LENGTHS = {
    "Work": 20,
    "Adaptation": 38,
    "Person": 30,
    "Publication": 42,
    "RelatedRecord": 42,
    "Source": 34,
    "Publisher": 30,
}


# ============================================================
# Labels
# ============================================================

TYPE_LABELS = {
    "Work": "Utwór",
    "Adaptation": "Adaptacja",
    "Person": "Osoba",
    "Publication": "Publikacja",
    "RelatedRecord": "Rekord powiązany",
    "Source": "Źródło",
    "Publisher": "Wydawca",
}


RELATIONSHIP_LABELS = {
    "ADAPTED_AS": "adaptacja",
    "AUTHORED_BY": "autor",
    "CREATED_BY": "twórca",
    "FROM_SOURCE": "źródło",
    "HAS_RECORD": "rekord",
    "PUBLISHED_BY": "wydawca",
    "RELATED_TO": "powiązane",
}


# ============================================================
# Edge styles
# ============================================================

EDGE_STYLES = {
    "ADAPTED_AS": {
        "width": 2.6,
        "color": "#87745e",
        "label": "adaptacja",
    },
    "HAS_RECORD": {
        "width": 1.8,
        "color": "#9e9991",
        "label": "rekord",
    },
    "CREATED_BY": {
        "width": 1.8,
        "color": "#9e9991",
        "label": "twórca",
    },
    "RELATED_TO": {
        "width": 1.0,
        "color": "#c8c3bb",
        "label": "",
    },
    "AUTHORED_BY": {
        "width": 1.0,
        "color": "#c8c3bb",
        "label": "",
    },
    "PUBLISHED_BY": {
        "width": 1.0,
        "color": "#c8c3bb",
        "label": "",
    },
    "FROM_SOURCE": {
        "width": 1.0,
        "color": "#c8c3bb",
        "label": "",
    },
}


# ============================================================
# Data loading
# ============================================================

def load_graph():
    """
    Load the presentation graph from JSON.
    """

    if not DATA_FILE.exists():
        raise FileNotFoundError(
            f"Graph file not found:\n{DATA_FILE}"
        )

    with open(
        DATA_FILE,
        "r",
        encoding="utf-8",
    ) as f:
        return json.load(f)


# ============================================================
# General helpers
# ============================================================

def get_node_type(node):
    """
    Return the presentation node type.
    """

    return (
        node.get("presentation_type")
        or node.get("type")
        or "Unknown"
    )


def clean_html(value):
    """
    Convert HTML-containing values to plain text.
    """

    if value is None:
        return ""

    value = str(value)

    soup = BeautifulSoup(
        value,
        "html.parser",
    )

    text = soup.get_text(
        " ",
        strip=True,
    )

    return html.unescape(text)


def shorten_text(value, max_length):
    """
    Shorten text at a word boundary.

    The full value remains available in the details panel
    and tooltip.
    """

    text = clean_html(value)

    if len(text) <= max_length:
        return text

    shortened = text[:max_length - 1].rsplit(
        " ",
        1,
    )[0]

    if not shortened:
        shortened = text[:max_length - 1]

    return shortened + "…"


# ============================================================
# Node titles and labels
# ============================================================

def get_node_title(node):
    """
    Return the full human-readable title of a node.
    """

    node_id = node.get("id")

    # --------------------------------------------------------
    # Important manually defined nodes
    # --------------------------------------------------------

    if node_id == "record:109715":
        return "Lalka"

    if node_id == "record:304249":
        return "Lalka (prem. 1968)"

    if node_id == "record:136679":
        return "Lalka (TV) – Lalka (prem. 1977)"

    properties = node.get(
        "properties",
        {},
    )

    # --------------------------------------------------------
    # Persons
    # --------------------------------------------------------

    for key in (
        "name",
        "person_name",
        "full_name",
        "author_name",
        "creator_name",
    ):
        if properties.get(key):
            return clean_html(
                properties[key]
            )

    # --------------------------------------------------------
    # General titles
    # --------------------------------------------------------

    for key in (
        "title",
        "name",
        "display_name",
        "label",
    ):
        if properties.get(key):
            return clean_html(
                properties[key]
            )

    # --------------------------------------------------------
    # Fallback
    # --------------------------------------------------------

    if node.get("label"):
        return clean_html(
            node["label"]
        )

    return node_id or "Brak nazwy"


def get_graph_label(node):
    """
    Return a shortened label displayed directly on the graph.

    Publication and RelatedRecord intentionally use
    exactly the same rules.
    """

    node_type = get_node_type(node)
    title = get_node_title(node)

    max_length = GRAPH_LABEL_LENGTHS.get(
        node_type,
        35,
    )

    return shorten_text(
        title,
        max_length,
    )


def get_person_name(node):
    """
    Return a person's name.
    """

    properties = node.get(
        "properties",
        {},
    )

    for key in (
        "name",
        "person_name",
        "full_name",
        "author_name",
        "creator_name",
    ):
        if properties.get(key):
            return clean_html(
                properties[key]
            )

    return get_node_title(node)


# ============================================================
# Details panel data
# ============================================================

def get_metadata(node):
    """
    Return the metadata shown in the details panel.

    PBL metadata is stored inside node["properties"].
    """

    properties = node.get(
        "properties",
        {},
    )

    metadata = {}

    # --------------------------------------------------------
    # PBL ID
    # --------------------------------------------------------

    pbl_id = properties.get("pbl_id")

    if pbl_id is not None:
        metadata["PBL ID"] = pbl_id

    # --------------------------------------------------------
    # PBL record type
    # --------------------------------------------------------

    pbl_type = properties.get("pbl_type")

    if pbl_type:
        metadata["Rodzaj zapisu"] = clean_html(
            pbl_type
        )

    # --------------------------------------------------------
    # Publication year
    # --------------------------------------------------------

    publication_year = properties.get(
        "publication_year"
    )

    if publication_year is not None:
        metadata["Rok publikacji"] = publication_year

    # --------------------------------------------------------
    # Source
    # --------------------------------------------------------

    source = properties.get("source")

    if source:
        metadata["Źródło"] = clean_html(
            source
        )

    return metadata


def get_description(node):
    """
    Return an optional description.
    """

    properties = node.get(
        "properties",
        {},
    )

    for key in (
        "description",
        "note",
        "notes",
    ):
        if properties.get(key):
            return clean_html(
                properties[key]
            )

    return ""


# ============================================================
# Node preparation
# ============================================================

def prepare_node(node):
    """
    Prepare visual properties of a graph node.
    """

    node_id = node.get("id")
    node_type = get_node_type(node)

    title = get_node_title(node)
    graph_label = get_graph_label(node)

    color = COLORS.get(
        node_type,
        "#999999",
    )

    size = NODE_SIZES.get(
        node_type,
        15,
    )

    # --------------------------------------------------------
    # Publication / RelatedRecord
    # --------------------------------------------------------
    #
    # Deliberately identical.
    # --------------------------------------------------------

    if node_type in (
        "Publication",
        "RelatedRecord",
    ):
        color = COLORS["Publication"]
        size = NODE_SIZES["Publication"]

    # --------------------------------------------------------
    # Tooltip
    # --------------------------------------------------------

    tooltip = title

    metadata = get_metadata(node)

    if metadata:

        tooltip_parts = [title]

        for key, value in metadata.items():
            tooltip_parts.append(
                f"{key}: {value}"
            )

        tooltip = "<br>".join(
            str(value)
            for value in tooltip_parts
        )

    # --------------------------------------------------------
    # Original node color
    #
    # This is kept so that the graph can be restored after
    # highlighting.
    # --------------------------------------------------------

    node_color = {
        "background": color,
        "border": color,
        "highlight": {
            "background": color,
            "border": TEXT_COLOR,
        },
        "hover": {
            "background": color,
            "border": TEXT_COLOR,
        },
    }

    return {
        "id": node_id,
        "label": graph_label,
        "title": tooltip,
        "color": node_color,
        "originalColor": node_color,
        "size": size,
        "font": {
            "face": "Arial",
            "size": 15,
            "color": TEXT_COLOR,
        },
        "borderWidth": 1.5,
        "shadow": True,
    }


# ============================================================
# Main
# ============================================================

def main():

    # --------------------------------------------------------
    # Load graph
    # --------------------------------------------------------

    graph = load_graph()

    nodes = graph.get(
        "nodes",
        [],
    )

    edges = graph.get(
        "edges",
        [],
    )

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    # --------------------------------------------------------
    # Create PyVis network
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # Physics / interaction
    # --------------------------------------------------------

    net.set_options(
        json.dumps(
            {
                "interaction": {
                    "hover": True,
                    "navigationButtons": True,
                    "keyboard": {
                        "enabled": True,
                    },
                    "multiselect": False,
                    "hideEdgesOnDrag": False,
                },

                "physics": {
                    "enabled": True,

                    "barnesHut": {
                        "gravitationalConstant": -8000,
                        "centralGravity": 0.18,
                        "springLength": 190,
                        "springConstant": 0.03,
                        "damping": 0.85,
                        "avoidOverlap": 1.2,
                    },

                    "stabilization": {
                        "enabled": True,
                        "iterations": 1000,
                        "updateInterval": 50,
                    },
                },

                "nodes": {
                    "shape": "dot",

                    "font": {
                        "face": "Arial",
                        "color": TEXT_COLOR,
                        "size": 15,
                    },

                    "borderWidth": 1.5,
                    "borderWidthSelected": 3,

                    "shadow": {
                        "enabled": True,
                        "color": "rgba(80,80,79,0.15)",
                        "size": 8,
                        "x": 2,
                        "y": 3,
                    },
                },

                "edges": {
                    "color": {
                        "color": EDGE_COLOR,
                        "highlight": TEXT_COLOR,
                        "hover": "#87745e",
                    },

                    "width": 1.2,
                    "selectionWidth": 2.5,

                    "smooth": {
                        "enabled": True,
                        "type": "dynamic",
                    },

                    "arrows": {
                        "to": {
                            "enabled": True,
                            "scaleFactor": 0.45,
                        },
                    },

                    "font": {
                        "face": "Arial",
                        "size": 11,
                        "color": "#87745e",
                        "strokeWidth": 3,
                        "strokeColor": BACKGROUND,
                    },
                },
            }
        )
    )

    # ========================================================
    # Nodes
    # ========================================================

    details_data = {}

    for node in nodes:

        node_id = node.get("id")
        node_type = get_node_type(node)

        prepared = prepare_node(node)

        # ----------------------------------------------------
        # Central Lalka node
        # ----------------------------------------------------

        if node_id == "record:109715":

            prepared["label"] = "Lalka"
            prepared["size"] = 48

            prepared["color"] = {
                "background": COLORS["Work"],
                "border": "#ffffff",

                "highlight": {
                    "background": COLORS["Work"],
                    "border": "#ffffff",
                },

                "hover": {
                    "background": COLORS["Work"],
                    "border": "#ffffff",
                },
            }

            prepared["originalColor"] = prepared["color"]

            prepared["font"] = {
                "face": "Arial",
                "size": 24,
                "color": "#ffffff",
                "bold": True,
            }

            prepared["borderWidth"] = 3

        # ----------------------------------------------------
        # Add node
        # ----------------------------------------------------

        net.add_node(
            prepared["id"],
            label=prepared["label"],
            title=prepared["title"],
            color=prepared["color"],
            size=prepared["size"],
            font=prepared["font"],
            borderWidth=prepared["borderWidth"],
            shadow=prepared["shadow"],
            originalColor=prepared["originalColor"],
        )

        # ----------------------------------------------------
        # Details data
        # ----------------------------------------------------

        details_data[node_id] = {
            "id": node_id,
            "type": node_type,
            "title": get_node_title(node),
            "metadata": get_metadata(node),
            "description": get_description(node),
        }

    # ========================================================
    # Edges
    # ========================================================

    for index, edge in enumerate(edges):

        source = edge.get("source")
        target = edge.get("target")

        relationship = (
            edge.get("relationship")
            or edge.get("type")
            or edge.get("relation")
            or ""
        )

        style = EDGE_STYLES.get(
            relationship,
            {
                "width": 1.0,
                "color": EDGE_COLOR,
                "label": "",
            },
        )

        relationship_label = (
            RELATIONSHIP_LABELS.get(
                relationship,
                relationship,
            )
        )

        label = style.get(
            "label",
            "",
        )

        edge_id = f"edge_{index}"

        net.add_edge(
            source,
            target,
            id=edge_id,
            label=label,
            title=relationship_label,
            width=style["width"],
            color=style["color"],
            arrows="to",
            smooth=True,

            # Original settings used by JavaScript
            # when the graph is reset.
            originalWidth=style["width"],
            originalColor=style["color"],
        )

    # ========================================================
    # Logo
    # ========================================================

    logo_data = ""

    if LOGO_FILE.exists():

        with open(
            LOGO_FILE,
            "rb",
        ) as f:

            encoded = base64.b64encode(
                f.read()
            ).decode("ascii")

        logo_data = (
            "data:image/png;base64,"
            + encoded
        )

    # ========================================================
    # Background image
    # ========================================================

    background_css = f"""
        background-color: {BACKGROUND} !important;
    """

    if BACKGROUND_IMAGE_FILE.exists():

        suffix = (
            BACKGROUND_IMAGE_FILE
            .suffix
            .lower()
        )

        mime_types = {
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
            ".webp": "image/webp",
        }

        mime = mime_types.get(
            suffix,
            "image/jpeg",
        )

        with open(
            BACKGROUND_IMAGE_FILE,
            "rb",
        ) as f:

            encoded = base64.b64encode(
                f.read()
            ).decode("ascii")

        background_uri = (
            f"data:{mime};base64,{encoded}"
        )

        background_css = f"""
            background-color: {BACKGROUND} !important;

            background-image:
                linear-gradient(
                    rgba(248, 246, 242, 0.91),
                    rgba(248, 246, 242, 0.91)
                ),
                url("{background_uri}") !important;

            background-size: cover;
            background-position: center;
            background-attachment: fixed;
        """

    # ========================================================
    # Logo HTML
    # ========================================================

    logo_html = ""

    if logo_data:

        logo_html = f"""
        <div class="pbl-logo">
            <img
                src="{logo_data}"
                alt="Polska Bibliografia Literacka"
            >
        </div>
        """

    # ========================================================
    # Details JSON
    # ========================================================

    details_json = json.dumps(
        details_data,
        ensure_ascii=False,
    )

    # Protect the embedded JSON from accidentally closing
    # the script element.
    details_json = (
        details_json
        .replace("<", "\\u003c")
        .replace(">", "\\u003e")
        .replace("&", "\\u0026")
    )

    # ========================================================
    # Custom HTML / CSS / JavaScript
    # ========================================================

    custom_html = f"""
    <style>

        /* ==================================================
           Base
           ================================================== */

        html,
        body {{
            margin: 0;
            padding: 0;
            width: 100%;
            height: 100%;
            overflow: hidden;
            background: {BACKGROUND};
            font-family: Arial, sans-serif;
        }}

        #mynetwork {{
            width: 100%;
            height: 100vh;
            {background_css}
        }}


        /* ==================================================
           Header
           ================================================== */

        .graph-header {{
            position: fixed;
            top: 20px;
            left: 24px;
            z-index: 1000;
            pointer-events: none;

            background:
                rgba(
                    248,
                    246,
                    242,
                    0.90
                );

            padding: 12px 16px;
            border-radius: 8px;

            box-shadow:
                0 2px 12px
                rgba(0, 0, 0, 0.08);
        }}

        .graph-header-title {{
            font-size: 20px;
            font-weight: 600;
            color: {TEXT_COLOR};
            margin-bottom: 3px;
        }}

        .graph-header-subtitle {{
            font-size: 12px;
            color: #77736e;
        }}


        /* ==================================================
           PBL logo
           ================================================== */

        .pbl-logo {{
            position: fixed;
            top: 20px;
            right: 24px;
            z-index: 1000;
            pointer-events: none;

            background:
                rgba(
                    248,
                    246,
                    242,
                    0.90
                );

            padding: 8px 12px;
            border-radius: 8px;
        }}

        .pbl-logo img {{
            display: block;
            max-width: 180px;
            max-height: 55px;
        }}


        /* ==================================================
           Legend
           ================================================== */

        .legend {{
            position: fixed;
            bottom: 22px;
            left: 24px;
            z-index: 1000;

            background:
                rgba(
                    248,
                    246,
                    242,
                    0.94
                );

            padding: 12px 15px;
            border-radius: 8px;

            box-shadow:
                0 2px 12px
                rgba(0, 0, 0, 0.08);

            font-size: 12px;
            color: {TEXT_COLOR};
        }}

        .legend-title {{
            font-weight: 600;
            margin-bottom: 8px;
        }}

        .legend-item {{
            display: flex;
            align-items: center;
            margin: 5px 0;
        }}

        .legend-dot {{
            width: 11px;
            height: 11px;
            border-radius: 50%;
            margin-right: 8px;
            flex-shrink: 0;
        }}


        /* ==================================================
           Details panel
           ================================================== */

        .details-panel {{
            position: fixed;
            top: 90px;
            right: 24px;
            z-index: 1001;

            width: 380px;
            max-height: calc(100vh - 130px);

            overflow-y: auto;

            background:
                rgba(
                    248,
                    246,
                    242,
                    0.97
                );

            border-radius: 10px;

            box-shadow:
                0 4px 22px
                rgba(0, 0, 0, 0.13);

            padding: 18px;
            box-sizing: border-box;

            display: none;
        }}

        .details-panel.visible {{
            display: block;
        }}

        .details-type {{
            font-size: 11px;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            color: #87745e;
            margin-bottom: 7px;
        }}

        .details-title {{
            font-size: 19px;
            line-height: 1.35;
            font-weight: 600;
            color: {TEXT_COLOR};
            margin-bottom: 15px;
        }}

        .details-row {{
            display: flex;
            gap: 10px;
            margin: 7px 0;
            font-size: 13px;
            line-height: 1.4;
        }}

        .details-key {{
            width: 105px;
            flex-shrink: 0;
            color: #77736e;
        }}

        .details-value {{
            color: {TEXT_COLOR};
            word-break: break-word;
        }}

        .details-description {{
            margin-top: 14px;
            padding-top: 12px;
            border-top: 1px solid #ded9d1;
            font-size: 13px;
            line-height: 1.5;
            color: {TEXT_COLOR};
        }}


        /* ==================================================
           Interaction hint
           ================================================== */

        .interaction-hint {{
            position: fixed;
            bottom: 22px;
            right: 24px;
            z-index: 1000;

            background:
                rgba(
                    248,
                    246,
                    242,
                    0.90
                );

            padding: 8px 12px;
            border-radius: 7px;

            font-size: 11px;
            color: #77736e;

            pointer-events: none;
        }}


        /* ==================================================
           Mobile / small screens
           ================================================== */

        @media (max-width: 700px) {{

            .graph-header {{
                top: 10px;
                left: 10px;
            }}

            .graph-header-title {{
                font-size: 16px;
            }}

            .pbl-logo {{
                top: 10px;
                right: 10px;
            }}

            .pbl-logo img {{
                max-width: 120px;
                max-height: 40px;
            }}

            .details-panel {{
                top: 70px;
                right: 10px;
                left: 10px;
                width: auto;
                max-height: 45vh;
            }}

            .legend {{
                bottom: 10px;
                left: 10px;
            }}

            .interaction-hint {{
                display: none;
            }}
        }}

    </style>


    <!-- ====================================================
         Header
         ==================================================== -->

    <div class="graph-header">

        <div class="graph-header-title">
            Lalka Knowledge Graph
        </div>

        <div class="graph-header-subtitle">
            Polska Bibliografia Literacka
        </div>

    </div>


    <!-- ====================================================
         Logo
         ==================================================== -->

    {logo_html}


    <!-- ====================================================
         Legend
         ==================================================== -->

    <div class="legend">

        <div class="legend-title">
            Typy węzłów
        </div>

        <div class="legend-item">
            <span
                class="legend-dot"
                style="background:{COLORS["Work"]};"
            ></span>
            Utwór
        </div>

        <div class="legend-item">
            <span
                class="legend-dot"
                style="background:{COLORS["Adaptation"]};"
            ></span>
            Adaptacja
        </div>

        <div class="legend-item">
            <span
                class="legend-dot"
                style="background:{COLORS["Person"]};"
            ></span>
            Osoba
        </div>

        <div class="legend-item">
            <span
                class="legend-dot"
                style="background:{COLORS["Publication"]};"
            ></span>
            Publikacja / rekord
        </div>

        <div class="legend-item">
            <span
                class="legend-dot"
                style="background:{COLORS["Source"]};"
            ></span>
            Źródło
        </div>

        <div class="legend-item">
            <span
                class="legend-dot"
                style="background:{COLORS["Publisher"]};"
            ></span>
            Wydawca
        </div>

    </div>


    <!-- ====================================================
         Details panel
         ==================================================== -->

    <div
        id="details-panel"
        class="details-panel"
    ></div>


    <!-- ====================================================
         Interaction hint
         ==================================================== -->

    <div class="interaction-hint">
        Kliknij węzeł, aby zobaczyć szczegóły
        · dwuklik — przybliżenie
    </div>


    <!-- ====================================================
         JavaScript
         ==================================================== -->

    <script>

        /*
         * IMPORTANT:
         *
         * Do NOT declare:
         *
         *     const network = window.network;
         *
         * PyVis already creates the `network` variable
         * in the generated HTML.
         */

        const detailsData = {details_json};


        // ==================================================
        // HTML escaping
        // ==================================================

        function escapeHtml(value) {{

            if (
                value === null ||
                value === undefined
            ) {{
                return "";
            }}

            return String(value)
                .replace(/&/g, "&amp;")
                .replace(/</g, "&lt;")
                .replace(/>/g, "&gt;")
                .replace(/"/g, "&quot;")
                .replace(/'/g, "&#039;");
        }}


        // ==================================================
        // Type labels
        // ==================================================

        function getTypeLabel(type) {{

            const labels = {{
                "Work": "Utwór",
                "Adaptation": "Adaptacja",
                "Person": "Osoba",
                "Publication": "Publikacja",
                "RelatedRecord": "Rekord powiązany",
                "Source": "Źródło",
                "Publisher": "Wydawca"
            }};

            return labels[type] || type || "";
        }}


        // ==================================================
        // Details HTML
        // ==================================================

        function buildDetailsHtml(data) {{

            if (!data) {{
                return "";
            }}

            let result = "";


            result += `
                <div class="details-type">
                    ${{escapeHtml(
                        getTypeLabel(data.type)
                    )}}
                </div>
            `;


            result += `
                <div class="details-title">
                    ${{escapeHtml(data.title)}}
                </div>
            `;


            if (data.metadata) {{

                for (
                    const [key, value]
                    of Object.entries(data.metadata)
                ) {{

                    if (
                        value === null ||
                        value === undefined ||
                        value === ""
                    ) {{
                        continue;
                    }}

                    result += `
                        <div class="details-row">

                            <div class="details-key">
                                ${{escapeHtml(key)}}
                            </div>

                            <div class="details-value">
                                ${{escapeHtml(value)}}
                            </div>

                        </div>
                    `;
                }}
            }}


            if (data.description) {{

                result += `
                    <div class="details-description">
                        ${{escapeHtml(
                            data.description
                        )}}
                    </div>
                `;
            }}


            return result;
        }}


        // ==================================================
        // Original edge color
        // ==================================================

        function getOriginalEdgeColor(edge) {{

            if (edge.originalColor) {{

                return {{
                    color: edge.originalColor,
                    opacity: 1
                }};
            }}


            if (
                edge.color &&
                typeof edge.color === "object" &&
                edge.color.color
            ) {{

                return {{
                    color: edge.color.color,
                    opacity: 1
                }};
            }}


            if (
                edge.color &&
                typeof edge.color === "string"
            ) {{

                return {{
                    color: edge.color,
                    opacity: 1
                }};
            }}


            return {{
                color: "{EDGE_COLOR}",
                opacity: 1
            }};
        }}


        // ==================================================
        // Original node color
        // ==================================================

        function getOriginalNodeColor(node) {{

            if (node.originalColor) {{
                return node.originalColor;
            }}

            if (node.color) {{
                return node.color;
            }}

            return {{
                background: "#999999",
                border: "#999999"
            }};
        }}


        // ==================================================
        // Reset graph
        // ==================================================

        function resetGraph() {{

            // ----------------------------------------------
            // Restore node colors
            // ----------------------------------------------

            const nodeUpdates = [];

            network.body.data.nodes
                .get()
                .forEach(node => {{

                    nodeUpdates.push({{
                        id: node.id,
                        color:
                            getOriginalNodeColor(node)
                    }});
                }});


            network.body.data.nodes.update(
                nodeUpdates
            );


            // ----------------------------------------------
            // Restore edge colors and widths
            // ----------------------------------------------

            const edgeUpdates = [];

            network.body.data.edges
                .get()
                .forEach(edge => {{

                    const originalColor =
                        getOriginalEdgeColor(edge);

                    edgeUpdates.push({{
                        id: edge.id,

                        color: originalColor,

                        width:
                            edge.originalWidth ||
                            1.0
                    }});
                }});


            network.body.data.edges.update(
                edgeUpdates
            );
        }}


        // ==================================================
        // Highlight selected node
        // ==================================================

        function highlightNode(nodeId) {{

            const connectedNodes =
                new Set(
                    network.getConnectedNodes(
                        nodeId
                    )
                );

            connectedNodes.add(nodeId);


            // ----------------------------------------------
            // Nodes
            // ----------------------------------------------

            const nodeUpdates = [];

            network.body.data.nodes
                .get()
                .forEach(node => {{

                    const connected =
                        connectedNodes.has(
                            node.id
                        );


                    const originalColor =
                        getOriginalNodeColor(node);


                    if (connected) {{

                        nodeUpdates.push({{
                            id: node.id,

                            color: originalColor
                        }});

                    }} else {{

                        nodeUpdates.push({{
                            id: node.id,

                            color: {{
                                background:
                                    "#d7d4cf",

                                border:
                                    "#d0ccc6",

                                highlight: {{
                                    background:
                                        "#d7d4cf",

                                    border:
                                        "#aaa59d"
                                }},

                                hover: {{
                                    background:
                                        "#d7d4cf",

                                    border:
                                        "#aaa59d"
                                }}
                            }}
                        }});
                    }}
                }});


            network.body.data.nodes.update(
                nodeUpdates
            );


            // ----------------------------------------------
            // Edges
            // ----------------------------------------------

            const connectedEdges =
                new Set(
                    network.getConnectedEdges(
                        nodeId
                    )
                );


            const edgeUpdates = [];

            network.body.data.edges
                .get()
                .forEach(edge => {{

                    const connected =
                        connectedEdges.has(
                            edge.id
                        );


                    const originalWidth =
                        edge.originalWidth ||
                        1.0;


                    if (connected) {{

                        edgeUpdates.push({{
                            id: edge.id,

                            color: {{
                                color: "#50504f",
                                opacity: 1
                            }},

                            width:
                                Math.max(
                                    originalWidth,
                                    2
                                )
                        }});

                    }} else {{

                        edgeUpdates.push({{
                            id: edge.id,

                            color: {{
                                color: "#d8d3cb",
                                opacity: 0.20
                            }},

                            width:
                                originalWidth
                        }});
                    }}
                }});


            network.body.data.edges.update(
                edgeUpdates
            );
        }}


        // ==================================================
        // Details panel
        // ==================================================

        function showDetails(nodeId) {{

            const panel =
                document.getElementById(
                    "details-panel"
                );


            const data =
                detailsData[nodeId];


            if (!data) {{

                panel.classList.remove(
                    "visible"
                );

                return;
            }}


            panel.innerHTML =
                buildDetailsHtml(data);


            panel.classList.add(
                "visible"
            );
        }}


        // ==================================================
        // Click
        // ==================================================

        network.on(
            "click",
            function(params) {{

                // ------------------------------------------
                // Clicked a node
                // ------------------------------------------

                if (
                    params.nodes &&
                    params.nodes.length > 0
                ) {{

                    const nodeId =
                        params.nodes[0];


                    // Stop the graph immediately.
                    network.setOptions({{
                        physics: {{
                            enabled: false
                        }}
                    }});


                    // Highlight selected node and
                    // its directly connected neighbourhood.
                    highlightNode(
                        nodeId
                    );


                    // Show metadata panel.
                    showDetails(
                        nodeId
                    );


                }} else {{

                    // --------------------------------------
                    // Clicked empty space
                    // --------------------------------------

                    resetGraph();


                    document
                        .getElementById(
                            "details-panel"
                        )
                        .classList.remove(
                            "visible"
                        );


                    // Start physics again.
                    network.setOptions({{
                        physics: {{
                            enabled: true
                        }}
                    }});
                }}
            }}
        );


        // ==================================================
        // Double click
        // ==================================================

        network.on(
            "doubleClick",
            function(params) {{

                if (
                    params.nodes &&
                    params.nodes.length > 0
                ) {{

                    // Keep the graph stopped while focusing.
                    network.setOptions({{
                        physics: {{
                            enabled: false
                        }}
                    }});


                    network.focus(
                        params.nodes[0],
                        {{
                            scale: 1.3,

                            animation: {{
                                duration: 500,
                                easingFunction:
                                    "easeInOutQuad"
                            }}
                        }}
                    );
                }}
            }}
        );

    </script>
    """


    # ========================================================
    # Generate PyVis HTML
    # ========================================================

    # Do NOT use net.write_html().
    #
    # On Windows PyVis can use the system encoding (e.g.
    # cp1250), which fails for some Unicode characters.
    #
    # generate_html() gives us the HTML as a Python string,
    # which we explicitly save as UTF-8 below.

    html_content = net.generate_html(
        notebook=False
    )


    # ========================================================
    # Inject custom HTML
    # ========================================================

    html_content = html_content.replace(
        "</body>",
        custom_html + "\n</body>",
    )


    # ========================================================
    # Save as UTF-8
    # ========================================================

    with open(
        OUTPUT_FILE,
        "w",
        encoding="utf-8",
        newline="",
    ) as f:

        f.write(
            html_content
        )


    # ========================================================
    # Final information
    # ========================================================

    print(
        f"Graph saved to: {OUTPUT_FILE}"
    )

    print(
        f"Nodes: {len(nodes)}"
    )

    print(
        f"Edges: {len(edges)}"
    )


# ============================================================
# Entry point
# ============================================================

if __name__ == "__main__":
    main()
"""
Extract data from the PBL Oracle database for the "Lalka" project.

The script extracts:
- records attached to the work "Lalka",
- nested records attached to those records,
- records connected with Bolesław Prus,
- records connected with the identified screen adaptations of "Lalka",
- authors,
- creators,
- publishers,
- record types / kinds from PBL_RODZAJE_ZAPISOW.

Database credentials and Oracle Client configuration are read from
environment variables and are NOT stored in the repository.

Required environment variables:

    PBL_ORACLE_HOST
    PBL_ORACLE_PORT
    PBL_ORACLE_SERVICE
    PBL_ORACLE_USER
    PBL_ORACLE_PASSWORD
    PBL_ORACLE_LIB_DIR

Run from the project root:

    python scripts/extract_lalka.py
"""


from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path

import oracledb
import pandas as pd


# =============================================================================
# Configuration
# =============================================================================

# PBL ID of the work "Lalka"
LALKA_ID = 109715

# PBL IDs associated with Bolesław Prus
PRUS_TWORCA_ID = 3426
PRUS_AUTOR_ID = 1082

# PBL IDs of the identified screen adaptations of "Lalka"
LALKA_SCREEN_ADAPTATION_IDS = [
    304249,
    136679,
]

# Number of hierarchy levels to retrieve
LALKA_NESTED_LEVELS = 2
PRUS_NESTED_LEVELS = 2
SCREEN_ADAPTATION_NESTED_LEVELS = 1


# =============================================================================
# Paths
# =============================================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

OUTPUT_DIR = PROJECT_ROOT / "data"

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True,
)


# =============================================================================
# Oracle connection
# =============================================================================

def get_database_connection() -> oracledb.Connection:
    """
    Connect to the PBL Oracle database.

    Connection parameters are read from environment variables.
    """

    required_variables = [
        "PBL_ORACLE_HOST",
        "PBL_ORACLE_PORT",
        "PBL_ORACLE_SERVICE",
        "PBL_ORACLE_USER",
        "PBL_ORACLE_PASSWORD",
        "PBL_ORACLE_LIB_DIR",
    ]

    missing_variables = [
        variable
        for variable in required_variables
        if not os.environ.get(variable)
    ]

    if missing_variables:
        raise RuntimeError(
            "Missing required environment variables: "
            + ", ".join(missing_variables)
        )

    # Oracle Instant Client
    oracle_client_path = os.environ[
        "PBL_ORACLE_LIB_DIR"
    ]

    try:
        oracledb.init_oracle_client(
            lib_dir=oracle_client_path
        )
    except oracledb.ProgrammingError:
        # Oracle Client has already been initialized.
        pass

    hostname = os.environ[
        "PBL_ORACLE_HOST"
    ]

    port = int(
        os.environ["PBL_ORACLE_PORT"]
    )

    service_name = os.environ[
        "PBL_ORACLE_SERVICE"
    ]

    user = os.environ[
        "PBL_ORACLE_USER"
    ]

    password = os.environ[
        "PBL_ORACLE_PASSWORD"
    ]

    dsn = oracledb.makedsn(
        hostname,
        port,
        service_name=service_name,
    )

    connection = oracledb.connect(
        user=user,
        password=password,
        dsn=dsn,
    )

    return connection


# =============================================================================
# Utilities
# =============================================================================

def chunk_list(
    values: list[int],
    chunk_size: int = 999,
):
    """
    Split a list into chunks.

    Oracle has a limit on the number of expressions
    that can be used in an IN clause.
    """

    for start in range(
        0,
        len(values),
        chunk_size,
    ):
        yield values[
            start:start + chunk_size
        ]


def unique_ids(
    values: list[int | None],
) -> list[int]:
    """
    Remove None values and duplicate IDs
    while preserving order.
    """

    result = []
    seen = set()

    for value in values:

        if value is None:
            continue

        value = int(value)

        if value not in seen:
            result.append(value)
            seen.add(value)

    return result


def dataframe_to_records(
    dataframe: pd.DataFrame,
) -> list[dict]:
    """
    Convert a pandas DataFrame into JSON-compatible dictionaries.
    """

    records = dataframe.to_dict(
        orient="records"
    )

    cleaned_records = []

    for record in records:

        cleaned_record = {}

        for key, value in record.items():

            if pd.isna(value):

                cleaned_record[key] = None

            elif hasattr(value, "item"):

                cleaned_record[key] = value.item()

            else:

                cleaned_record[key] = value

        cleaned_records.append(
            cleaned_record
        )

    return cleaned_records


# =============================================================================
# Record hierarchy
# =============================================================================

def get_child_records(
    ids: list[int],
    connection: oracledb.Connection,
) -> list[int]:
    """
    Return IDs of records directly attached to the supplied records.

    Relationship:

        PBL_ZAPISY.ZA_ZA_ZAPIS_ID
            ->
        PBL_ZAPISY.ZA_ZAPIS_ID
    """

    ids = unique_ids(ids)

    if not ids:
        return []

    children = []

    for chunk in chunk_list(ids):

        ids_string = ", ".join(
            map(str, chunk)
        )

        query = f"""
            SELECT
                za_zapis_id

            FROM IBL_OWNER.pbl_zapisy

            WHERE za_za_zapis_id IN (
                {ids_string}
            )
        """

        dataframe = pd.read_sql(
            query,
            con=connection,
        )

        if not dataframe.empty:

            children.extend(
                dataframe[
                    "ZA_ZAPIS_ID"
                ].astype(int).tolist()
            )

    return unique_ids(children)


def get_descendants(
    root_ids: list[int],
    connection: oracledb.Connection,
    levels: int,
) -> list[int]:
    """
    Retrieve records attached to root records
    up to the specified number of hierarchy levels.

    The root IDs themselves are included.
    """

    root_ids = unique_ids(root_ids)

    all_ids = list(root_ids)

    current_level = root_ids

    for _ in range(levels):

        children = get_child_records(
            current_level,
            connection,
        )

        new_children = [
            record_id
            for record_id in children
            if record_id not in all_ids
        ]

        all_ids.extend(
            new_children
        )

        current_level = new_children

        if not current_level:
            break

    return unique_ids(all_ids)


# =============================================================================
# Bolesław Prus
# =============================================================================

def get_prus_record_ids(
    connection: oracledb.Connection,
) -> list[int]:
    """
    Find records where Bolesław Prus appears
    as an author or creator.

    The IDs are based on the existing PBL database exploration.
    """

    query = f"""
        SELECT DISTINCT

            z.za_zapis_id

        FROM IBL_OWNER.pbl_zapisy z

        LEFT JOIN IBL_OWNER.pbl_zapisy_autorzy a
            ON z.za_zapis_id =
               a.zaam_za_zapis_id

        LEFT JOIN IBL_OWNER.pbl_autorzy t
            ON a.zaam_am_autor_id =
               t.am_autor_id

        LEFT JOIN IBL_OWNER.pbl_zapisy_tworcy ztw
            ON ztw.zatw_za_zapis_id =
               z.za_zapis_id

        LEFT JOIN IBL_OWNER.pbl_tworcy tw
            ON tw.tw_tworca_id =
               ztw.zatw_tw_tworca_id

        WHERE

            (
                t.am_imie LIKE 'Boles%'
                AND t.am_nazwisko = 'Prus'
            )

            OR

            (
                tw.tw_imie LIKE 'Boles%'
                AND tw.tw_nazwisko = 'Prus'
            )

        ORDER BY
            z.za_zapis_id
    """

    dataframe = pd.read_sql(
        query,
        con=connection,
    )

    if dataframe.empty:
        return []

    return unique_ids(
        dataframe[
            "ZA_ZAPIS_ID"
        ].tolist()
    )


# =============================================================================
# Main PBL records
# =============================================================================

def get_full_records(
    ids: list[int],
    connection: oracledb.Connection,
) -> pd.DataFrame:
    """
    Retrieve the main fields of PBL records.

    Authors, creators and publishers are retrieved separately
    to avoid multiplying records through multi-valued JOINs.

    Record kind is retrieved from PBL_RODZAJE_ZAPISOW.

    Important distinction:

        ZA_TYPE
            -> general PBL record type

        ZA_RZ_RODZAJ1_ID
            -> ID of the detailed record kind

        RZ_NAZWA
            -> name of the detailed record kind
    """

    ids = unique_ids(ids)

    if not ids:
        return pd.DataFrame()

    dataframes = []

    for chunk in chunk_list(ids):

        ids_string = ", ".join(
            map(str, chunk)
        )

        query = f"""
            SELECT

                z.za_zapis_id,

                z.za_za_zapis_id
                    AS zapis_nadrzedny,

                z.za_type,

                z.za_rz_rodzaj1_id,

                r.rz_nazwa,

                z.za_tytul,

                d.dz_dzial_id,

                d.dz_nazwa,

                zr.zr_zrodlo_id,

                zr.zr_tytul,

                z.za_zrodlo_rok,

                z.za_zrodlo_nr,

                z.za_zrodlo_str,

                z.za_seria_wydawnicza,

                z.za_opis_wspoltworcow,

                z.za_wydawnictwa,

                z.za_rok_wydania,

                z.za_opis_fizyczny_ksiazki,

                z.za_adnotacje,

                z.za_opis_imprezy,

                z.za_organizator

            FROM IBL_OWNER.pbl_zapisy z

            LEFT JOIN IBL_OWNER.pbl_zrodla zr
                ON z.za_zr_zrodlo_id =
                   zr.zr_zrodlo_id

            LEFT JOIN IBL_OWNER.pbl_dzialy d
                ON z.za_dz_dzial1_id =
                   d.dz_dzial_id

            LEFT JOIN IBL_OWNER.pbl_rodzaje_zapisow r
                ON z.za_rz_rodzaj1_id =
                   r.rz_rodzaj_id

            WHERE z.za_zapis_id IN (
                {ids_string}
            )
        """

        dataframe = pd.read_sql(
            query,
            con=connection,
        )

        dataframes.append(
            dataframe
        )

    if not dataframes:
        return pd.DataFrame()

    dataframe = pd.concat(
        dataframes,
        ignore_index=True,
    )

    dataframe = dataframe.drop_duplicates(
        subset=[
            "ZA_ZAPIS_ID"
        ]
    )

    # Remove records marked as not yet classified.
    if "DZ_NAZWA" in dataframe.columns:

        dataframe = dataframe[
            dataframe["DZ_NAZWA"]
            != "-- do ustalenia --"
        ]

    return dataframe


# =============================================================================
# Authors
# =============================================================================

def get_authors(
    record_ids: list[int],
    connection: oracledb.Connection,
) -> pd.DataFrame:
    """
    Retrieve authors associated with PBL records.
    """

    record_ids = unique_ids(
        record_ids
    )

    if not record_ids:
        return pd.DataFrame()

    dataframes = []

    for chunk in chunk_list(record_ids):

        ids_string = ", ".join(
            map(str, chunk)
        )

        query = f"""
            SELECT DISTINCT

                a.zaam_za_zapis_id
                    AS zapis_id,

                t.am_autor_id
                    AS autor_id,

                t.am_imie
                    AS imie,

                t.am_nazwisko
                    AS nazwisko

            FROM IBL_OWNER.pbl_zapisy_autorzy a

            LEFT JOIN IBL_OWNER.pbl_autorzy t
                ON a.zaam_am_autor_id =
                   t.am_autor_id

            WHERE a.zaam_za_zapis_id IN (
                {ids_string}
            )
        """

        dataframes.append(
            pd.read_sql(
                query,
                con=connection,
            )
        )

    return pd.concat(
        dataframes,
        ignore_index=True,
    ).drop_duplicates()


# =============================================================================
# Creators
# =============================================================================

def get_creators(
    record_ids: list[int],
    connection: oracledb.Connection,
) -> pd.DataFrame:
    """
    Retrieve creators associated with PBL records.
    """

    record_ids = unique_ids(
        record_ids
    )

    if not record_ids:
        return pd.DataFrame()

    dataframes = []

    for chunk in chunk_list(record_ids):

        ids_string = ", ".join(
            map(str, chunk)
        )

        query = f"""
            SELECT DISTINCT

                ztw.zatw_za_zapis_id
                    AS zapis_id,

                tw.tw_tworca_id
                    AS tworca_id,

                tw.tw_imie
                    AS imie,

                tw.tw_nazwisko
                    AS nazwisko

            FROM IBL_OWNER.pbl_zapisy_tworcy ztw

            LEFT JOIN IBL_OWNER.pbl_tworcy tw
                ON tw.tw_tworca_id =
                   ztw.zatw_tw_tworca_id

            WHERE ztw.zatw_za_zapis_id IN (
                {ids_string}
            )
        """

        dataframes.append(
            pd.read_sql(
                query,
                con=connection,
            )
        )

    return pd.concat(
        dataframes,
        ignore_index=True,
    ).drop_duplicates()


# =============================================================================
# Publishers
# =============================================================================

def get_publishers(
    record_ids: list[int],
    connection: oracledb.Connection,
) -> pd.DataFrame:
    """
    Retrieve publishers associated with PBL records.
    """

    record_ids = unique_ids(
        record_ids
    )

    if not record_ids:
        return pd.DataFrame()

    dataframes = []

    for chunk in chunk_list(record_ids):

        ids_string = ", ".join(
            map(str, chunk)
        )

        query = f"""
            SELECT DISTINCT

                zwyd.zawy_za_zapis_id
                    AS zapis_id,

                w.wy_wydawnictwo_id
                    AS wydawnictwo_id,

                w.wy_nazwa
                    AS nazwa,

                w.wy_miasto
                    AS miasto

            FROM IBL_OWNER.pbl_zapisy_wydawnictwa zwyd

            LEFT JOIN IBL_OWNER.pbl_wydawnictwa w
                ON w.wy_wydawnictwo_id =
                   zwyd.zawy_wy_wydawnictwo_id

            WHERE zwyd.zawy_za_zapis_id IN (
                {ids_string}
            )
        """

        dataframes.append(
            pd.read_sql(
                query,
                con=connection,
            )
        )

    return pd.concat(
        dataframes,
        ignore_index=True,
    ).drop_duplicates()


# =============================================================================
# JSON export
# =============================================================================

def save_json(
    data,
    path: Path,
) -> None:
    """
    Save data as UTF-8 JSON.
    """

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


# =============================================================================
# Main
# =============================================================================

def main() -> None:

    print(
        "Connecting to PBL Oracle database..."
    )

    connection = get_database_connection()

    try:

        # ---------------------------------------------------------------------
        # 1. Lalka
        # ---------------------------------------------------------------------

        print(
            "Finding records attached to Lalka..."
        )

        lalka_ids = get_descendants(
            [LALKA_ID],
            connection,
            levels=LALKA_NESTED_LEVELS,
        )

        print(
            f"  Lalka-related records: "
            f"{len(lalka_ids)}"
        )

        # ---------------------------------------------------------------------
        # 2. Bolesław Prus
        # ---------------------------------------------------------------------

        print(
            "Finding records related to Bolesław Prus..."
        )

        prus_direct_ids = get_prus_record_ids(
            connection
        )

        print(
            f"  Direct Prus records: "
            f"{len(prus_direct_ids)}"
        )

        prus_ids = get_descendants(
            prus_direct_ids,
            connection,
            levels=PRUS_NESTED_LEVELS,
        )

        print(
            f"  Prus-related records including "
            f"nested records: {len(prus_ids)}"
        )

        # ---------------------------------------------------------------------
        # 3. Screen adaptations
        # ---------------------------------------------------------------------

        print(
            "Finding records related to Lalka screen adaptations..."
        )

        screen_adaptation_ids = get_descendants(
            LALKA_SCREEN_ADAPTATION_IDS,
            connection,
            levels=SCREEN_ADAPTATION_NESTED_LEVELS,
        )

        print(
            f"  Screen-adaptation-related records: "
            f"{len(screen_adaptation_ids)}"
        )

        # ---------------------------------------------------------------------
        # 4. Combine IDs
        # ---------------------------------------------------------------------

        all_record_ids = unique_ids(
            lalka_ids
            + prus_ids
            + screen_adaptation_ids
        )

        print()
        print(
            f"Total unique record IDs: "
            f"{len(all_record_ids)}"
        )

        # ---------------------------------------------------------------------
        # 5. Main records
        # ---------------------------------------------------------------------

        print(
            "Downloading main record data..."
        )

        records_df = get_full_records(
            all_record_ids,
            connection,
        )

        print(
            f"  Records downloaded: "
            f"{len(records_df)}"
        )

        # ---------------------------------------------------------------------
        # 6. Authors
        # ---------------------------------------------------------------------

        print(
            "Downloading authors..."
        )

        authors_df = get_authors(
            all_record_ids,
            connection,
        )

        print(
            f"  Author relations: "
            f"{len(authors_df)}"
        )

        # ---------------------------------------------------------------------
        # 7. Creators
        # ---------------------------------------------------------------------

        print(
            "Downloading creators..."
        )

        creators_df = get_creators(
            all_record_ids,
            connection,
        )

        print(
            f"  Creator relations: "
            f"{len(creators_df)}"
        )

        # ---------------------------------------------------------------------
        # 8. Publishers
        # ---------------------------------------------------------------------

        print(
            "Downloading publishers..."
        )

        publishers_df = get_publishers(
            all_record_ids,
            connection,
        )

        print(
            f"  Publisher relations: "
            f"{len(publishers_df)}"
        )

        # ---------------------------------------------------------------------
        # 9. Save raw data
        # ---------------------------------------------------------------------

        print()
        print(
            "Saving extracted data..."
        )

        save_json(
            dataframe_to_records(
                records_df
            ),
            OUTPUT_DIR
            / "lalka_records_raw.json",
        )

        save_json(
            dataframe_to_records(
                authors_df
            ),
            OUTPUT_DIR
            / "lalka_authors_raw.json",
        )

        save_json(
            dataframe_to_records(
                creators_df
            ),
            OUTPUT_DIR
            / "lalka_creators_raw.json",
        )

        save_json(
            dataframe_to_records(
                publishers_df
            ),
            OUTPUT_DIR
            / "lalka_publishers_raw.json",
        )

        # ---------------------------------------------------------------------
        # 10. Metadata
        # ---------------------------------------------------------------------

        metadata = {

            "project":
                "Lalka Knowledge Graph",

            "source":
                "Polska Bibliografia Literacka",

            "extracted_at":
                datetime.now(
                    timezone.utc
                ).isoformat(),

            "root_ids": {

                "lalka":
                    LALKA_ID,

                "prus_tworca":
                    PRUS_TWORCA_ID,

                "prus_autor":
                    PRUS_AUTOR_ID,

                "screen_adaptations":
                    LALKA_SCREEN_ADAPTATION_IDS,
            },

            "nested_levels": {

                "lalka":
                    LALKA_NESTED_LEVELS,

                "prus":
                    PRUS_NESTED_LEVELS,

                "screen_adaptations":
                    SCREEN_ADAPTATION_NESTED_LEVELS,
            },

            "record_fields": {

                "record_type":
                    "ZA_TYPE",

                "record_kind_id":
                    "ZA_RZ_RODZAJ1_ID",

                "record_kind_name":
                    "RZ_NAZWA",
            },

            "counts": {

                "unique_record_ids":
                    len(all_record_ids),

                "records":
                    len(records_df),

                "author_relations":
                    len(authors_df),

                "creator_relations":
                    len(creators_df),

                "publisher_relations":
                    len(publishers_df),
            },
        }

        save_json(
            metadata,
            OUTPUT_DIR
            / "lalka_extraction_metadata.json",
        )

        print()
        print(
            "Extraction completed."
        )

        print(
            f"Data saved to: {OUTPUT_DIR}"
        )

    finally:

        connection.close()

        print(
            "Database connection closed."
        )


if __name__ == "__main__":
    main()
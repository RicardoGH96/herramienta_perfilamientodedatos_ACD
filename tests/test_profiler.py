from __future__ import annotations

import pandas as pd

from src.profiler import build_profiles, semantic_null_mask


def test_semantic_null_mask_recognizes_markers() -> None:
    series = pd.Series([None, "NaN", "??", "valor", "  "])
    mask = semantic_null_mask(series, ["", "NAN", "??"])
    assert mask.tolist() == [True, True, True, False, True]


def test_global_and_segmented_profiles_have_expected_shape() -> None:
    dataframe = pd.DataFrame(
        {
            "ID": ["A-1", "A-2", "A-3", "A-4"],
            "Sistema_Origen": ["WEB", "WEB", "ERP", "??"],
            "Email": ["a@x.com", " b@x.com", None, "c@x.com"],
        }
    )

    global_profile, segmented_profile, origins = build_profiles(
        dataframe,
        table_name="tbl_demo",
        segment_column="Sistema_Origen",
        null_tokens=["", "NAN", "??"],
    )

    assert len(global_profile) == len(dataframe.columns)
    assert len(segmented_profile) == len(dataframe.columns) * 3
    assert global_profile["SistemaOrigen"].unique().tolist() == ["GLOBAL"]
    assert "?? (MARCADOR)" in origins

    id_row = global_profile.loc[global_profile["Campo"] == "ID"].iloc[0]
    assert id_row["Llave"] == "Sí (global)"

    email_row = global_profile.loc[global_profile["Campo"] == "Email"].iloc[0]
    assert email_row["Cantidad de Nulos"] == 1
    assert email_row["%Espacios"] == 25.0

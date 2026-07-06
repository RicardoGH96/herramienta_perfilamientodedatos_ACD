from __future__ import annotations

import math
import re
from collections.abc import Iterable
from datetime import date, datetime
from decimal import Decimal
from typing import Any

import numpy as np
import pandas as pd

from .config import GLOBAL_SCOPE_LABEL, OUTPUT_COLUMNS


_WHITESPACE_ISSUE = re.compile(r"(^\s)|(\s$)|(\s{2,})")
_DATE_NAME_HINT = re.compile(r"fecha|date|datetime|timestamp|hora", re.IGNORECASE)


def _is_real_null(value: Any) -> bool:
    if value is None:
        return True
    try:
        result = pd.isna(value)
    except (TypeError, ValueError):
        return False
    return bool(result) if isinstance(result, (bool, np.bool_)) else False


def _normalized_token(value: Any) -> str:
    return str(value).strip().upper()


def semantic_null_mask(series: pd.Series, null_tokens: Iterable[str]) -> pd.Series:
    """Identifica nulos y marcadores de ausencia de datos válidos."""
    normalized_tokens = {_normalized_token(token) for token in null_tokens}

    def is_semantic_null(value: Any) -> bool:
        if _is_real_null(value):
            return True
        if isinstance(value, str):
            return _normalized_token(value) in normalized_tokens
        return False

    return series.map(is_semantic_null).astype(bool)


def _display_value(value: Any) -> str:
    """Convierte valores a texto estable para mostrar, medir longitud y exportar."""
    if _is_real_null(value):
        return ""
    if isinstance(value, pd.Timestamp):
        return value.isoformat(sep=" ")
    if isinstance(value, datetime):
        return value.isoformat(sep=" ")
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, (float, np.floating)) and math.isfinite(float(value)):
        if float(value).is_integer():
            return str(int(value))
        return format(float(value), ".15g")
    return str(value)


def _structural_pattern(value: Any) -> str:
    """Obtiene un patrón estructural compacto, por ejemplo L{1}-D{3}."""
    if isinstance(value, (datetime, date, pd.Timestamp)):
        return "FECHA"
    if isinstance(value, (int, np.integer)) and not isinstance(value, bool):
        return "NUM_ENTERO"
    if isinstance(value, (float, np.floating, Decimal)) and not isinstance(value, bool):
        text = _display_value(value)
        decimals = len(text.partition(".")[2]) if "." in text else 0
        return f"NUM_DECIMAL({decimals})" if decimals else "NUM_ENTERO"

    text = _display_value(value)
    if not text:
        return "VACIO"

    tokens: list[str] = []
    for char in text:
        if char.isdigit():
            tokens.append("D")
        elif char.isalpha():
            tokens.append("L")
        elif char.isspace():
            tokens.append("S")
        else:
            tokens.append(char)

    compressed: list[str] = []
    index = 0
    while index < len(tokens):
        token = tokens[index]
        if token in {"D", "L", "S"}:
            end = index + 1
            while end < len(tokens) and tokens[end] == token:
                end += 1
            count = end - index
            compressed.append(f"{token}{{{count}}}")
            index = end
        else:
            compressed.append(token)
            index += 1
    return "".join(compressed)


def _safe_unique_count(series: pd.Series) -> int:
    """Cuenta distintos incluso si se reciben tipos mixtos o valores no hashables."""
    try:
        return int(series.nunique(dropna=True))
    except TypeError:
        canonical = series.map(lambda value: (type(value).__name__, repr(value)))
        return int(canonical.nunique(dropna=True))


def _safe_min_max(series: pd.Series, column_name: str) -> tuple[str, str]:
    """Calcula mínimos y máximos según naturaleza numérica, fecha o texto."""
    if series.empty:
        return "", ""

    if pd.api.types.is_datetime64_any_dtype(series):
        parsed = pd.to_datetime(series, errors="coerce").dropna()
        if not parsed.empty:
            return _display_value(parsed.min()), _display_value(parsed.max())

    numeric = pd.to_numeric(series, errors="coerce")
    if numeric.notna().all():
        return _display_value(numeric.min()), _display_value(numeric.max())

    if _DATE_NAME_HINT.search(column_name):
        parsed_dates = pd.to_datetime(series, errors="coerce")
        if parsed_dates.notna().all():
            return _display_value(parsed_dates.min()), _display_value(parsed_dates.max())

    text_values = series.map(_display_value)
    if text_values.empty:
        return "", ""
    return min(text_values, key=str.casefold), max(text_values, key=str.casefold)


def _space_issue_percentage(series: pd.Series, total_rows: int) -> float:
    if total_rows == 0:
        return 0.0

    def has_issue(value: Any) -> bool:
        if not isinstance(value, str):
            return False
        return bool(_WHITESPACE_ISSUE.search(value)) or (bool(value) and not value.strip())

    return round(float(series.map(has_issue).sum()) / total_rows * 100, 2)


def _origin_label(value: Any, null_tokens: Iterable[str]) -> str:
    """Mantiene visibles los valores de origen anómalos para análisis de causa raíz."""
    if _is_real_null(value):
        return "(NULO REAL)"
    text = str(value)
    if not text.strip():
        return "(VACÍO)"
    normalized_tokens = {_normalized_token(token) for token in null_tokens if token}
    if _normalized_token(text) in normalized_tokens:
        return f"{text.strip()} (MARCADOR)"
    return text.strip()


def profile_dataframe(
    dataframe: pd.DataFrame,
    *,
    table_name: str,
    system_origin: str,
    null_tokens: Iterable[str],
    key_scope: str,
) -> pd.DataFrame:
    """Genera una fila de perfilamiento por cada campo del DataFrame."""
    total_rows = int(len(dataframe))
    records: list[dict[str, Any]] = []

    for column_name in dataframe.columns:
        series = dataframe[column_name]
        null_mask = semantic_null_mask(series, null_tokens)
        non_null = series.loc[~null_mask]
        non_null_count = int(len(non_null))
        null_count = int(null_mask.sum())
        unique_count = _safe_unique_count(non_null)
        unique_percentage = (
            round(unique_count / non_null_count * 100, 2) if non_null_count else 0.0
        )

        display_values = non_null.map(_display_value)
        lengths = display_values.map(len)
        min_length = int(lengths.min()) if not lengths.empty else None
        max_length = int(lengths.max()) if not lengths.empty else None
        minimum, maximum = _safe_min_max(non_null, str(column_name))
        format_count = int(non_null.map(_structural_pattern).nunique()) if non_null_count else 0
        is_candidate_key = total_rows > 0 and null_count == 0 and unique_count == total_rows

        records.append(
            {
                "SistemaOrigen": system_origin,
                "Tabla": table_name,
                "Campo": str(column_name),
                "Cantidad de Registros": total_rows,
                "Cantidad Valores Únicos": unique_count,
                "% Valores únicos": unique_percentage,
                "Valor Mínimo": minimum,
                "Valor Máximo": maximum,
                "Cantidad de Nulos": null_count,
                "%Nulos": round(null_count / total_rows * 100, 2) if total_rows else 0.0,
                "Longitud Mínima": min_length,
                "Longitud Máxima": max_length,
                "Cantidad Formatos": format_count,
                "Llave": f"Sí ({key_scope})" if is_candidate_key else "No",
                "%Espacios": _space_issue_percentage(series, total_rows),
            }
        )

    return pd.DataFrame.from_records(records, columns=OUTPUT_COLUMNS)


def build_profiles(
    dataframe: pd.DataFrame,
    *,
    table_name: str,
    segment_column: str,
    null_tokens: Iterable[str],
) -> tuple[pd.DataFrame, pd.DataFrame, list[str]]:
    """Construye perfil global y perfil segmentado por sistema de origen."""
    if segment_column not in dataframe.columns:
        raise KeyError(f"No existe la columna de segmentación: {segment_column}")

    global_profile = profile_dataframe(
        dataframe,
        table_name=table_name,
        system_origin=GLOBAL_SCOPE_LABEL,
        null_tokens=null_tokens,
        key_scope="global",
    )

    labels = dataframe[segment_column].map(
        lambda value: _origin_label(value, null_tokens)
    )
    segmented_frames: list[pd.DataFrame] = []
    detected_origins: list[str] = []

    for origin in sorted(labels.unique().tolist(), key=str.casefold):
        group = dataframe.loc[labels == origin].reset_index(drop=True)
        detected_origins.append(origin)
        segmented_frames.append(
            profile_dataframe(
                group,
                table_name=table_name,
                system_origin=origin,
                null_tokens=null_tokens,
                key_scope="segmento",
            )
        )

    segmented_profile = (
        pd.concat(segmented_frames, ignore_index=True)
        if segmented_frames
        else pd.DataFrame(columns=OUTPUT_COLUMNS)
    )
    return global_profile, segmented_profile, detected_origins

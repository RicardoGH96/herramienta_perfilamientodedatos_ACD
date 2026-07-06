from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class DatasetSelection:
    """Selección de origen Excel realizada desde la interfaz."""

    file_path: Path
    sheet_name: str
    table_name: str
    table_reference: str
    is_excel_table: bool


@dataclass(frozen=True, slots=True)
class ProfileExecution:
    """Metadatos básicos de una ejecución de perfilamiento."""

    source_file: str
    sheet_name: str
    table_name: str
    table_reference: str
    segment_column: str
    row_count: int
    column_count: int
    origin_count: int
    executed_at: str
    elapsed_seconds: float

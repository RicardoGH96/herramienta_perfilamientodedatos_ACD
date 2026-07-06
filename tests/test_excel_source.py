from __future__ import annotations

from pathlib import Path

from openpyxl import Workbook
from openpyxl.worksheet.table import Table, TableStyleInfo

from src.excel_source import list_tables, read_selection
from src.models import DatasetSelection


def test_detects_excel_table_and_reads_data(tmp_path: Path) -> None:
    file_path = tmp_path / "demo.xlsx"
    workbook = Workbook()
    worksheet = workbook.active
    worksheet.title = "Data"
    worksheet.append(["ID", "Sistema_Origen"])
    worksheet.append([1, "WEB"])
    worksheet.append([2, "ERP"])
    table = Table(displayName="tbl_demo", ref="A1:B3")
    table.tableStyleInfo = TableStyleInfo(name="TableStyleMedium2")
    worksheet.add_table(table)
    workbook.save(file_path)

    tables = list_tables(file_path, "Data")
    assert len(tables) == 1
    assert tables[0].name == "tbl_demo"

    selection = DatasetSelection(
        file_path=file_path,
        sheet_name="Data",
        table_name=tables[0].name,
        table_reference=tables[0].reference,
        is_excel_table=True,
    )
    dataframe = read_selection(selection)
    assert dataframe.shape == (2, 2)
    assert dataframe["Sistema_Origen"].tolist() == ["WEB", "ERP"]

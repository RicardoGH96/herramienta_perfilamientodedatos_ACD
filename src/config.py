from __future__ import annotations

from pathlib import Path

APP_TITLE = "Herramienta de Perfilamiento y Análisis de Calidad de Datos"
APP_AUTHOR = "Ricardo García Hernández"
COMPANY_NAME = "RetailTech S.A."
DATA_DIRECTORY = Path(__file__).resolve().parent.parent / "perfilamiento"
SUPPORTED_EXCEL_EXTENSIONS = {".xlsx", ".xlsm"}

OUTPUT_COLUMNS = [
    "SistemaOrigen",
    "Tabla",
    "Campo",
    "Cantidad de Registros",
    "Cantidad Valores Únicos",
    "% Valores únicos",
    "Valor Mínimo",
    "Valor Máximo",
    "Cantidad de Nulos",
    "%Nulos",
    "Longitud Mínima",
    "Longitud Máxima",
    "Cantidad Formatos",
    "Llave",
    "%Espacios",
]

DEFAULT_NULL_TOKENS = (
    "",
    "NAN",
    "NULL",
    "NONE",
    "N/A",
    "NA",
    "S/D",
    "SIN DATO",
    "SIN INFORMACION",
    "SIN INFORMACIÓN",
    "??",
    "?",
)

GLOBAL_SCOPE_LABEL = "GLOBAL"
PROFILE_GLOBAL_SHEET = "Perfil_ACD_Global"
PROFILE_ORIGIN_SHEET = "Perfil_ACD_Origen"
EXECUTION_SHEET = "Perfil_ACD_Info"

from __future__ import annotations

import time
from datetime import datetime
from pathlib import Path

import pandas as pd
import streamlit as st

from src.config import (
    APP_AUTHOR,
    COMPANY_NAME,
    APP_TITLE,
    DATA_DIRECTORY,
    DEFAULT_NULL_TOKENS,
)
from src.excel_source import list_excel_files, list_sheet_names, list_tables, read_selection
from src.exporter import build_profiled_workbook
from src.models import DatasetSelection, ProfileExecution
from src.profiler import build_profiles


st.set_page_config(
    page_title=APP_TITLE,
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
    <style>
      .block-container {padding-top: 1.4rem; padding-bottom: 2rem; max-width: 1500px;}
      h1, h2, h3 {letter-spacing: -0.02em;}
      [data-testid="stMetric"] {
        background: #ffffff;
        border: 1px solid #e3e8ef;
        padding: 1rem 1.1rem;
        border-radius: 14px;
        box-shadow: 0 3px 12px rgba(15, 42, 67, 0.05);
      }
      div[data-testid="stForm"] {
        border: 1px solid #dfe6ee;
        border-radius: 16px;
        padding: 1.25rem 1.35rem 0.35rem 1.35rem;
        background: #fbfcfe;
      }
    .app-hero {
        background: linear-gradient(135deg, #0f2f4f 0%, #174f6f 100%);
        padding: 1.4rem 1.7rem;
        border-radius: 16px;
        margin-bottom: 1rem;
        box-shadow: 0 6px 18px rgba(15, 47, 79, 0.14);
      }
      
      .app-hero-title {
            font-size: 1.85rem;
            font-weight: 750;
            color: #ffffff;
      }
      
      .app-hero-subtitle {
        color: #d8e7f0;
        margin-top: .35rem;
        font-size: 1rem;
      }
      
      .app-author {
        margin-top: .75rem;
        color: #8fd3c7;
        font-size: .88rem;
        font-weight: 600;
      }
      
      .app-company {
        color: #ffffff;
        font-size: 1rem;
        font-weight: 700;
        white-space: nowrap;
        padding-top: .25rem;
     }
      .step-row {display:flex; gap:.5rem; flex-wrap:wrap; margin:.2rem 0 1rem 0;}
      .step-chip {background:#eef4f8; color:#234f72; border-radius:999px; padding:.35rem .75rem; font-size:.88rem;}
      .hint-box {background:#f7fafc; border-left:4px solid #2f7c87; padding:.75rem 1rem; border-radius:8px; color:#334155;}
      .small-note {color:#64748b; font-size:.88rem;}
      .stDownloadButton button, .stButton button {border-radius:10px; font-weight:650;}
      

    div[data-baseweb="tab-list"] {
        gap: 8px;
        border-bottom: 1px solid #dbe3ec;
    }

    /* Pestañas sin seleccionar */
    button[data-baseweb="tab"] {
        background-color: #f3f6f9;
        color: #334e68;
        border-radius: 8px 8px 0 0;
        padding: 10px 18px;
        border: none;
    }

    /* Pestaña seleccionada */
    button[data-baseweb="tab"][aria-selected="true"] {
        background-color: #123B63;
        color: #ffffff;
        border-bottom: 3px solid #2AA5A5;
    }

    /* Asegura que el texto también cambie */
    button[data-baseweb="tab"][aria-selected="true"] p {
        color: #ffffff;
        font-weight: 600;
    }

    /* Efecto al pasar el mouse */
    button[data-baseweb="tab"]:hover {
        background-color: #dfe9f2;
        color: #123B63;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    f"""
<div class="app-hero">
<div class="app-hero-top">
<div>
<div class="app-hero-title">{APP_TITLE}</div>
<div class="app-author">Desarrollado por {APP_AUTHOR}</div>
</div>
<div class="app-company">{COMPANY_NAME}</div>
</div>
</div>
""",
    unsafe_allow_html=True,
)


def initialize_state() -> None:
    defaults = {
        "global_profile": None,
        "segmented_profile": None,
        "execution": None,
        "selected_file": None,
        "detected_origins": [],
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


initialize_state()

source = st.radio(
    "Escoge la fuente a perfilar",
    options=["Excel", "SQL"],
    horizontal=True,
    help="Opciones de feuntes de datos",
)

if source.startswith("SQL"):
    st.info(
        "Próximamente, perfilado de fuente SQL"
        " por Ricardo García Hernández"
    )
    st.stop()

files = list_excel_files(DATA_DIRECTORY)
if not files:
    st.error(
        f"No hay archivos Excel en la carpeta `{DATA_DIRECTORY}`. "
        "Copia allí un archivo .xlsx o .xlsm y recarga la aplicación."
    )
    st.stop()

with st.form("profile_configuration", clear_on_submit=False):
    st.subheader("Configurar perfilamiento")
    file_names = [path.name for path in files]
    selected_file_name = st.selectbox(
        "Archivo Excel",
        file_names,
        help=f"El programa sólo busca archivos en la ruta: {DATA_DIRECTORY}",
    )
    selected_file = next(path for path in files if path.name == selected_file_name)

    sheet_names = list_sheet_names(selected_file)
    default_sheet_index = sheet_names.index("Data") if "Data" in sheet_names else 0
    selected_sheet = st.selectbox(
        "Hoja",
        sheet_names,
        index=default_sheet_index,
        help="Selecciona la hoja que contiene la tabla o rango de datos.",
    )

    tables = list_tables(selected_file, selected_sheet)
    if tables:
        selected_table = st.selectbox(
            "Tabla",
            tables,
            format_func=lambda item: item.label,
            help="Se priorizan las tablas de Excel. De no existir, toma el rango detectado con datos.",
        )
        if not selected_table.is_excel_table:
            st.warning(
                "No se encontró una tabla de Excel en esta hoja. Se usará el rango detectado. "
            )
    else:
        selected_table = None
        st.error("La hoja seleccionada no contiene datos.")

    dataframe_preview = None
    segment_column = None
    if selected_table is not None:
        preview_selection = DatasetSelection(
            file_path=selected_file,
            sheet_name=selected_sheet,
            table_name=selected_table.name,
            table_reference=selected_table.reference,
            is_excel_table=selected_table.is_excel_table,
        )
        try:
            dataframe_preview = read_selection(preview_selection)
            columns = dataframe_preview.columns.tolist()
            preferred = next(
                (
                    column
                    for column in columns
                    if str(column).replace("_", "").casefold() == "sistemaorigen"
                ),
                columns[0],
            )
            segment_column = st.selectbox(
                "Segmentar por",
                columns,
                index=columns.index(preferred),
                help="El perfil global analiza toda la tabla; el perfil segmentado repite las métricas por este campo.",
            )
        except Exception as exc:  # interfaz: mensaje claro, detalle fuera de la vista principal
            st.error(f"No se pudo leer la selección: {exc}")

    with st.expander("Opciones avanzadas", expanded=False):
        null_tokens_text = st.text_area(
            "Marcadores considerados como datos faltantes.",
            value="\n".join(DEFAULT_NULL_TOKENS),
            height=180,
            help="Un marcador por línea. Se conservan los valores originales; solo cambia su conteo en el perfilamiento.",
        )
        st.caption(
            "Ejemplos: `NaN`, `NULL`, `S/D` y `??`. En la segmentación, estos valores permanecen visibles para facilitar la trazabilidad."
        )

    submitted = st.form_submit_button(
        "Ejecutar perfilamiento",
        type="primary",
        use_container_width=True,
        disabled=selected_table is None or dataframe_preview is None or segment_column is None,
    )

if submitted:
    null_tokens = tuple(line.strip() for line in null_tokens_text.splitlines())
    selection = DatasetSelection(
        file_path=selected_file,
        sheet_name=selected_sheet,
        table_name=selected_table.name,
        table_reference=selected_table.reference,
        is_excel_table=selected_table.is_excel_table,
    )

    started = time.perf_counter()
    try:
        with st.spinner("Analizando estructura, nulos, formatos, longitudes, unicidad y espacios..."):
            dataframe = read_selection(selection)
            global_profile, segmented_profile, detected_origins = build_profiles(
                dataframe,
                table_name=selection.table_name,
                segment_column=segment_column,
                null_tokens=null_tokens,
            )
        elapsed = round(time.perf_counter() - started, 3)

        execution = ProfileExecution(
            source_file=selection.file_path.name,
            sheet_name=selection.sheet_name,
            table_name=selection.table_name,
            table_reference=selection.table_reference,
            segment_column=segment_column,
            row_count=len(dataframe),
            column_count=len(dataframe.columns),
            origin_count=len(detected_origins),
            executed_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            elapsed_seconds=elapsed,
        )

        st.session_state.global_profile = global_profile
        st.session_state.segmented_profile = segmented_profile
        st.session_state.execution = execution
        st.session_state.selected_file = selection.file_path
        st.session_state.detected_origins = detected_origins
        st.success("Perfilamiento ejecutado correctamente.")
    except Exception as exc:
        st.error(f"No se pudo completar el perfilamiento: {exc}")

if st.session_state.global_profile is not None:
    execution: ProfileExecution = st.session_state.execution
    global_profile: pd.DataFrame = st.session_state.global_profile
    segmented_profile: pd.DataFrame = st.session_state.segmented_profile

    st.divider()
    st.subheader("Resumen de la ejecución")
    metric_columns = st.columns(5)
    metric_columns[0].metric("Registros", f"{execution.row_count:,}")
    metric_columns[1].metric("Campos", execution.column_count)
    metric_columns[2].metric("Sistemas de origen válidos:", execution.origin_count)
    metric_columns[3].metric("Tabla / rango", execution.table_name)
    metric_columns[4].metric("Tiempo", f"{execution.elapsed_seconds:.3f} s")

    st.markdown(    
        """
        <div class="hint-box">
          <strong>Tener en cuenta:</strong> cada fila representa un campo perfilado. En la vista global,
          <code>SistemaOrigen</code> toma el valor <code>GLOBAL</code>. En la vista segmentada,
          las mismas métricas se recalculan para cada valor encontrado en la columna de origen.
        </div>
        """,
        unsafe_allow_html=True,
    )

    global_tab, segmented_tab, export_tab, definitions_tab = st.tabs(
        [
            "Perfilamiento General",
            "Por sistema de origen",
            "Exportar",
            "Definiciones",
        ]
    )

    table_config = {
        "% Valores únicos": st.column_config.NumberColumn(format="%.2f%%"),
        "%Nulos": st.column_config.NumberColumn(format="%.2f%%"),
        "%Espacios": st.column_config.NumberColumn(format="%.2f%%"),
        "Cantidad de Registros": st.column_config.NumberColumn(format="%d"),
        "Cantidad Valores Únicos": st.column_config.NumberColumn(format="%d"),
        "Cantidad de Nulos": st.column_config.NumberColumn(format="%d"),
        "Longitud Mínima": st.column_config.NumberColumn(format="%d"),
        "Longitud Máxima": st.column_config.NumberColumn(format="%d"),
        "Cantidad Formatos": st.column_config.NumberColumn(format="%d"),
    }

    with global_tab:
        search_global = st.text_input(
            "Buscar campo",
            placeholder="Ejemplo: RUC, Email_Contacto, Monto_USD",
            key="search_global",
        )
        filtered_global = global_profile
        if search_global:
            filtered_global = global_profile.loc[
                global_profile["Campo"].str.contains(search_global, case=False, na=False)
            ]
        st.dataframe(
            filtered_global,
            use_container_width=True,
            hide_index=True,
            height=min(620, 90 + 36 * len(filtered_global)),
            column_config=table_config,
        )

    with segmented_tab:
        origin_options = st.session_state.detected_origins
        selected_origins = st.multiselect(
            "Filtrar sistemas de origen",
            options=origin_options,
            default=origin_options,
        )
        search_segment = st.text_input(
            "Buscar campo",
            placeholder="Ejemplo: Sistema_Origen o ID_Cliente",
            key="search_segment",
        )
        filtered_segmented = segmented_profile.loc[
            segmented_profile["SistemaOrigen"].isin(selected_origins)
        ]
        if search_segment:
            filtered_segmented = filtered_segmented.loc[
                filtered_segmented["Campo"].str.contains(search_segment, case=False, na=False)
            ]
        st.dataframe(
            filtered_segmented,
            use_container_width=True,
            hide_index=True,
            height=620,
            column_config=table_config,
        )

    with export_tab:
        st.markdown(
            "La descarga conserva el libro original y agrega las hojas "
            "`Perfil_ACD_Global`, `Perfil_ACD_Origen` y `Perfil_ACD_Info`."
        )
        try:
            output_bytes = build_profiled_workbook(
                st.session_state.selected_file,
                global_profile,
                segmented_profile,
                execution,
            )
            output_name = f"{Path(execution.source_file).stem}_PERFILADO.xlsx"
            st.download_button(
                "Descargar copia del Excel con resultados",
                data=output_bytes,
                file_name=output_name,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                type="primary",
                use_container_width=True,
            )
        except Exception as exc:
            st.error(f"No fue posible preparar la descarga: {exc}")

    with definitions_tab:
        definitions = pd.DataFrame(
            [
                ("Cantidad de Registros", "Total de registros TODOS o por SISTEMA ORIGEN."),
                ("Cantidad Valores Únicos", "Valores distintos, excluyendo nulos físicos."),
                ("% Valores únicos", "Valores distintos (no nulos) / cant. registros (no nulos)."),
                ("Valor Mínimo / Máximo", "Valores mínimo y máximo para toda la tabla o por SISTEMA ORIGEN"),
                ("Cantidad de Nulos", "Cant. total de nulos"),
                ("Longitud Mínima / Máxima", "Cantidad de caracteres min y max para cada campo."),
                ("Cantidad Formatos", "Cantidad de patrones estructurales diferentes."),
                ("Llave Candidata", "Candidata técnica: 100% única y sin nulos dentro del alcance evaluado."),
                ("%Espacios", "Registros con espacios iniciales, finales o compuestos solo por espacios."),
            ],
            columns=["Métrica", "Definición"],
        )
        st.dataframe(definitions, use_container_width=True, hide_index=True)
    

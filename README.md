# Perfilador de Calidad de Datos

Aplicación UX en **Python + Streamlit** para perfilar una Tabla de Excel o, como respaldo, el rango real con datos. Genera dos tablas de resultados:

- `Perfilamiento_Global`: una fila por campo para toda la tabla.
- `Perfilamiento_Origen`: una fila por campo y por cada valor de `Sistema_Origen`.

## 1. Requisitos

- Python 3.11 o superior.
- Windows, macOS o Linux.

## 2. Instalación

Abre una terminal dentro de esta carpeta y ejecuta:

```bash
python -m venv .venv
```

En Windows:

```bash
.venv\Scripts\activate
```

En macOS/Linux:

```bash
source .venv/bin/activate
```

Instala dependencias:

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## 3. Preparar el Excel

1. Coloca el archivo `.xlsx` o `.xlsm` en la carpeta `perfilamiento`.
2. Preferentemente, convierte el rango de datos en una **Tabla de Excel** con `Ctrl + T`.
3. Asegúrate de que la tabla tenga encabezados únicos.
4. La aplicación también ofrece un modo de respaldo si no encuentra una Tabla de Excel.

## 4. Ejecutar

En Windows puedes hacer doble clic en `run_app.bat`.

También puedes ejecutar:

```bash
python -m streamlit run app.py
```

Streamlit abrirá la aplicación en el navegador.

## 5. Flujo de uso

1. Selecciona `Excel` como fuente.
2. Elige el archivo, la hoja y la tabla detectada.
3. Selecciona la columna de segmentación; por defecto se propone `Sistema_Origen`.
4. Revisa los marcadores tratados como nulos semánticos.
5. Presiona **Ejecutar perfilamiento**.
6. Revisa las pestañas global y segmentada.
7. Descarga una copia del Excel con las hojas nuevas.

## 6. Columnas generadas

- SistemaOrigen
- Tabla
- Campo
- Cantidad de Registros
- Cantidad Valores Únicos
- % Valores únicos
- Valor Mínimo
- Valor Máximo
- Cantidad de Nulos
- %Nulos
- Longitud Mínima
- Longitud Máxima
- Cantidad Formatos
- Llave
- %Espacios

## 7. Criterios importantes

- `% Valores únicos` = valores distintos no nulos / registros no nulos.
- Los marcadores como `NaN`, `NULL`, `S/D` o `??` pueden tratarse como nulos semánticos.
- En la segmentación, los valores anómalos de origen siguen visibles, por ejemplo `?? (MARCADOR)`.
- `Llave` significa **candidata técnica**, no una confirmación funcional: requiere validación del Data Owner.
- `%Espacios` identifica espacios iniciales, finales, múltiples o valores compuestos únicamente por espacios.
- `Cantidad Formatos` cuenta patrones estructurales distintos, por ejemplo `L{1}-D{3}`.

## 8. Exportación

La descarga conserva las hojas del libro fuente y agrega o reemplaza:

- `Perfilamiento_Global`
- `Perfilamiento_Origen`
- `Perfilamiento_Info`

El archivo original ubicado en `perfilamiento` no se modifica.

## 9. Evolución SQL

La opción SQL aparece en la interfaz como **Próximamente** para comunicar la escalabilidad de la iniciativa, pero no contiene conexión ni credenciales en esta versión del examen.

## 10. Pruebas

```bash
pytest -q
```

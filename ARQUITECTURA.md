# Arquitectura de la solución

```text
Interfaz Streamlit
        ↓
Selección Excel / SQL (roadmap)
        ↓
Detección de archivo, hoja y Tabla de Excel
        ↓
Lectura controlada del rango con openpyxl
        ↓
Motor de perfilamiento con pandas
        ├── Perfilamiento global
        └── Perfilamiento por Sistema_Origen
        ↓
Visualización interactiva
        ↓
Copia del Excel con resultados
```

## Separación de responsabilidades

- `app.py`: experiencia de usuario, navegación y presentación.
- `src/excel_source.py`: acceso, detección y lectura del origen Excel.
- `src/profiler.py`: reglas técnicas de perfilamiento.
- `src/exporter.py`: generación de la copia del libro con resultados.
- `src/models.py`: estructuras de datos de la ejecución.
- `src/config.py`: constantes y configuración centralizada.

## Decisiones de Gobierno de Datos

- Se conserva el archivo fuente sin modificaciones.
- Los nulos físicos y los marcadores semánticos se distinguen mediante configuración.
- Los valores anómalos de `Sistema_Origen` permanecen visibles en el análisis segmentado.
- La inferencia de llave se presenta como candidata técnica y no como decisión de negocio.
- La segmentación permite identificar el sistema donde se concentra el deterioro de calidad.

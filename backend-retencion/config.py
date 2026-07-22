import os
from pathlib import Path

# SRI
SRI_RUC = "1805010053001"
SRI_PASSWORD = "TU_CLAVE_SRI"

# Rutas
DOWNLOADS_PATH = Path(r"C:\Users\Usuario\Downloads")
PDF_STORAGE_BASE = Path(r"C:\Users\Usuario\Desktop\DIARIO\FACTURAS")
EXCEL_PATH = Path(r"C:\Users\Usuario\Desktop\DIARIO\retenciones.xlsx")

# Monica 11 - nombre exacto de la ventana principal
MONICA_WINDOW_TITLE = "MODULOS"

# Retenciones esperadas (porcentajes correctos)
EXPECTED_RENTA_PCT = 2.000
EXPECTED_IVA_PCT = 30.000
TOLERANCE = 0.01  # diferencia aceptable para comparación de montos
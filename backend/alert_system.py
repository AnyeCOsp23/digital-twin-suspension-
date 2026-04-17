import json
import numpy as np
from scipy.signal import find_peaks
from datetime import datetime

STABILITY_THRESHOLD = 0.05   # meters
ALERT_TIME_LIMIT    = 3.0    # seconds
BACHE_START_TIME    = 1.0    # second when bump occurs

def check_maintenance_alert(m, b, k):
    """
    Calcula el tiempo de estabilización (aprox. al 2%) dependiendo del tipo de amortiguamiento.
    Se activa una alerta de mantenimiento si el tiempo supera los 3 segundos.
    """
    if b == 0:
        return True, float('inf')
        
    wn = np.sqrt(k / m)
    zeta = b / (2 * m * wn)
    
    if zeta < 0.95:
        # Sistema Subamortiguado: Ts ≈ 4 / (zeta * wn) = 8 * m / b
        stab_time = round(8.0 * m / b, 2)
    elif zeta <= 1.05:
        # Sistema Críticamente Amortiguado o cercano
        stab_time = round(5.83 / wn, 2)
    else:
        # Sistema Sobreamortiguado: dominado por la raíz más cercana a cero
        s1 = -zeta * wn + wn * np.sqrt(zeta**2 - 1)
        stab_time = round(-4.0 / s1, 2) if s1 != 0 else float('inf')
        
    alert = stab_time > 3.0
    return alert, stab_time

def export_peaks_json(t, x, m, b, k, filepath="picos_vibracion.json"):
    """
    Detects vibration peaks and exports them to a structured JSON file.
    Returns the number of peaks found.
    """
    # Encontrar picos reales (usamos valor absoluto para picos positivos y negativos)
    peaks_idx, properties = find_peaks(np.abs(x), height=0.01, prominence=0.005)

    peaks_data = [
        {
            "timestamp":  round(float(t[i]), 4),
            "amplitud":   round(float(x[i]), 4),
            "peak_index": int(i)
        }
        for i in peaks_idx
    ]

    output = {
        "version_del_modelo":  "1.0.0",
        "fecha_exportacion":   datetime.now().isoformat(),
        "parametros": {
            "masa_kg":       m,
            "amortiguador_b": b,
            "resorte_k":     k
        },
        "umbral_de_alerta_s":  ALERT_TIME_LIMIT,
        "total_picos":         len(peaks_data),
        "picos_detectados":    peaks_data
    }

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    return len(peaks_data)
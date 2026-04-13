"""
utils/predictor.py
------------------
Funciones de predicción reutilizadas por todas las páginas.
"""

import numpy as np
import pandas as pd
import pickle
import os

_ARTIFACTS = None

def load_artifacts():
    global _ARTIFACTS
    if _ARTIFACTS is None:
        path = os.path.join(os.path.dirname(__file__), '..', 'models', 'artifacts.pkl')
        with open(path, 'rb') as f:
            _ARTIFACTS = pickle.load(f)
    return _ARTIFACTS


def predict(barrio: str, room_type: str, accommodates: int,
            amenity_count: int, barrios_df: pd.DataFrame) -> dict:
    """
    Devuelve precio estimado (ARS/noche), probabilidad alta ocupación,
    ocupación estimada (noches/año) y revenue anual estimado.
    """
    art = load_artifacts()

    # Variables externas del barrio
    row_b = barrios_df[barrios_df['barrio'] == barrio]
    if row_b.empty:
        row_b = barrios_df.mean(numeric_only=True)
    else:
        row_b = row_b.iloc[0]

    dist_obelisco = row_b['dist_obelisco']
    crimes        = row_b['crimes']
    subte         = row_b['subte']
    density       = row_b['density']

    # Construir fila de features
    X_raw = pd.DataFrame([{
        'accommodates':  accommodates,
        'amenity_count': amenity_count,
        'dist_obelisco': dist_obelisco,
        'crimes':        crimes,
        'subte':         subte,
        'density':       density,
        'barrio':        barrio,
        'room_type':     room_type,
    }])

    VARS_NUM = art['vars_num']
    VARS_CAT = art['vars_cat']

    # Encode categóricas
    enc = art['encoder']
    known_barrios    = art['cat_categories']['barrio']
    known_room_types = art['cat_categories']['room_type']

    if barrio not in known_barrios:
        X_raw['barrio'] = known_barrios[0]
    if room_type not in known_room_types:
        X_raw['room_type'] = known_room_types[0]

    X_raw[VARS_CAT] = enc.transform(X_raw[VARS_CAT])
    X = X_raw[VARS_NUM + VARS_CAT].astype(float)

    # Precio
    log_p = art['model_price'].predict(X)[0]
    precio = np.exp(log_p)

    # Ocupación
    X_sc = art['scaler'].transform(X)
    prob_alta = art['model_ocup'].predict_proba(X_sc)[0][1]

    mediana = art['mediana_ocup']
    # Estimación continua de noches: interpolamos entre [0, 255]
    # prob_alta = 0.5 → mediana, lineal en ambos extremos
    if prob_alta >= 0.5:
        noches = mediana + (prob_alta - 0.5) * 2 * (255 - mediana)
    else:
        noches = prob_alta * 2 * mediana

    noches = float(np.clip(noches, 0, 255))
    ocup_pct = noches / 365 * 100

    revenue_anual  = precio * noches
    revenue_mensual = revenue_anual / 12

    return {
        'precio':           round(precio, 0),
        'noches':           round(noches, 1),
        'ocup_pct':         round(ocup_pct, 1),
        'prob_alta_ocup':   round(prob_alta * 100, 1),
        'revenue_anual':    round(revenue_anual, 0),
        'revenue_mensual':  round(revenue_mensual, 0),
        'precio_medio_barrio': round(float(row_b['precio_medio_barrio']), 0),
        'ocup_media_barrio':   round(float(row_b['ocup_media_barrio']), 1),
    }


def get_mejoras(barrio: str, room_type: str, accommodates: int,
                amenity_count: int, barrios_df: pd.DataFrame) -> list:
    """
    Simula mejoras incrementales en cada variable accionable
    y devuelve el impacto en precio y revenue.
    """
    base = predict(barrio, room_type, accommodates, amenity_count, barrios_df)
    mejoras = []

    # +5 amenities
    m1 = predict(barrio, room_type, accommodates, amenity_count + 5, barrios_df)
    diff_precio   = m1['precio'] - base['precio']
    diff_revenue  = m1['revenue_anual'] - base['revenue_anual']
    if diff_precio > 0:
        mejoras.append({
            'accion': '➕ Añadir 5 amenities',
            'descripcion': 'WiFi de alta velocidad, cafetera, secadora, AC, TV smart...',
            'impacto_precio': diff_precio,
            'impacto_revenue': diff_revenue,
            'prioridad': 'Alta' if diff_precio > 1000 else 'Media',
        })

    # +1 persona de capacidad
    if accommodates < 8:
        m2 = predict(barrio, room_type, accommodates + 1, amenity_count, barrios_df)
        diff_p2 = m2['precio'] - base['precio']
        diff_r2 = m2['revenue_anual'] - base['revenue_anual']
        if diff_p2 > 0:
            mejoras.append({
                'accion': '🛏️ Aumentar capacidad en 1 huésped',
                'descripcion': 'Añadir una cama extra o sofá cama aumenta el precio de mercado.',
                'impacto_precio': diff_p2,
                'impacto_revenue': diff_r2,
                'prioridad': 'Alta' if diff_p2 > 2000 else 'Media',
            })

    # Instant bookable (simulado: +8% ocupación → +8% revenue)
    mejoras.append({
        'accion': '⚡ Activar reserva instantánea',
        'descripcion': 'Los listings con reserva instantánea tienen ~15% más conversión en Airbnb.',
        'impacto_precio': 0,
        'impacto_revenue': round(base['revenue_anual'] * 0.08, 0),
        'prioridad': 'Alta',
    })

    # Verificar identidad (simulado: +5% revenue)
    mejoras.append({
        'accion': '✅ Verificar identidad como host',
        'descripcion': 'La verificación mejora la confianza del huésped y el posicionamiento en la plataforma.',
        'impacto_precio': 0,
        'impacto_revenue': round(base['revenue_anual'] * 0.05, 0),
        'prioridad': 'Media',
    })

    # Ordenar por impacto revenue
    mejoras.sort(key=lambda x: x['impacto_revenue'], reverse=True)
    return mejoras

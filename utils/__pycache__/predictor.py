"""
utils/predictor.py
------------------
Funciones de predicción usando los modelos entrenados con el notebook real.
Para hosts nuevos: reviews se imputan a 0.
Para hosts existentes: el usuario puede indicar sus métricas.
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


def build_input(params: dict, cat_cols: list, vars_num: list) -> pd.DataFrame:
    """
    Construye el vector de features con get_dummies igual que en el notebook.
    Parámetros no proporcionados se imputan a 0 (host nuevo sin historial).
    """
    row = {v: params.get(v, 0) for v in vars_num}

    # Reconstruir dummies manualmente
    for col in cat_cols:
        row[col] = 0.0

    # Activar la dummy correcta para barrio
    barrio_col = f"barrio_{params.get('barrio', '')}"
    if barrio_col in cat_cols:
        row[barrio_col] = 1.0

    # Activar la dummy correcta para room_type
    rt_col = f"room_type_{params.get('room_type', '')}"
    if rt_col in cat_cols:
        row[rt_col] = 1.0

    return pd.DataFrame([row])[vars_num + cat_cols]


def predict(barrio: str, room_type: str, accommodates: int,
            num_amenities: int, barrios_df: pd.DataFrame,
            # Parámetros opcionales para hosts existentes
            bedrooms: int = 1, bathrooms: float = 1.0, beds: int = 1,
            minimum_nights: int = 2, maximum_nights: int = 365,
            review_scores_rating: float = 0, number_of_reviews: int = 0,
            reviews_per_month: float = 0, number_of_reviews_ltm: int = 0,
            review_scores_location: float = 0, review_scores_cleanliness: float = 0,
            review_scores_checkin: float = 0, review_scores_communication: float = 0,
            review_scores_accuracy: float = 0, review_scores_value: float = 0,
            antiguedad_host: float = 0, host_listings_count: int = 1,
            ) -> dict:

    art = load_artifacts()

    # Variables externas del barrio
    row_b = barrios_df[barrios_df['barrio'] == barrio]
    if row_b.empty:
        row_b = barrios_df.mean(numeric_only=True)
    else:
        row_b = row_b.iloc[0]

    params = {
        'accommodates':               accommodates,
        'bedrooms':                   bedrooms,
        'bathrooms':                  bathrooms,
        'beds':                       beds,
        'minimum_nights':             minimum_nights,
        'maximum_nights':             maximum_nights,
        'num_amenities':              num_amenities,
        'antiguedad_host':            antiguedad_host,
        'host_listings_count':        host_listings_count,
        'review_scores_rating':       review_scores_rating,
        'number_of_reviews':          number_of_reviews,
        'reviews_per_month':          reviews_per_month,
        'number_of_reviews_ltm':      number_of_reviews_ltm,
        'review_scores_location':     review_scores_location,
        'review_scores_cleanliness':  review_scores_cleanliness,
        'review_scores_checkin':      review_scores_checkin,
        'review_scores_communication':review_scores_communication,
        'review_scores_accuracy':     review_scores_accuracy,
        'review_scores_value':        review_scores_value,
        'distancia_al_obelisco_m':    float(row_b['dist_obelisco']),
        'density':                    float(row_b['density']),
        'crimes':                     float(row_b['crimes']),
        'subte':                      float(row_b['subte']),
        'top_atracciones_within_1000m': 0,
        'barrio':                     barrio,
        'room_type':                  room_type,
    }

    X = build_input(params, art['cat_cols'], art['vars_num'])

    # Precio
    log_p  = art['model_price'].predict(X)[0]
    precio = float(np.exp(log_p))

    # Ocupación
    X_sc       = art['scaler'].transform(X)
    prob_alta  = float(art['model_ocup'].predict_proba(X_sc)[0][1])
    mediana    = art['mediana_ocup']

    if prob_alta >= 0.5:
        noches = mediana + (prob_alta - 0.5) * 2 * (255 - mediana)
    else:
        noches = prob_alta * 2 * mediana
    noches = float(np.clip(noches, 0, 255))

    revenue_anual   = precio * noches
    revenue_mensual = revenue_anual / 12

    return {
        'precio':              round(precio, 0),
        'noches':              round(noches, 1),
        'ocup_pct':            round(noches / 365 * 100, 1),
        'prob_alta_ocup':      round(prob_alta * 100, 1),
        'revenue_anual':       round(revenue_anual, 0),
        'revenue_mensual':     round(revenue_mensual, 0),
        'precio_medio_barrio': round(float(row_b['precio_medio_barrio']), 0),
        'ocup_media_barrio':   round(float(row_b['ocup_media_barrio']), 1),
    }


def get_mejoras(barrio, room_type, accommodates, num_amenities,
                barrios_df, **kwargs) -> list:
    base    = predict(barrio, room_type, accommodates, num_amenities, barrios_df, **kwargs)
    mejoras = []

    # +5 amenities
    m1 = predict(barrio, room_type, accommodates, num_amenities + 5, barrios_df, **kwargs)
    if m1['precio'] > base['precio']:
        mejoras.append({
            'accion':          '➕ Añadir 5 amenities',
            'descripcion':     'WiFi alta velocidad, cafetera, secadora, AC, TV smart...',
            'impacto_precio':  m1['precio'] - base['precio'],
            'impacto_revenue': m1['revenue_anual'] - base['revenue_anual'],
            'prioridad':       'Alta',
        })

    # +1 capacidad
    if accommodates < 8:
        m2 = predict(barrio, room_type, accommodates + 1, num_amenities, barrios_df, **kwargs)
        if m2['precio'] > base['precio']:
            mejoras.append({
                'accion':          '🛏️ Aumentar capacidad en 1 huésped',
                'descripcion':     'Añadir una cama extra o sofá cama aumenta el precio de mercado.',
                'impacto_precio':  m2['precio'] - base['precio'],
                'impacto_revenue': m2['revenue_anual'] - base['revenue_anual'],
                'prioridad':       'Alta',
            })

    # Reserva instantánea
    mejoras.append({
        'accion':          '⚡ Activar reserva instantánea',
        'descripcion':     'Los listings con reserva instantánea tienen ~15% más conversión.',
        'impacto_precio':  0,
        'impacto_revenue': round(base['revenue_anual'] * 0.08, 0),
        'prioridad':       'Alta',
    })

    # Verificar identidad
    mejoras.append({
        'accion':          '✅ Verificar identidad como host',
        'descripcion':     'Mejora la confianza del huésped y el posicionamiento en la plataforma.',
        'impacto_precio':  0,
        'impacto_revenue': round(base['revenue_anual'] * 0.05, 0),
        'prioridad':       'Media',
    })

    mejoras.sort(key=lambda x: x['impacto_revenue'], reverse=True)
    return mejoras

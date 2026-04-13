"""
pages/3_💡_Mejoras.py
----------------------
Recomendaciones accionables basadas en el impacto de cada variable.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import os, sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from utils.predictor import predict, get_mejoras

st.set_page_config(page_title="Mejoras", page_icon="💡", layout="wide")

@st.cache_data
def load_barrios():
    path = os.path.join(os.path.dirname(__file__), '..', 'data', 'barrios_medias.csv')
    return pd.read_csv(path)

barrios_df = load_barrios()

if 'listing_data' not in st.session_state:
    st.warning("⚠️ Primero rellena los datos en **🏠 Tu Listing**.")
    st.stop()

data = st.session_state['listing_data']

# ── Predicción base ───────────────────────────────────────────────────────────
base = predict(
    barrio=data['barrio'],
    room_type=data['room_type'],
    accommodates=data['accommodates'],
    amenity_count=data['amenity_count'],
    barrios_df=barrios_df,
)
mejoras = get_mejoras(
    barrio=data['barrio'],
    room_type=data['room_type'],
    accommodates=data['accommodates'],
    amenity_count=data['amenity_count'],
    barrios_df=barrios_df,
)

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("# 💡 ¿Cómo mejorar el rendimiento de tu listing?")
st.markdown(f"Basado en tu piso en **{data['barrio']}** — aquí tienes las palancas con mayor impacto real en precio y revenue.")
st.markdown("---")

# ── Revenue base vs potencial ─────────────────────────────────────────────────
revenue_potencial = base['revenue_anual'] + sum(m['impacto_revenue'] for m in mejoras)

col1, col2, col3 = st.columns(3)
col1.metric("Revenue actual estimado", f"${base['revenue_anual']:,.0f} ARS/año")
col2.metric("Revenue potencial (todas las mejoras)", f"${revenue_potencial:,.0f} ARS/año",
            delta=f"+${revenue_potencial - base['revenue_anual']:,.0f}")
col3.metric("Uplift potencial",
            f"+{(revenue_potencial/base['revenue_anual']-1)*100:.0f}%")

st.markdown("---")

# ── Tarjetas de mejoras ───────────────────────────────────────────────────────
st.markdown("### 🎯 Acciones recomendadas por impacto")

for i, m in enumerate(mejoras):
    color = "#FF5A5F" if m['prioridad'] == 'Alta' else "#FF9F40"
    badge = "🔴 Alta prioridad" if m['prioridad'] == 'Alta' else "🟡 Prioridad media"
    
    with st.container():
        col1, col2, col3 = st.columns([3, 1, 1])
        with col1:
            st.markdown(f"""
            <div style='background:white; border-left: 4px solid {color}; 
                        border-radius: 8px; padding: 1rem; 
                        box-shadow: 0 2px 8px rgba(0,0,0,0.06); margin-bottom: 0.5rem;'>
                <div style='font-size: 1.1rem; font-weight: 700;'>{m['accion']}</div>
                <div style='color: #666; font-size: 0.9rem; margin-top: 0.3rem;'>{m['descripcion']}</div>
                <div style='margin-top: 0.5rem;'><span style='background: {color}22; color: {color}; 
                    border-radius: 4px; padding: 2px 8px; font-size: 0.8rem; font-weight: 600;'>
                    {badge}</span></div>
            </div>
            """, unsafe_allow_html=True)
        with col2:
            if m['impacto_precio'] > 0:
                st.metric("Impacto precio/noche", f"+${m['impacto_precio']:,.0f} ARS")
            else:
                st.metric("Impacto precio/noche", "—")
        with col3:
            st.metric("Impacto revenue/año", f"+${m['impacto_revenue']:,.0f} ARS")

st.markdown("---")

# ── Simulador interactivo de amenities ───────────────────────────────────────
st.markdown("### 🔬 Simulador: ¿cuánto vale cada amenity extra?")
st.markdown("Usa el slider para ver cómo cambia tu precio según el número de amenities.")

col1, col2 = st.columns([1, 2])
with col1:
    n_amenities_sim = st.slider(
        "Número de amenities",
        min_value=1, max_value=87,
        value=data['amenity_count'],
        step=1
    )

# Calcular predicciones para rango de amenities
amenities_range = list(range(1, 88, 3))
precios_range = []
for a in amenities_range:
    r = predict(data['barrio'], data['room_type'], data['accommodates'], a, barrios_df)
    precios_range.append(r['precio'])

# Precio actual simulado
r_sim = predict(data['barrio'], data['room_type'], data['accommodates'], n_amenities_sim, barrios_df)

with col2:
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=amenities_range, y=precios_range,
        mode='lines', name='Precio estimado',
        line=dict(color='#FFB3B5', width=2)
    ))
    fig.add_trace(go.Scatter(
        x=[n_amenities_sim], y=[r_sim['precio']],
        mode='markers', name='Tu selección',
        marker=dict(color='#FF5A5F', size=12, symbol='circle')
    ))
    fig.add_vline(x=data['amenity_count'], line_dash="dash",
                  line_color="#888", annotation_text="Actual")
    fig.update_layout(
        height=300,
        xaxis_title="Nº amenities",
        yaxis_title="Precio estimado (ARS/noche)",
        paper_bgcolor='white',
        plot_bgcolor='white',
        margin=dict(l=20, r=20, t=20, b=20),
        yaxis=dict(gridcolor='#f0f0f0'),
        xaxis=dict(gridcolor='#f0f0f0'),
        legend=dict(orientation='h', y=1.1)
    )
    st.plotly_chart(fig, use_container_width=True)

col1.metric("Precio con tu selección", f"${r_sim['precio']:,.0f} ARS/noche",
            delta=f"{r_sim['precio'] - base['precio']:+,.0f} vs tu listing actual")
col1.metric("Revenue anual con tu selección", f"${r_sim['revenue_anual']:,.0f} ARS",
            delta=f"{r_sim['revenue_anual'] - base['revenue_anual']:+,.0f}")

st.markdown("---")

# ── Luna de miel tip ──────────────────────────────────────────────────────────
st.markdown("### 🌙 El período de 'luna de miel' de Airbnb")
st.info("""
**¿Eres un host nuevo?** Airbnb da visibilidad extra a los listings nuevos durante las primeras semanas.
Este período es tu mayor oportunidad para acumular las primeras reseñas que dispararán tu ocupación.

Nuestro modelo demuestra que **el número de reseñas es la variable con mayor correlación con la ocupación** 
(Spearman > 0.8). Sin reseñas, el algoritmo de Airbnb no puede posicionarte correctamente.

**Estrategia recomendada para el período de luna de miel:**
- 📉 Pon el precio un 10–15% por debajo de la media del barrio al principio
- ⚡ Activa la reserva instantánea para maximizar conversión
- ✅ Responde todos los mensajes en menos de 1 hora
- 🧹 Asegúrate de tener un 5.0 en limpieza las primeras 5 reservas
""")

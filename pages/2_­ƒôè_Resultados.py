"""
pages/2_📊_Resultados.py
------------------------
Muestra la predicción de precio, ocupación y revenue.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from utils.predictor import predict

st.set_page_config(page_title="Resultados", page_icon="📊", layout="wide")

@st.cache_data
def load_barrios():
    path = os.path.join(os.path.dirname(__file__), '..', 'data', 'barrios_medias.csv')
    return pd.read_csv(path)

barrios_df = load_barrios()

# ── Check session state ───────────────────────────────────────────────────────
if 'listing_data' not in st.session_state:
    st.warning("⚠️ Primero rellena los datos de tu listing en la página **🏠 Tu Listing**.")
    st.stop()

data = st.session_state['listing_data']

# ── Predicción ────────────────────────────────────────────────────────────────
with st.spinner("Calculando predicción..."):
    result = predict(
        barrio=data['barrio'],
        room_type=data['room_type'],
        accommodates=data['accommodates'],
        amenity_count=data['amenity_count'],
        barrios_df=barrios_df,
    )

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown(f"# 📊 Resultados para tu piso en **{data['barrio']}**")
st.markdown("Basado en los datos reales de los listings activos en Buenos Aires.")
st.markdown("---")

# ── KPIs principales ──────────────────────────────────────────────────────────
st.markdown("### 💰 Estimación de rendimiento")
col1, col2, col3, col4 = st.columns(4)

with col1:
    delta_precio = result['precio'] - result['precio_medio_barrio']
    delta_str = f"+${delta_precio:,.0f}" if delta_precio >= 0 else f"-${abs(delta_precio):,.0f}"
    st.metric(
        label="💵 Precio estimado / noche",
        value=f"${result['precio']:,.0f} ARS",
        delta=f"{delta_str} vs media del barrio",
        delta_color="normal"
    )

with col2:
    delta_ocup = result['noches'] - result['ocup_media_barrio']
    st.metric(
        label="📅 Noches reservadas / año",
        value=f"{result['noches']:.0f} noches",
        delta=f"{delta_ocup:+.0f} vs media del barrio",
        delta_color="normal"
    )

with col3:
    st.metric(
        label="📈 Revenue estimado / mes",
        value=f"${result['revenue_mensual']:,.0f} ARS",
    )

with col4:
    st.metric(
        label="🏆 Revenue estimado / año",
        value=f"${result['revenue_anual']:,.0f} ARS",
    )

st.markdown("---")

# ── Gauge ocupación ───────────────────────────────────────────────────────────
col1, col2 = st.columns(2)

with col1:
    st.markdown("#### Probabilidad de alta ocupación")
    fig_gauge = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=result['prob_alta_ocup'],
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': "% probabilidad de estar por encima de la mediana", 'font': {'size': 13}},
        delta={'reference': 50, 'increasing': {'color': "#FF5A5F"}},
        gauge={
            'axis': {'range': [0, 100], 'tickwidth': 1},
            'bar': {'color': "#FF5A5F"},
            'bgcolor': "white",
            'borderwidth': 2,
            'bordercolor': "#eee",
            'steps': [
                {'range': [0, 40], 'color': '#FFF0F0'},
                {'range': [40, 65], 'color': '#FFE0E0'},
                {'range': [65, 100], 'color': '#FFD0D0'},
            ],
            'threshold': {
                'line': {'color': "#c0392b", 'width': 4},
                'thickness': 0.75,
                'value': 50
            }
        }
    ))
    fig_gauge.update_layout(height=280, margin=dict(l=20, r=20, t=60, b=20),
                            paper_bgcolor='white')
    st.plotly_chart(fig_gauge, use_container_width=True)

with col2:
    st.markdown("#### Comparativa con la media del barrio")
    
    categories = ['Precio/noche', 'Noches/año', 'Revenue anual']
    
    # Normalizar para comparar
    tu_vals = [result['precio'], result['noches'], result['revenue_anual']]
    barrio_vals = [
        result['precio_medio_barrio'],
        result['ocup_media_barrio'],
        result['precio_medio_barrio'] * result['ocup_media_barrio']
    ]
    
    fig_bar = go.Figure()
    fig_bar.add_trace(go.Bar(
        name='Tu listing', x=categories,
        y=[v/b*100 for v, b in zip(tu_vals, barrio_vals)],
        marker_color='#FF5A5F',
        text=[f"{v/b*100:.0f}%" for v, b in zip(tu_vals, barrio_vals)],
        textposition='outside'
    ))
    fig_bar.add_hline(y=100, line_dash="dash", line_color="#888",
                      annotation_text="Media del barrio (100%)")
    fig_bar.update_layout(
        height=280,
        yaxis_title="% vs media del barrio",
        showlegend=False,
        paper_bgcolor='white',
        plot_bgcolor='white',
        margin=dict(l=20, r=20, t=40, b=20),
        yaxis=dict(gridcolor='#f0f0f0')
    )
    st.plotly_chart(fig_bar, use_container_width=True)

st.markdown("---")

# ── Desglose revenue mensual ──────────────────────────────────────────────────
st.markdown("### 📅 Proyección de ingresos mensual")

meses = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun',
         'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic']

# Buenos Aires: verano dic-mar (alta), invierno may-jul (baja)
estacionalidad = [1.25, 1.20, 1.10, 0.95, 0.85, 0.80,
                  0.80, 0.85, 0.95, 1.00, 1.05, 1.20]
revenue_mensual_est = [result['revenue_mensual'] * f for f in estacionalidad]

fig_line = go.Figure()
fig_line.add_trace(go.Bar(
    x=meses, y=revenue_mensual_est,
    marker_color=['#FF5A5F' if f >= 1.0 else '#FFB3B5' for f in estacionalidad],
    text=[f"${v:,.0f}" for v in revenue_mensual_est],
    textposition='outside',
    textfont=dict(size=9),
))
fig_line.update_layout(
    height=320,
    yaxis_title="Revenue estimado (ARS)",
    paper_bgcolor='white',
    plot_bgcolor='white',
    margin=dict(l=20, r=20, t=20, b=20),
    yaxis=dict(gridcolor='#f0f0f0'),
    xaxis=dict(gridcolor='#f0f0f0'),
)
st.plotly_chart(fig_line, use_container_width=True)
st.caption("*La estacionalidad aplica el patrón histórico de Buenos Aires: pico en temporada de verano (diciembre–marzo).")

st.markdown("---")

# ── Resumen inputs ────────────────────────────────────────────────────────────
with st.expander("📋 Ver datos introducidos"):
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f"**Barrio:** {data['barrio']}")
        st.markdown(f"**Tipo:** {data['room_type']}")
        st.markdown(f"**Capacidad:** {data['accommodates']} personas")
    with col2:
        st.markdown(f"**Dormitorios:** {data['bedrooms']}")
        st.markdown(f"**Baños:** {data['bathrooms']}")
        st.markdown(f"**Amenities:** {data['amenity_count']}")
    with col3:
        st.markdown(f"**Reserva instantánea:** {'Sí' if data['instant_bookable'] else 'No'}")
        st.markdown(f"**Estancia mínima:** {data['minimum_nights']} noches")
        st.markdown(f"**Años de experiencia:** {data['years_hosting']}")

# ── Nota metodológica ─────────────────────────────────────────────────────────
st.info("""
**Nota metodológica:** El precio se estima con XGBoost (R²=0.82) entrenado sobre 35.172 listings reales. 
La ocupación usa Regresión Logística (AUC=0.75) sobre features estructurales únicamente, 
replicando la metodología del paper del grupo. 
La estimación de ocupación en noches usa el **San Francisco Model** (Inside Airbnb).
""")

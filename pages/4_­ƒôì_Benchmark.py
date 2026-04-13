"""
pages/4_📍_Benchmark.py
------------------------
Scatter plot: tu listing vs el mercado real de Buenos Aires.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os, sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from utils.predictor import predict

st.set_page_config(page_title="Benchmark", page_icon="📍", layout="wide")

@st.cache_data
def load_data():
    base = os.path.join(os.path.dirname(__file__), '..', 'data')
    scatter  = pd.read_csv(os.path.join(base, 'scatter_listings.csv'))
    barrios  = pd.read_csv(os.path.join(base, 'barrios_medias.csv'))
    return scatter, barrios

scatter_df, barrios_df = load_data()

if 'listing_data' not in st.session_state:
    st.warning("⚠️ Primero rellena los datos en **🏠 Tu Listing**.")
    st.stop()

data = st.session_state['listing_data']

result = predict(
    barrio=data['barrio'],
    room_type=data['room_type'],
    accommodates=data['accommodates'],
    amenity_count=data['amenity_count'],
    barrios_df=barrios_df,
)

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("# 📍 Tu listing vs el mercado de Buenos Aires")
st.markdown("Compara la posición de tu piso frente a los 5.000 listings más activos de la ciudad.")
st.markdown("---")

# ── Filtros ───────────────────────────────────────────────────────────────────
col1, col2, col3 = st.columns(3)
with col1:
    filtro_barrio = st.checkbox(f"Solo mostrar listings de {data['barrio']}", value=False)
with col2:
    filtro_tipo = st.checkbox(f"Solo mostrar '{data['room_type']}'", value=False)
with col3:
    cap_precio = st.slider("Precio máximo en gráfico (ARS)", 10000, 200000, 150000, 5000)

# Aplicar filtros
df_plot = scatter_df.copy()
if filtro_barrio:
    df_plot = df_plot[df_plot['barrio'] == data['barrio']]
if filtro_tipo:
    df_plot = df_plot[df_plot['room_type'] == data['room_type']]
df_plot = df_plot[df_plot['precio'] <= cap_precio]

# ── Scatter principal ─────────────────────────────────────────────────────────
st.markdown("### 💹 Precio vs Ocupación — Tu posición en el mercado")

# Color por barrio vs otros
df_plot['grupo'] = df_plot['barrio'].apply(
    lambda b: data['barrio'] if b == data['barrio'] else 'Otros barrios'
)
color_map = {data['barrio']: '#FFB3B5', 'Otros barrios': '#E0E0E0'}

fig = px.scatter(
    df_plot,
    x='precio', y='ocupacion',
    color='grupo',
    color_discrete_map=color_map,
    opacity=0.6,
    hover_data=['barrio', 'room_type', 'accommodates', 'amenity_count'],
    labels={
        'precio': 'Precio por noche (ARS)',
        'ocupacion': 'Ocupación estimada (noches/año)',
        'grupo': ''
    },
    title=f"Mercado Airbnb Buenos Aires — {len(df_plot):,} listings"
)

# Tu listing
fig.add_trace(go.Scatter(
    x=[result['precio']],
    y=[result['noches']],
    mode='markers+text',
    name='🏠 Tu listing',
    marker=dict(
        color='#FF5A5F',
        size=18,
        symbol='star',
        line=dict(color='white', width=2)
    ),
    text=['← Tu listing'],
    textposition='middle right',
    textfont=dict(color='#FF5A5F', size=13, family='Arial Black'),
))

# Líneas de referencia (mediana del barrio)
barrio_info = barrios_df[barrios_df['barrio'] == data['barrio']].iloc[0]
fig.add_hline(y=barrio_info['ocup_media_barrio'], line_dash="dot",
              line_color="#FF5A5F", opacity=0.5,
              annotation_text=f"Ocupación media {data['barrio']}")
fig.add_vline(x=barrio_info['precio_medio_barrio'], line_dash="dot",
              line_color="#FF5A5F", opacity=0.5,
              annotation_text=f"Precio medio {data['barrio']}")

fig.update_layout(
    height=520,
    paper_bgcolor='white',
    plot_bgcolor='white',
    margin=dict(l=20, r=20, t=60, b=20),
    xaxis=dict(gridcolor='#f0f0f0', title='Precio por noche (ARS)'),
    yaxis=dict(gridcolor='#f0f0f0', title='Ocupación estimada (noches/año)'),
    legend=dict(orientation='h', yanchor='bottom', y=1.02),
)
st.plotly_chart(fig, use_container_width=True)

# ── Cuadrantes ────────────────────────────────────────────────────────────────
st.markdown("### 🎯 ¿En qué cuadrante está tu listing?")

precio_med = barrio_info['precio_medio_barrio']
ocup_med   = barrio_info['ocup_media_barrio']

alto_precio = result['precio'] >= precio_med
alta_ocup   = result['noches'] >= ocup_med

if alto_precio and alta_ocup:
    cuadrante = "⭐ **TOP PERFORMER**"
    desc = "Precio y ocupación por encima de la media de tu barrio. Excelente posicionamiento."
    color = "#27ae60"
elif alto_precio and not alta_ocup:
    cuadrante = "💎 **PREMIUM / BAJO VOLUMEN**"
    desc = "Precio alto pero ocupación por debajo de la media. Puede indicar sobrevalorización o nichos premium."
    color = "#f39c12"
elif not alto_precio and alta_ocup:
    cuadrante = "🔥 **ALTO VOLUMEN / PRECIO BAJO**"
    desc = "Mucha demanda pero precio bajo. Oportunidad de subir precio gradualmente."
    color = "#2980b9"
else:
    cuadrante = "⚠️ **EN DESARROLLO**"
    desc = "Precio y ocupación por debajo de la media. Hay margen de mejora en ambas dimensiones."
    color = "#e74c3c"

st.markdown(f"""
<div style='background: white; border-left: 5px solid {color}; border-radius: 8px; 
            padding: 1.2rem; box-shadow: 0 2px 8px rgba(0,0,0,0.06);'>
    <div style='font-size: 1.3rem;'>{cuadrante}</div>
    <div style='color: #666; margin-top: 0.4rem;'>{desc}</div>
    <div style='margin-top: 0.8rem; display: flex; gap: 2rem;'>
        <span>Tu precio: <strong>${result['precio']:,.0f} ARS</strong> 
              (media barrio: ${precio_med:,.0f} ARS)</span>
        <span>Tu ocupación: <strong>{result['noches']:.0f} noches</strong> 
              (media barrio: {ocup_med:.0f} noches)</span>
    </div>
</div>
""", unsafe_allow_html=True)

st.markdown("---")

# ── Revenue por barrio ────────────────────────────────────────────────────────
st.markdown("### 🏙️ Precio medio por barrio")

barrios_sorted = barrios_df.sort_values('precio_medio_barrio', ascending=True).tail(20)
colors = ['#FF5A5F' if b == data['barrio'] else '#FFB3B5' for b in barrios_sorted['barrio']]

fig2 = go.Figure(go.Bar(
    x=barrios_sorted['precio_medio_barrio'],
    y=barrios_sorted['barrio'],
    orientation='h',
    marker_color=colors,
    text=[f"${v:,.0f}" for v in barrios_sorted['precio_medio_barrio']],
    textposition='outside',
    textfont=dict(size=9),
))
fig2.update_layout(
    height=500,
    xaxis_title="Precio medio por noche (ARS)",
    paper_bgcolor='white',
    plot_bgcolor='white',
    margin=dict(l=20, r=80, t=20, b=20),
    xaxis=dict(gridcolor='#f0f0f0'),
)
st.plotly_chart(fig2, use_container_width=True)

st.markdown("---")

# ── CTA Airbnb ────────────────────────────────────────────────────────────────
st.markdown("### 🚀 ¿Listo para publicar tu anuncio?")
col1, col2 = st.columns([2, 1])
with col1:
    st.markdown("""
    Ya tienes toda la información para lanzar tu listing con confianza:
    - Sabes cuánto cobrar por noche
    - Sabes cuántas noches puedes esperar reservar
    - Sabes qué amenities añadir para maximizar tus ingresos
    - Sabes dónde estás en el mercado
    """)
with col2:
    st.markdown("""
    <div style='text-align: center; padding: 1rem;'>
        <a href='https://www.airbnb.es/host/homes' target='_blank' 
           style='background: #FF5A5F; color: white; padding: 0.8rem 1.5rem; 
                  border-radius: 8px; text-decoration: none; font-weight: 700; 
                  font-size: 1.1rem; display: inline-block;'>
            🏠 Publicar mi anuncio en Airbnb →
        </a>
        <div style='margin-top: 0.8rem; color: #888; font-size: 0.85rem;'>
            Te redirige a la página oficial de Airbnb
        </div>
    </div>
    """, unsafe_allow_html=True)

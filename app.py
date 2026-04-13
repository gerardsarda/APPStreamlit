"""
app.py — Listing Performance Predictor
#AdaLovelaceGroup · ISDI Máster Data Analytics 2025-2026

Ejecutar con:
    streamlit run app.py
"""

import streamlit as st

st.set_page_config(
    page_title="Listing Performance Predictor",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Estilos globales ──────────────────────────────────────────────────────────
st.markdown("""
<style>
/* Fondo y tipografía general */
[data-testid="stAppViewContainer"] {
    background-color: #fafafa;
}
/* Sidebar */
[data-testid="stSidebar"] {
    background: linear-gradient(160deg, #FF5A5F 0%, #c0392b 100%);
}
[data-testid="stSidebar"] * {
    color: white !important;
}
[data-testid="stSidebar"] .stRadio label {
    color: white !important;
    font-weight: 500;
}
/* Botón primario */
div.stButton > button {
    background-color: #FF5A5F;
    color: white;
    border: none;
    border-radius: 8px;
    font-weight: 600;
    padding: 0.5rem 1.5rem;
    transition: background 0.2s;
}
div.stButton > button:hover {
    background-color: #c0392b;
    color: white;
}
/* Métricas */
[data-testid="stMetric"] {
    background: white;
    border-radius: 12px;
    padding: 1rem;
    box-shadow: 0 2px 8px rgba(0,0,0,0.07);
}
/* Separador */
hr { border-color: #FF5A5F33; }
/* Títulos */
h1, h2, h3 { color: #222 !important; }
</style>
""", unsafe_allow_html=True)

# ── Sidebar con logo y navegación ────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🏠 Listing Performance Predictor")
    st.markdown("---")
    st.markdown("**#AdaLovelaceGroup**")
    st.markdown("ISDI · Máster Data Analytics")
    st.markdown("Buenos Aires · 2025–2026")
    st.markdown("---")
    st.markdown("""
    ### Cómo funciona
    1. **Tu listing** — introduce los datos de tu piso
    2. **Resultados** — precio y ocupación estimados
    3. **Mejoras** — qué puedes hacer para subir tus ingresos
    4. **Benchmark** — cómo estás vs el mercado
    """)
    st.markdown("---")
    st.caption("Modelo entrenado sobre datos reales de Airbnb Buenos Aires (Inside Airbnb · 35.172 listings)")

# ── Página de bienvenida ──────────────────────────────────────────────────────
col1, col2 = st.columns([2, 1])

with col1:
    st.markdown("# 🏠 Listing Performance Predictor")
    st.markdown("""
    ### ¿Cuánto puedes ganar en Airbnb antes de publicar tu anuncio?
    
    Esta herramienta usa **modelos de Machine Learning** entrenados sobre más de 35.000 
    listings reales de Buenos Aires para estimar, antes de que publiques tu anuncio:
    """)
    
    col_a, col_b, col_c = st.columns(3)
    with col_a:
        st.markdown("""
        #### 💰 Precio por noche
        Estimación basada en ubicación, tamaño y amenities de tu piso
        """)
    with col_b:
        st.markdown("""
        #### 📅 Ocupación esperada
        Noches reservadas al año según las características de tu listing
        """)
    with col_c:
        st.markdown("""
        #### 📈 Revenue anual
        Ingreso estimado: precio × noches reservadas
        """)
    
    st.markdown("---")
    st.info("👈 **Empieza por la página '🏠 Tu Listing'** en el menú de la izquierda")

with col2:
    st.markdown("""
    <div style='background: white; border-radius: 16px; padding: 1.5rem; 
                box-shadow: 0 4px 16px rgba(255,90,95,0.15); text-align: center;'>
        <div style='font-size: 3rem;'>🏆</div>
        <div style='font-size: 0.9rem; color: #666; margin-top: 0.5rem;'>Modelo entrenado con</div>
        <div style='font-size: 2rem; font-weight: 700; color: #FF5A5F;'>35.172</div>
        <div style='font-size: 0.9rem; color: #666;'>listings reales</div>
        <hr style='border-color: #eee;'>
        <div style='font-size: 0.9rem; color: #666;'>Precisión modelo precio</div>
        <div style='font-size: 2rem; font-weight: 700; color: #FF5A5F;'>R² 0.82</div>
        <hr style='border-color: #eee;'>
        <div style='font-size: 0.9rem; color: #666;'>Precisión modelo ocupación</div>
        <div style='font-size: 2rem; font-weight: 700; color: #FF5A5F;'>AUC 0.75</div>
        <hr style='border-color: #eee;'>
        <div style='font-size: 0.9rem; color: #666;'>Barrios cubiertos</div>
        <div style='font-size: 2rem; font-weight: 700; color: #FF5A5F;'>48</div>
    </div>
    """, unsafe_allow_html=True)

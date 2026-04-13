"""
pages/1_🏠_Tu_Listing.py
"""

import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="Tu Listing", page_icon="🏠", layout="wide")

@st.cache_data
def load_barrios():
    path = os.path.join(os.path.dirname(__file__), '..', 'data', 'barrios_medias.csv')
    return pd.read_csv(path)

barrios_df   = load_barrios()
lista_barrios = barrios_df.sort_values('n_listings', ascending=False)['barrio'].tolist()

st.markdown("# 🏠 Cuéntanos sobre tu piso")
st.markdown("Rellena los datos de tu alojamiento. Para hosts nuevos deja los campos de reseñas en 0.")
st.markdown("---")

with st.form("listing_form"):

    # ── Ubicación ─────────────────────────────────────────────────────────────
    st.markdown("### 📍 Ubicación")
    col1, col2 = st.columns(2)
    with col1:
        barrio = st.selectbox("Barrio de Buenos Aires", options=lista_barrios)
    with col2:
        info = barrios_df[barrios_df['barrio'] == barrio].iloc[0]
        st.metric("Precio medio del barrio",    f"${info['precio_medio_barrio']:,.0f} ARS/noche")
        st.metric("Ocupación media del barrio", f"{info['ocup_media_barrio']:.0f} noches/año")

    st.markdown("---")

    # ── Características ───────────────────────────────────────────────────────
    st.markdown("### 🛏️ Características del alojamiento")
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        room_type = st.selectbox("Tipo de alojamiento",
            ["Entire home/apt", "Private room", "Shared room", "Hotel room"])
    with col2:
        accommodates = st.slider("Huéspedes máx.", 1, 16, 2)
    with col3:
        bedrooms = st.slider("Dormitorios", 0, 8, 1)
    with col4:
        bathrooms = st.slider("Baños", 1, 6, 1)
    with col5:
        beds = st.slider("Camas", 1, 10, 1)

    st.markdown("---")

    # ── Amenities ─────────────────────────────────────────────────────────────
    st.markdown("### ✨ Comodidades")
    amenities_options = {
        "WiFi": True, "Cocina equipada": True, "Aire acondicionado": False,
        "Calefacción": True, "TV / Smart TV": False, "Lavadora": False,
        "Secadora": False, "Cafetera": False, "Microondas": True,
        "Plancha": False, "Escritorio": False, "Balcón / Terraza": False,
        "Piscina": False, "Gimnasio": False, "Ascensor": False,
        "Parking": False, "Admite mascotas": False, "Detector de humo": True,
        "Extintor": False, "Botiquín": False,
    }
    cols = st.columns(4)
    selected = []
    for i, (am, default) in enumerate(amenities_options.items()):
        with cols[i % 4]:
            if st.checkbox(am, value=default, key=f"am_{i}"):
                selected.append(am)
    num_amenities = len(selected)
    st.info(f"✅ Has seleccionado **{num_amenities} amenities** (media del mercado: ~36)")

    st.markdown("---")

    # ── Políticas ─────────────────────────────────────────────────────────────
    st.markdown("### 📋 Políticas")
    col1, col2, col3 = st.columns(3)
    with col1:
        minimum_nights = st.number_input("Estancia mínima (noches)", 1, 30, 2)
    with col2:
        maximum_nights = st.number_input("Estancia máxima (noches)", 1, 365, 365)
    with col3:
        instant_bookable = st.toggle("Reserva instantánea", value=False)

    st.markdown("---")

    # ── Perfil del host ───────────────────────────────────────────────────────
    st.markdown("### 👤 Perfil del host")
    col1, col2 = st.columns(2)
    with col1:
        antiguedad_host      = st.slider("Años de experiencia como host", 0, 20, 0)
    with col2:
        host_listings_count  = st.number_input("Nº de propiedades que gestionas", 1, 100, 1)

    st.markdown("---")

    # ── Reseñas (opcional para hosts existentes) ──────────────────────────────
    st.markdown("### ⭐ Reseñas *(déjalo en 0 si eres host nuevo)*")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        number_of_reviews     = st.number_input("Nº total de reseñas",     0, 5000, 0)
        number_of_reviews_ltm = st.number_input("Reseñas último año",      0, 500,  0)
    with col2:
        reviews_per_month     = st.number_input("Reseñas por mes",         0.0, 50.0, 0.0, step=0.1)
        review_scores_rating  = st.slider("Puntuación global (0=sin reseñas)", 0.0, 5.0, 0.0, 0.1)
    with col3:
        review_scores_cleanliness    = st.slider("Limpieza",        0.0, 5.0, 0.0, 0.1)
        review_scores_communication  = st.slider("Comunicación",    0.0, 5.0, 0.0, 0.1)
        review_scores_checkin        = st.slider("Check-in",        0.0, 5.0, 0.0, 0.1)
    with col4:
        review_scores_accuracy       = st.slider("Precisión",       0.0, 5.0, 0.0, 0.1)
        review_scores_location       = st.slider("Ubicación",       0.0, 5.0, 0.0, 0.1)
        review_scores_value          = st.slider("Calidad-precio",  0.0, 5.0, 0.0, 0.1)

    st.markdown("---")
    submitted = st.form_submit_button("🔮 Ver mi predicción", use_container_width=True)

if submitted:
    st.session_state['listing_data'] = {
        'barrio':                      barrio,
        'room_type':                   room_type,
        'accommodates':                accommodates,
        'bedrooms':                    bedrooms,
        'bathrooms':                   bathrooms,
        'beds':                        beds,
        'minimum_nights':              minimum_nights,
        'maximum_nights':              maximum_nights,
        'num_amenities':               num_amenities,
        'antiguedad_host':             antiguedad_host,
        'host_listings_count':         host_listings_count,
        'instant_bookable':            instant_bookable,
        'number_of_reviews':           number_of_reviews,
        'number_of_reviews_ltm':       number_of_reviews_ltm,
        'reviews_per_month':           reviews_per_month,
        'review_scores_rating':        review_scores_rating,
        'review_scores_cleanliness':   review_scores_cleanliness,
        'review_scores_communication': review_scores_communication,
        'review_scores_checkin':       review_scores_checkin,
        'review_scores_accuracy':      review_scores_accuracy,
        'review_scores_location':      review_scores_location,
        'review_scores_value':         review_scores_value,
    }
    st.success("✅ ¡Datos guardados! Ve a **📊 Resultados** en el menú de la izquierda.")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Barrio", barrio)
    col2.metric("Tipo", room_type)
    col3.metric("Capacidad", f"{accommodates} personas")
    col4.metric("Amenities", num_amenities)

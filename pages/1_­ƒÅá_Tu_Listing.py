"""
pages/1_🏠_Tu_Listing.py
------------------------
Formulario de inputs del usuario.
Guarda en st.session_state para que las otras páginas accedan.
"""

import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="Tu Listing", page_icon="🏠", layout="wide")

# ── Cargar barrios ────────────────────────────────────────────────────────────
@st.cache_data
def load_barrios():
    path = os.path.join(os.path.dirname(__file__), '..', 'data', 'barrios_medias.csv')
    return pd.read_csv(path)

barrios_df = load_barrios()
lista_barrios = barrios_df.sort_values('n_listings', ascending=False)['barrio'].tolist()

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("# 🏠 Cuéntanos sobre tu piso")
st.markdown("Rellena los datos de tu alojamiento. Solo necesitamos la información básica — el resto lo calculamos nosotros.")
st.markdown("---")

# ── Formulario ────────────────────────────────────────────────────────────────
with st.form("listing_form"):
    
    # SECCIÓN 1: Ubicación
    st.markdown("### 📍 Ubicación")
    col1, col2 = st.columns(2)
    with col1:
        barrio = st.selectbox(
            "Barrio de Buenos Aires",
            options=lista_barrios,
            help="El barrio es la variable con mayor impacto en el precio."
        )
    with col2:
        # Mostrar info del barrio seleccionado
        info = barrios_df[barrios_df['barrio'] == barrio].iloc[0]
        st.metric("Precio medio del barrio", f"${info['precio_medio_barrio']:,.0f} ARS/noche")
        st.metric("Ocupación media del barrio", f"{info['ocup_media_barrio']:.0f} noches/año")
    
    st.markdown("---")
    
    # SECCIÓN 2: Características del piso
    st.markdown("### 🛏️ Características del alojamiento")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        room_type = st.selectbox(
            "Tipo de alojamiento",
            options=["Entire home/apt", "Private room", "Shared room", "Hotel room"],
            help="El alojamiento completo tiene mayor demanda en Buenos Aires (91% del mercado)."
        )
    with col2:
        accommodates = st.slider(
            "Capacidad máxima (huéspedes)",
            min_value=1, max_value=16, value=2,
            help="Número máximo de huéspedes que admite tu piso."
        )
    with col3:
        bedrooms = st.slider("Dormitorios", min_value=0, max_value=8, value=1)
    with col4:
        bathrooms = st.slider("Baños", min_value=1, max_value=6, value=1)

    st.markdown("---")
    
    # SECCIÓN 3: Amenities
    st.markdown("### ✨ Comodidades (Amenities)")
    st.markdown("Marca las comodidades que tiene o tendrá tu piso:")
    
    amenities_options = {
        "WiFi":                      True,
        "Cocina equipada":           True,
        "Aire acondicionado":        False,
        "Calefacción":               True,
        "TV / Smart TV":             False,
        "Lavadora":                  False,
        "Secadora":                  False,
        "Cafetera / Nespresso":      False,
        "Microondas":                True,
        "Plancha":                   False,
        "Escritorio / zona trabajo": False,
        "Balcón / Terraza":          False,
        "Piscina":                   False,
        "Gimnasio":                  False,
        "Ascensor":                  False,
        "Parking":                   False,
        "Admite mascotas":           False,
        "Detector de humo":          True,
        "Extintor":                  False,
        "Botiquín":                  False,
    }
    
    cols = st.columns(4)
    selected_amenities = []
    for i, (amenity, default) in enumerate(amenities_options.items()):
        with cols[i % 4]:
            if st.checkbox(amenity, value=default, key=f"am_{i}"):
                selected_amenities.append(amenity)
    
    amenity_count = len(selected_amenities)
    st.info(f"✅ Has seleccionado **{amenity_count} amenities** (media del mercado: ~36)")
    
    st.markdown("---")
    
    # SECCIÓN 4: Políticas
    st.markdown("### 📋 Políticas de reserva")
    col1, col2, col3 = st.columns(3)
    with col1:
        instant_bookable = st.toggle(
            "Reserva instantánea",
            value=False,
            help="Permite que los huéspedes reserven sin aprobación previa. Aumenta la conversión."
        )
    with col2:
        minimum_nights = st.number_input(
            "Estancia mínima (noches)",
            min_value=1, max_value=30, value=2
        )
    with col3:
        years_hosting = st.slider(
            "Años de experiencia como host",
            min_value=0, max_value=20, value=0,
            help="0 si eres nuevo en Airbnb."
        )
    
    st.markdown("---")
    
    # SUBMIT
    col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 2])
    with col_btn1:
        submitted = st.form_submit_button("🔮 Ver mi predicción", use_container_width=True)
    with col_btn2:
        st.form_submit_button("🔄 Limpiar", use_container_width=True)

# ── Guardar en session_state ──────────────────────────────────────────────────
if submitted:
    st.session_state['listing_data'] = {
        'barrio':           barrio,
        'room_type':        room_type,
        'accommodates':     accommodates,
        'bedrooms':         bedrooms,
        'bathrooms':        bathrooms,
        'amenity_count':    amenity_count,
        'amenities_list':   selected_amenities,
        'instant_bookable': instant_bookable,
        'minimum_nights':   minimum_nights,
        'years_hosting':    years_hosting,
    }
    st.success("✅ ¡Datos guardados! Ve a **📊 Resultados** en el menú de la izquierda.")
    
    # Resumen del input
    st.markdown("### Resumen de tu listing")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Barrio", barrio)
    col2.metric("Tipo", room_type.replace("Entire home/apt", "Piso completo").replace("Private room", "Habitación privada"))
    col3.metric("Capacidad", f"{accommodates} personas")
    col4.metric("Amenities", f"{amenity_count}")

elif 'listing_data' in st.session_state:
    st.info("👆 Ya tienes datos guardados. Puedes modificarlos o ir directamente a **📊 Resultados**.")

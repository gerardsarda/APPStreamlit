# 🏠 Listing Performance Predictor
**#AdaLovelaceGroup · ISDI Máster Data Analytics 2025–2026**

Herramienta para predecir precio y ocupación de un listing de Airbnb en Buenos Aires antes de publicarlo.

---

## ⚙️ Setup (solo la primera vez)

### 1. Instalar dependencias
```bash
pip install -r requirements.txt
```

### 2. Entrenar los modelos
```bash
python models/train_models.py
```
Esto genera el archivo `models/artifacts.pkl` con los modelos entrenados.
Tarda ~30 segundos. Solo hay que hacerlo una vez.

### 3. Lanzar la app
```bash
streamlit run app.py
```

Se abrirá automáticamente en tu navegador en `http://localhost:8501`

---

## 📁 Estructura del proyecto

```
airbnb_app/
├── app.py                          ← Página de bienvenida
├── requirements.txt
├── README.md
├── pages/
│   ├── 1_🏠_Tu_Listing.py         ← Formulario de inputs
│   ├── 2_📊_Resultados.py         ← Precio + ocupación + revenue
│   ├── 3_💡_Mejoras.py            ← Recomendaciones accionables
│   └── 4_📍_Benchmark.py          ← Scatter vs mercado real
├── models/
│   ├── train_models.py             ← Script de entrenamiento
│   └── artifacts.pkl               ← (se genera al ejecutar train_models.py)
├── data/
│   ├── barrios_medias.csv          ← Variables externas por barrio (BigQuery)
│   └── scatter_listings.csv        ← 5.000 listings para benchmark (BigQuery)
└── utils/
    └── predictor.py                ← Funciones de predicción
```

---

## 🧠 Modelos

| Modelo | Algoritmo | Target | Métrica |
|--------|-----------|--------|---------|
| Precio | XGBoost Regressor | log(precio) | R² ≈ 0.82 |
| Ocupación | Logistic Regression | alta_ocupacion (binario) | AUC ≈ 0.75 |

**Variables del modelo (lo que el usuario NO rellena — se imputa por barrio):**
- `distancia_al_obelisco_m`
- `crimes_within_500m`
- `subte_within_300m`
- `airbnb_density_250m`

**Variables del modelo (lo que el usuario SÍ rellena):**
- Barrio, tipo de alojamiento
- Capacidad (accommodates)
- Número de amenities

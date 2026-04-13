"""
train_models.py
---------------
Ejecutar UNA VEZ antes de lanzar la app:
    python models/train_models.py

Entrena XGBoost (precio) y LogisticRegression (alta ocupación)
usando los datos reales de BigQuery exportados en los CSV.
Guarda los modelos como .pkl en esta misma carpeta.
"""

import pandas as pd
import numpy as np
import pickle
import os
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import OrdinalEncoder, StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import r2_score, roc_auc_score
import xgboost as xgb

# ── Rutas ────────────────────────────────────────────────────────────────────
BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
DATA_DIR   = os.path.join(BASE_DIR, '..', 'data')
SCATTER_CSV = os.path.join(DATA_DIR, 'scatter_listings.csv')
BARRIOS_CSV = os.path.join(DATA_DIR, 'barrios_medias.csv')

# ── Cargar datos ─────────────────────────────────────────────────────────────
print("Cargando datos...")
df = pd.read_csv(SCATTER_CSV)
barrios = pd.read_csv(BARRIOS_CSV)

# Merge con variables externas por barrio
df = df.merge(
    barrios[['barrio','dist_obelisco','crimes','subte','density']],
    on='barrio', how='left'
)

print(f"Dataset: {df.shape[0]} filas, {df.shape[1]} columnas")
print(f"Barrios: {df['barrio'].nunique()}")

# ── Definir features ─────────────────────────────────────────────────────────
VARS_NUM = [
    'accommodates', 'amenity_count',
    'dist_obelisco', 'crimes', 'subte', 'density',
]
VARS_CAT = ['barrio', 'room_type']
TARGET_PRICE = 'precio'
TARGET_OCUP  = 'ocupacion'

df = df.dropna(subset=VARS_NUM + VARS_CAT + [TARGET_PRICE, TARGET_OCUP])
df = df[df[TARGET_PRICE] > 0]
df = df[df[TARGET_OCUP] >= 0]

# Log precio (target para XGBoost)
df['log_precio'] = np.log(df[TARGET_PRICE])

# Alta ocupación (target binario para LogReg)
mediana_ocup = df[TARGET_OCUP].median()
df['alta_ocupacion'] = (df[TARGET_OCUP] > mediana_ocup).astype(int)
print(f"Mediana ocupación: {mediana_ocup:.0f} noches/año")
print(f"Alta ocupación (1): {df['alta_ocupacion'].sum()} | Baja (0): {(df['alta_ocupacion']==0).sum()}")

# ── Encoder para variables categóricas ───────────────────────────────────────
enc = OrdinalEncoder(handle_unknown='use_encoded_value', unknown_value=-1)
df[VARS_CAT] = enc.fit_transform(df[VARS_CAT])

X = df[VARS_NUM + VARS_CAT].astype(float)

# ── MODELO 1: XGBoost Precio ─────────────────────────────────────────────────
print("\n--- Entrenando XGBoost (precio)...")
y_price = df['log_precio']
X_tr, X_te, y_tr, y_te = train_test_split(X, y_price, test_size=0.2, random_state=42)

model_price = xgb.XGBRegressor(
    n_estimators=400,
    learning_rate=0.05,
    max_depth=6,
    subsample=0.8,
    colsample_bytree=0.8,
    random_state=42,
    verbosity=0,
)
model_price.fit(X_tr, y_tr)
r2 = r2_score(y_te, model_price.predict(X_te))
print(f"R² precio (test): {r2:.3f}")

# ── MODELO 2: LogReg Alta Ocupación ──────────────────────────────────────────
print("\n--- Entrenando LogisticRegression (ocupación)...")
y_ocup = df['alta_ocupacion']
X_tr2, X_te2, y_tr2, y_te2 = train_test_split(X, y_ocup, test_size=0.2, random_state=42)

scaler = StandardScaler()
X_tr2_sc = scaler.fit_transform(X_tr2)
X_te2_sc  = scaler.transform(X_te2)

model_ocup = LogisticRegression(max_iter=1000, random_state=42)
model_ocup.fit(X_tr2_sc, y_tr2)
auc = roc_auc_score(y_te2, model_ocup.predict_proba(X_te2_sc)[:,1])
print(f"AUC ocupación (test): {auc:.3f}")

# ── Guardar modelos ───────────────────────────────────────────────────────────
artifacts = {
    'model_price':    model_price,
    'model_ocup':     model_ocup,
    'encoder':        enc,
    'scaler':         scaler,
    'vars_num':       VARS_NUM,
    'vars_cat':       VARS_CAT,
    'mediana_ocup':   mediana_ocup,
    'cat_categories': {
        'barrio':    enc.categories_[0].tolist(),
        'room_type': enc.categories_[1].tolist(),
    }
}

out_path = os.path.join(BASE_DIR, 'artifacts.pkl')
with open(out_path, 'wb') as f:
    pickle.dump(artifacts, f)

print(f"\n✅ Modelos guardados en: {out_path}")
print("Ya puedes ejecutar: streamlit run app.py")

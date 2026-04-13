"""
train_models.py
---------------
Ejecutar UNA VEZ desde la carpeta airbnb_app:
    python models/train_models.py

Replica EXACTAMENTE el notebook del grupo (Cell 12 modelo final R²~0.82
y Modelo 3 LogReg ocupación AUC~0.75).
"""

import pandas as pd
import numpy as np
import pickle
import os
from sklearn.model_selection import train_test_split
from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error, roc_auc_score
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
import xgboost as xgb

RANDOM_STATE = 42
BASE_DIR  = os.path.dirname(os.path.abspath(__file__))
DATA_DIR  = os.path.join(BASE_DIR, '..', 'data')
CSV_PATH  = os.path.join(DATA_DIR, 'dataset_completo.csv')

# ── 1. Cargar datos ───────────────────────────────────────────────────────────
print("Cargando dataset completo...")
df = pd.read_csv(CSV_PATH)
print(f"Shape original: {df.shape[0]:,} filas x {df.shape[1]} columnas")

# ── 2. Filtro outliers p1-p99 (igual que notebook Cell 12) ───────────────────
q_low  = df['log_precio'].quantile(0.01)
q_high = df['log_precio'].quantile(0.99)
df = df[(df['log_precio'] > q_low) & (df['log_precio'] < q_high)].copy()
print(f"Tras filtro outliers: {df.shape[0]:,} filas")

# ── 3. Features (replica exacta notebook Cell 12) ────────────────────────────
VARS_NUM = [
    'accommodates', 'bedrooms', 'bathrooms', 'beds',
    'review_scores_rating', 'number_of_reviews',
    'reviews_per_month', 'number_of_reviews_ltm',
    'distancia_al_obelisco_m', 'density',
    'crimes', 'subte',
    'top_atracciones_within_1000m',
    'num_amenities', 'antiguedad_host',
    'host_listings_count',
    'review_scores_location', 'review_scores_cleanliness',
    'review_scores_checkin', 'review_scores_communication',
    'review_scores_accuracy', 'review_scores_value',
]
VARS_CAT = ['barrio', 'room_type']

df_common = df[['log_precio', 'estimated_occupancy'] + VARS_NUM + VARS_CAT].dropna(
    subset=['log_precio'] + VARS_CAT
).copy()

# Imputar reviews con 0 para hosts nuevos (en predicción)
for col in VARS_NUM:
    if col in df_common.columns:
        df_common[col] = pd.to_numeric(df_common[col], errors='coerce').fillna(0)

print(f"Tras dropna: {df_common.shape[0]:,} filas")

# Consolidar categorías raras MIN_FREQ=50 (igual que notebook)
for c in VARS_CAT:
    df_common[c] = df_common[c].astype(str)
    vc   = df_common[c].value_counts()
    rare = vc[vc < 50].index
    df_common.loc[df_common[c].isin(rare), c] = 'Otro'
    print(f"  {c}: {df_common[c].nunique()} categorías")

# Guardar categorías antes del get_dummies (para predicción después)
cat_categories = {c: sorted(df_common[c].unique().tolist()) for c in VARS_CAT}

# get_dummies igual que notebook
df_d = pd.get_dummies(df_common, columns=VARS_CAT, drop_first=True, dtype=float)
cat_cols = [c for c in df_d.columns if c.startswith('barrio_') or c.startswith('room_type_')]
FEATURES = VARS_NUM + cat_cols
print(f"Total features: {len(FEATURES)}")

X     = df_d[FEATURES].copy()
y_log = df_d['log_precio'].copy()

# ── 4. Split 60/20/20 (igual que notebook Cell 12) ───────────────────────────
idx_train, idx_temp = train_test_split(X.index, test_size=0.4, random_state=RANDOM_STATE)
idx_valid, idx_test = train_test_split(idx_temp, test_size=0.5, random_state=RANDOM_STATE)

X_train = X.loc[idx_train]; X_valid = X.loc[idx_valid]; X_test = X.loc[idx_test]
y_train = y_log.loc[idx_train]; y_valid = y_log.loc[idx_valid]; y_test = y_log.loc[idx_test]
print(f"\nTrain: {len(X_train):,} | Valid: {len(X_valid):,} | Test: {len(X_test):,}")

# ── 5. XGBoost precio (hiperparámetros exactos notebook Cell 12) ──────────────
print("\n--- Entrenando XGBoost precio (puede tardar 5-10 min)...")
model_price = xgb.XGBRegressor(
    n_estimators=8000,
    learning_rate=0.03,
    max_depth=8,
    subsample=0.8,
    colsample_bytree=0.8,
    min_child_weight=1,
    reg_lambda=1,
    objective='reg:squarederror',
    random_state=RANDOM_STATE,
    n_jobs=-1,
    early_stopping_rounds=150,
    verbosity=0,
)
model_price.fit(X_train, y_train, eval_set=[(X_valid, y_valid)], verbose=False)

pred_test = model_price.predict(X_test)
r2_price  = r2_score(y_test, pred_test)
mae       = mean_absolute_error(y_test, pred_test)
print(f"✅ R² precio (test) : {r2_price:.4f}  ← objetivo ~0.82")
print(f"   Error típico     : ~{(np.exp(mae)-1)*100:.1f}%")
print(f"   Best iteration   : {model_price.best_iteration}")

# ── 6. LogReg ocupación (Modelo 3 del notebook) ───────────────────────────────
print("\n--- Entrenando LogisticRegression ocupación (Modelo 3)...")
df_ocup      = df_d[df_d['estimated_occupancy'] > 0].copy()
mediana_ocup = df_ocup['estimated_occupancy'].median()
df_ocup['alta_ocupacion'] = (df_ocup['estimated_occupancy'] > mediana_ocup).astype(int)
print(f"   Mediana ocupación : {mediana_ocup:.0f} noches/año")
print(f"   Alta (1): {df_ocup['alta_ocupacion'].sum():,} | Baja (0): {(df_ocup['alta_ocupacion']==0).sum():,}")

X_oc = df_ocup[FEATURES].copy()
y_oc = df_ocup['alta_ocupacion']
X_tr_o, X_te_o, y_tr_o, y_te_o = train_test_split(
    X_oc, y_oc, test_size=0.2, random_state=RANDOM_STATE)

scaler     = StandardScaler()
X_tr_sc    = scaler.fit_transform(X_tr_o)
X_te_sc    = scaler.transform(X_te_o)
model_ocup = LogisticRegression(max_iter=1000, random_state=RANDOM_STATE)
model_ocup.fit(X_tr_sc, y_tr_o)

auc = roc_auc_score(y_te_o, model_ocup.predict_proba(X_te_sc)[:,1])
print(f"✅ AUC ocupación (test) : {auc:.4f}  ← objetivo ~0.75")

# ── 7. Guardar artefactos ─────────────────────────────────────────────────────
artifacts = {
    'model_price':    model_price,
    'model_ocup':     model_ocup,
    'scaler':         scaler,
    'features':       FEATURES,
    'vars_num':       VARS_NUM,
    'vars_cat':       VARS_CAT,
    'cat_cols':       cat_cols,       # columnas dummy generadas
    'cat_categories': cat_categories, # valores únicos por categoría
    'mediana_ocup':   mediana_ocup,
    'r2_price':       r2_price,
    'auc_ocup':       auc,
}

out_path = os.path.join(BASE_DIR, 'artifacts.pkl')
with open(out_path, 'wb') as f:
    pickle.dump(artifacts, f)

print(f"\n{'='*50}")
print(f"✅ Guardado en: {out_path}")
print(f"   R² precio         : {r2_price:.4f}")
print(f"   AUC ocupación     : {auc:.4f}")
print("="*50)
print("\nYa puedes ejecutar:  streamlit run app.py")

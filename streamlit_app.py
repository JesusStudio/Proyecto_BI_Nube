import streamlit as st
import pandas as pd
import plotly.express as px
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import LabelEncoder
import os

columnas = [
    "RecoleccionKey", "TiempoKey",
    "CodigoZona", "NombreZona", "Sector", "Distrito",
    "Fecha", "Anio", "Mes", "NombreMes", "Trimestre", "DiaSemana", "EsFeriado",
    "PlacaCamion", "TipoCamion", "CapacidadTonMax", "EstadoCamion",
    "CodigoContenedor", "UbicacionReferencia", "TipoContenedor", "VolumenLitros",
    "NombreResiduo", "UnidadMedida", "ClaseResiduo", "EsPeligroso",
    "ToneladasRecolectadas", "TiempoRecoleccion", "PorcentajeSaturacion",
    "NumeroQuejas", "DistanciaKm"
]

df = pd.read_csv("fact_recoleccion.csv", sep=";", names=columnas)

df["Fecha"] = pd.to_datetime(df["Fecha"])
df["MesNombre"] = df["Fecha"].dt.strftime("%B")

st.set_page_config(page_title="EcoBI Dashboard", layout="wide")

st.title("Dashboard Ejecutivo – Gestión de Residuos Sólidos")

# Filtros
colf1, colf2, colf3 = st.columns(3)

distrito = colf1.selectbox("Distrito", ["Todas"] + sorted(df["Distrito"].unique()))
residuo = colf2.selectbox("Residuo", ["Todos"] + sorted(df["NombreResiduo"].unique()))
fecha = colf3.date_input("Rango de fechas", [df["Fecha"].min(), df["Fecha"].max()])

df_filtrado = df.copy()

if distrito != "Todas":
    df_filtrado = df_filtrado[df_filtrado["Distrito"] == distrito]

if residuo != "Todos":
    df_filtrado = df_filtrado[df_filtrado["NombreResiduo"] == residuo]

if len(fecha) == 2:
    df_filtrado = df_filtrado[
        (df_filtrado["Fecha"] >= pd.to_datetime(fecha[0])) &
        (df_filtrado["Fecha"] <= pd.to_datetime(fecha[1]))
    ]

# KPIs
k1, k2, k3, k4, k5 = st.columns(5)

k1.metric("Total Toneladas", f"{df_filtrado['ToneladasRecolectadas'].sum():,.2f}")
k2.metric("Tiempo Prom. Ruta", f"{df_filtrado['TiempoRecoleccion'].mean():.2f} min")
k3.metric("Saturación Prom.", f"{df_filtrado['PorcentajeSaturacion'].mean():.2f}%")
k4.metric("Total Quejas", f"{df_filtrado['NumeroQuejas'].sum():,.0f}")
k5.metric("Distancia Prom.", f"{df_filtrado['DistanciaKm'].mean():.2f} km")

# Gráficos principales
col1, col2 = st.columns(2)

ton_distrito = df_filtrado.groupby("Distrito")["ToneladasRecolectadas"].sum().reset_index()

fig1 = px.bar(
    ton_distrito,
    x="Distrito",
    y="ToneladasRecolectadas",
    title="Total Toneladas por distrito"
)

col1.plotly_chart(fig1, use_container_width=True)

ton_residuo = df_filtrado.groupby("NombreResiduo")["ToneladasRecolectadas"].sum().reset_index()

fig2 = px.pie(
    ton_residuo,
    names="NombreResiduo",
    values="ToneladasRecolectadas",
    title="Total Toneladas por residuo"
)

col2.plotly_chart(fig2, use_container_width=True)

col3, col4 = st.columns(2)

tabla = df_filtrado.groupby("NombreResiduo").agg({
    "ToneladasRecolectadas": "sum",
    "NumeroQuejas": "sum"
}).reset_index()

col3.subheader("Tabla Toneladas y Quejas por Residuo")
col3.dataframe(tabla, use_container_width=True)

ton_fecha = df_filtrado.groupby("Fecha")["ToneladasRecolectadas"].sum().reset_index()

fig3 = px.line(
    ton_fecha,
    x="Fecha",
    y="ToneladasRecolectadas",
    title="Total Toneladas por fecha",
    markers=True
)

col4.plotly_chart(fig3, use_container_width=True)

# =====================================================
# Predicciones reales con Machine Learning
# =====================================================

df_ml = df.copy()

le = LabelEncoder()
df_ml["ZonaCodificada"] = le.fit_transform(df_ml["NombreZona"])

X = df_ml[["Mes", "Trimestre", "ZonaCodificada"]]

futuros = pd.DataFrame({
    "Mes": [5, 6, 7, 8],
    "Trimestre": [2, 2, 3, 3],
    "ZonaCodificada": [2, 2, 2, 2]
})

# Modelo 1: Toneladas
modelo_ton = LinearRegression()
modelo_ton.fit(X, df_ml["ToneladasRecolectadas"])
pred_ton = modelo_ton.predict(futuros)

# Modelo 2: Tiempo de recolección
modelo_tiempo = RandomForestRegressor(n_estimators=50, random_state=42)
modelo_tiempo.fit(X, df_ml["TiempoRecoleccion"])
pred_tiempo = modelo_tiempo.predict(futuros)

# Modelo 3: Saturación
modelo_sat = LinearRegression()
modelo_sat.fit(X, df_ml["PorcentajeSaturacion"])
pred_sat = modelo_sat.predict(futuros)
pred_sat = [min(100, max(0, v)) for v in pred_sat]

tabla_pred = pd.DataFrame({
    "Mes futuro": ["Mes 5", "Mes 6", "Mes 7", "Mes 8"],
    "Toneladas predichas": [round(v, 2) for v in pred_ton],
    "Tiempo predicho (min)": [round(v, 2) for v in pred_tiempo],
    "Saturación predicha (%)": [round(v, 2) for v in pred_sat]
})

colp1, colp2, colp3 = st.columns(3)

figp1 = px.line(
    tabla_pred,
    x="Mes futuro",
    y="Toneladas predichas",
    title="Predicción de Toneladas",
    markers=True
)

figp2 = px.line(
    tabla_pred,
    x="Mes futuro",
    y="Tiempo predicho (min)",
    title="Predicción de Tiempo de Recolección",
    markers=True
)

figp3 = px.line(
    tabla_pred,
    x="Mes futuro",
    y="Saturación predicha (%)",
    title="Predicción de Saturación",
    markers=True
)

colp1.plotly_chart(figp1, use_container_width=True)
colp2.plotly_chart(figp2, use_container_width=True)
colp3.plotly_chart(figp3, use_container_width=True)


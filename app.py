import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(layout="wide")

df=pd.read_csv("fact_recoleccion.csv")

st.title("EcoBI - Gestión Inteligente de Residuos Sólidos")

st.sidebar.header("Filtros")

distrito=st.sidebar.selectbox(
"Distrito",
["Todos"]+list(df["Distrito"].unique())
)

if distrito!="Todos":
    df=df[df["Distrito"]==distrito]

k1,k2,k3,k4,k5=st.columns(5)

k1.metric("Toneladas",round(df["Toneladas"].sum(),2))

k2.metric("Tiempo Prom.",round(df["TiempoRuta"].mean(),2))

k3.metric("Saturación",round(df["Saturacion"].mean(),2))

k4.metric("Quejas",df["Quejas"].sum())

k5.metric("Distancia",round(df["DistanciaKm"].mean(),2))

c1,c2=st.columns(2)

with c1:

    fig=px.bar(
        df.groupby("Distrito")["Toneladas"].sum().reset_index(),
        x="Distrito",
        y="Toneladas",
        color="Distrito"
    )

    st.plotly_chart(fig,use_container_width=True)

with c2:

    fig=px.pie(
        df,
        names="Residuo"
    )

    st.plotly_chart(fig,use_container_width=True)

df["Fecha"]=pd.to_datetime(df["Fecha"])

mes=df.groupby(df["Fecha"].dt.month)["Toneladas"].sum().reset_index()

fig=px.line(

mes,

x="Fecha",

y="Toneladas",

markers=True

)

st.plotly_chart(fig,use_container_width=True)

st.subheader("Datos")

st.dataframe(df)

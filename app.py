import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from sklearn.linear_model import LinearRegression

# =========================================================
# CONFIGURACIÓN
# =========================================================

st.set_page_config(
    page_title="EcoBI - Dashboard Ejecutivo",
    page_icon="♻️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# =========================================================
# ESTILOS CSS
# =========================================================

st.markdown(
    """
    <style>
        .stApp {
            background-color: #f2f4f3;
        }

        .block-container {
            padding-top: 1rem;
            padding-bottom: 2rem;
            max-width: 100%;
        }

        .titulo-dashboard {
            background: white;
            padding: 17px 20px 12px 20px;
            border-radius: 12px;
            box-shadow: 0 3px 10px rgba(0,0,0,0.10);
            margin-bottom: 14px;
        }

        .titulo-dashboard h1 {
            color: #1f2937;
            font-size: 28px;
            margin: 0;
            font-weight: 750;
        }

        .linea-verde {
            height: 4px;
            width: 370px;
            background: #1f7159;
            margin-top: 10px;
            border-radius: 5px;
        }

        .kpi-card {
            background: white;
            border-radius: 13px;
            padding: 16px 9px;
            min-height: 145px;
            text-align: center;
            box-shadow: 0 4px 12px rgba(0,0,0,0.14);
            border: 1px solid #e4e7e5;
        }

        .kpi-icon {
            font-size: 42px;
            margin-bottom: 2px;
        }

        .kpi-value {
            font-size: 22px;
            font-weight: 750;
            color: #252525;
            margin-top: 2px;
        }

        .kpi-label {
            font-size: 15px;
            color: #686868;
            margin-top: 5px;
        }

        div[data-testid="stPlotlyChart"] {
            background: white;
            border-radius: 13px;
            padding: 5px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.13);
            border: 1px solid #e5e7e6;
        }

        div[data-testid="stDataFrame"] {
            background: white;
            border-radius: 13px;
            padding: 8px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.13);
            border: 1px solid #e5e7e6;
        }

        div[data-testid="stSelectbox"],
        div[data-testid="stDateInput"] {
            background: white;
            border-radius: 9px;
        }

        .stSelectbox label,
        .stDateInput label {
            font-weight: 650;
            color: #333333;
        }

        header[data-testid="stHeader"] {
            background: transparent;
        }

        #MainMenu {
            visibility: hidden;
        }

        footer {
            visibility: hidden;
        }
    </style>
    """,
    unsafe_allow_html=True
)

# =========================================================
# CARGA Y PREPARACIÓN DE DATOS
# =========================================================

@st.cache_data
def cargar_datos():
    datos = pd.read_csv("fact_recoleccion.csv")

    datos.columns = datos.columns.str.strip()

    datos["Fecha"] = pd.to_datetime(
        datos["Fecha"],
        errors="coerce"
    )

    columnas_numericas = [
        "Toneladas",
        "TiempoRuta",
        "Saturacion",
        "Quejas",
        "DistanciaKm"
    ]

    for columna in columnas_numericas:
        datos[columna] = pd.to_numeric(
            datos[columna],
            errors="coerce"
        ).fillna(0)

    datos = datos.dropna(subset=["Fecha"])

    return datos


try:
    df_original = cargar_datos()
except FileNotFoundError:
    st.error(
        "No se encontró el archivo fact_recoleccion.csv. "
        "Debe estar en la misma carpeta que app.py."
    )
    st.stop()
except Exception as error:
    st.error(f"Error al cargar el dataset: {error}")
    st.stop()

# =========================================================
# ENCABEZADO Y FILTROS
# =========================================================

encabezado, filtros = st.columns([1.08, 1.25], gap="large")

with encabezado:
    st.markdown(
        """
        <div class="titulo-dashboard">
            <h1>Dashboard Ejecutivo – Gestión de Residuos Sólidos</h1>
            <div class="linea-verde"></div>
        </div>
        """,
        unsafe_allow_html=True
    )

with filtros:
    filtro1, filtro2, filtro3 = st.columns([1, 1, 1.55])

    with filtro1:
        distrito_seleccionado = st.selectbox(
            "Distrito",
            ["Todos"] + sorted(
                df_original["Distrito"]
                .dropna()
                .astype(str)
                .unique()
                .tolist()
            )
        )

    with filtro2:
        residuo_seleccionado = st.selectbox(
            "Residuo",
            ["Todos"] + sorted(
                df_original["Residuo"]
                .dropna()
                .astype(str)
                .unique()
                .tolist()
            )
        )

    with filtro3:
        fecha_minima = df_original["Fecha"].min().date()
        fecha_maxima = df_original["Fecha"].max().date()

        rango_fechas = st.date_input(
            "Periodo",
            value=(fecha_minima, fecha_maxima),
            min_value=fecha_minima,
            max_value=fecha_maxima
        )

# =========================================================
# APLICACIÓN DE FILTROS
# =========================================================

df = df_original.copy()

if distrito_seleccionado != "Todos":
    df = df[df["Distrito"] == distrito_seleccionado]

if residuo_seleccionado != "Todos":
    df = df[df["Residuo"] == residuo_seleccionado]

if isinstance(rango_fechas, (tuple, list)) and len(rango_fechas) == 2:
    fecha_inicio = pd.Timestamp(rango_fechas[0])
    fecha_fin = pd.Timestamp(rango_fechas[1])

    df = df[
        (df["Fecha"] >= fecha_inicio)
        & (df["Fecha"] <= fecha_fin)
    ]

if df.empty:
    st.warning("No existen registros para los filtros seleccionados.")
    st.stop()

# =========================================================
# FUNCIONES
# =========================================================

def formato_decimal(valor, decimales=2):
    """
    Formato español:
    3.097,60
    """
    texto = f"{valor:,.{decimales}f}"
    return texto.replace(",", "X").replace(".", ",").replace("X", ".")


def tarjeta_kpi(icono, valor, etiqueta):
    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-icon">{icono}</div>
            <div class="kpi-value">{valor}</div>
            <div class="kpi-label">{etiqueta}</div>
        </div>
        """,
        unsafe_allow_html=True
    )


def crear_prediccion(
    datos,
    columna,
    operacion,
    titulo,
    unidad,
    color_linea
):
    serie = datos[["Fecha", columna]].copy()
    serie = serie.dropna()

    if operacion == "sum":
        serie = (
            serie.groupby("Fecha", as_index=False)[columna]
            .sum()
            .sort_values("Fecha")
        )
    else:
        serie = (
            serie.groupby("Fecha", as_index=False)[columna]
            .mean()
            .sort_values("Fecha")
        )

    if len(serie) < 2:
        figura = go.Figure()
        figura.add_annotation(
            text="No hay suficientes datos para predecir",
            showarrow=False
        )
        figura.update_layout(
            title=titulo,
            height=230
        )
        return figura

    fecha_base = serie["Fecha"].min()

    serie["Dia"] = (
        serie["Fecha"] - fecha_base
    ).dt.days

    x = serie[["Dia"]]
    y = serie[columna]

    modelo = LinearRegression()
    modelo.fit(x, y)

    ultima_fecha = serie["Fecha"].max()

    fechas_futuras = pd.date_range(
        start=ultima_fecha + pd.Timedelta(days=1),
        periods=30,
        freq="D"
    )

    dias_futuros = (
        fechas_futuras - fecha_base
    ).days.to_numpy().reshape(-1, 1)

    valores_futuros = modelo.predict(dias_futuros)

    if columna in ["Saturacion", "Quejas", "Toneladas"]:
        valores_futuros = np.maximum(valores_futuros, 0)

    if columna == "Saturacion":
        valores_futuros = np.minimum(valores_futuros, 100)

    prediccion = pd.DataFrame({
        "Fecha": fechas_futuras,
        columna: valores_futuros
    })

    figura = go.Figure()

    figura.add_trace(
        go.Scatter(
            x=serie["Fecha"],
            y=serie[columna],
            mode="lines",
            name="Histórico",
            line=dict(
                color=color_linea,
                width=1.5
            )
        )
    )

    figura.add_trace(
        go.Scatter(
            x=prediccion["Fecha"],
            y=prediccion[columna],
            mode="lines",
            name="Predicción",
            line=dict(
                color="#ff9f43",
                width=3,
                dash="dash"
            )
        )
    )

    figura.add_vline(
        x=ultima_fecha,
        line_dash="dot",
        line_color="#9ca3af"
    )

    figura.update_layout(
        title=dict(
            text=titulo,
            font=dict(size=16)
        ),
        xaxis_title="Fecha",
        yaxis_title=unidad,
        template="plotly_dark",
        height=235,
        margin=dict(l=20, r=20, t=45, b=20),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )

    return figura


# =========================================================
# TARJETAS KPI
# =========================================================

total_toneladas = df["Toneladas"].sum()
tiempo_promedio = df["TiempoRuta"].mean()
saturacion_promedio = df["Saturacion"].mean()
total_quejas = df["Quejas"].sum()
distancia_promedio = df["DistanciaKm"].mean()

kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)

with kpi1:
    tarjeta_kpi(
        "🚛",
        f"{formato_decimal(total_toneladas)} t",
        "Total Toneladas"
    )

with kpi2:
    tarjeta_kpi(
        "⏱️",
        f"{formato_decimal(tiempo_promedio)} min.",
        "Tiempo Prom. Ruta"
    )

with kpi3:
    tarjeta_kpi(
        "🗑️",
        f"{formato_decimal(saturacion_promedio)} %",
        "Saturación Prom."
    )

with kpi4:
    tarjeta_kpi(
        "⚠️",
        formato_decimal(total_quejas, 0),
        "Total Quejas"
    )

with kpi5:
    tarjeta_kpi(
        "🗺️",
        f"{formato_decimal(distancia_promedio)} km",
        "Distancia Prom."
    )

st.write("")

# =========================================================
# DISTRIBUCIÓN DEL DASHBOARD
# =========================================================

zona_principal, zona_predicciones = st.columns(
    [1.68, 1],
    gap="large"
)

# =========================================================
# COLUMNA IZQUIERDA
# =========================================================

with zona_principal:
    grafico1, grafico2 = st.columns(
        [1.15, 1],
        gap="large"
    )

    # TONELADAS POR DISTRITO
    with grafico1:
        toneladas_distrito = (
            df.groupby("Distrito", as_index=False)["Toneladas"]
            .sum()
            .sort_values("Toneladas", ascending=False)
        )

        fig_distrito = px.bar(
            toneladas_distrito,
            x="Distrito",
            y="Toneladas",
            title="Total Toneladas por distrito",
            text_auto=".2s"
        )

        fig_distrito.update_traces(
            marker_color="#24745d"
        )

        fig_distrito.update_layout(
            height=330,
            showlegend=False,
            paper_bgcolor="white",
            plot_bgcolor="white",
            margin=dict(l=20, r=20, t=50, b=20),
            xaxis_title="",
            yaxis_title="Toneladas"
        )

        fig_distrito.update_xaxes(
            tickangle=-35,
            showgrid=False
        )

        fig_distrito.update_yaxes(
            gridcolor="#e5e7eb"
        )

        st.plotly_chart(
            fig_distrito,
            use_container_width=True
        )

    # TONELADAS POR RESIDUO
    with grafico2:
        toneladas_residuo = (
            df.groupby("Residuo", as_index=False)["Toneladas"]
            .sum()
            .sort_values("Toneladas", ascending=False)
        )

        fig_residuo = px.pie(
            toneladas_residuo,
            names="Residuo",
            values="Toneladas",
            hole=0.52,
            title="Total Toneladas por residuo"
        )

        fig_residuo.update_traces(
            textposition="inside",
            textinfo="percent",
            hovertemplate=(
                "<b>%{label}</b><br>"
                "Toneladas: %{value:.2f}<br>"
                "Porcentaje: %{percent}<extra></extra>"
            )
        )

        fig_residuo.update_layout(
            height=330,
            paper_bgcolor="white",
            margin=dict(l=10, r=10, t=50, b=10),
            legend=dict(
                orientation="v",
                yanchor="middle",
                y=0.5,
                xanchor="left",
                x=1
            )
        )

        st.plotly_chart(
            fig_residuo,
            use_container_width=True
        )

    tabla_col, fecha_col = st.columns(
        [1, 1.08],
        gap="large"
    )

    # TABLA RESUMEN
    with tabla_col:
        tabla_resumen = (
            df.groupby("Residuo", as_index=False)
            .agg(
                Total_Toneladas=("Toneladas", "sum"),
                Total_Quejas=("Quejas", "sum")
            )
            .sort_values(
                "Total_Toneladas",
                ascending=False
            )
        )

        tabla_resumen["Total_Toneladas"] = (
            tabla_resumen["Total_Toneladas"]
            .round(2)
        )

        tabla_resumen["Total_Quejas"] = (
            tabla_resumen["Total_Quejas"]
            .round(0)
            .astype(int)
        )

        tabla_resumen = tabla_resumen.rename(
            columns={
                "Residuo": "Residuo",
                "Total_Toneladas": "Total Toneladas",
                "Total_Quejas": "Total Quejas"
            }
        )

        st.markdown("#### Resumen por residuo")

        st.dataframe(
            tabla_resumen,
            use_container_width=True,
            hide_index=True,
            height=335,
            column_config={
                "Total Toneladas": st.column_config.NumberColumn(
                    format="%.2f"
                ),
                "Total Quejas": st.column_config.NumberColumn(
                    format="%d"
                )
            }
        )

    # TONELADAS POR FECHA
    with fecha_col:
        toneladas_fecha = (
            df.groupby("Fecha", as_index=False)["Toneladas"]
            .sum()
            .sort_values("Fecha")
        )

        fig_fecha = px.line(
            toneladas_fecha,
            x="Fecha",
            y="Toneladas",
            title="Total Toneladas por fecha"
        )

        fig_fecha.update_traces(
            line=dict(
                color="#24745d",
                width=2
            ),
            fill="tozeroy"
        )

        fig_fecha.update_layout(
            height=380,
            paper_bgcolor="white",
            plot_bgcolor="white",
            margin=dict(l=20, r=20, t=50, b=25),
            xaxis_title="",
            yaxis_title="Toneladas"
        )

        fig_fecha.update_xaxes(
            showgrid=False
        )

        fig_fecha.update_yaxes(
            gridcolor="#e5e7eb"
        )

        st.plotly_chart(
            fig_fecha,
            use_container_width=True
        )

# =========================================================
# COLUMNA DERECHA: PREDICCIONES
# =========================================================

with zona_predicciones:
    fig_pred_toneladas = crear_prediccion(
        df,
        columna="Toneladas",
        operacion="sum",
        titulo="Predicción de Toneladas",
        unidad="Toneladas",
        color_linea="#27a9e1"
    )

    st.plotly_chart(
        fig_pred_toneladas,
        use_container_width=True
    )

    fig_pred_saturacion = crear_prediccion(
        df,
        columna="Saturacion",
        operacion="mean",
        titulo="Predicción de Saturación",
        unidad="Porcentaje",
        color_linea="#68c46a"
    )

    st.plotly_chart(
        fig_pred_saturacion,
        use_container_width=True
    )

    fig_pred_quejas = crear_prediccion(
        df,
        columna="Quejas",
        operacion="sum",
        titulo="Predicción de Quejas",
        unidad="Cantidad",
        color_linea="#d378e6"
    )

    st.plotly_chart(
        fig_pred_quejas,
        use_container_width=True
    )

# =========================================================
# DATOS DETALLADOS
# =========================================================

with st.expander("Ver registros detallados"):
    st.dataframe(
        df.sort_values("Fecha", ascending=False),
        use_container_width=True,
        hide_index=True
    )

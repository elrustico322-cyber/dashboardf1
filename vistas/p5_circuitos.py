import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

ROJO  = "#e10600"
CARD  = "#1a1a1a"
TEXTO = "#f0f0f0"
GRIS  = "#888888"

PLOTLY_LAYOUT = dict(
    paper_bgcolor=CARD,
    plot_bgcolor=CARD,
    font=dict(family="Roboto", color=TEXTO, size=12),
    margin=dict(l=16, r=16, t=40, b=16),
)


def mostrar(df_master, tablas):

    # ── ENCABEZADO ────────────────────────────────────────────────────────────
    st.markdown("""
    <div class="page-header">
        <div class="page-breadcrumb">FÓRMULA 1 · ANALYTICS</div>
        <div class="page-title">CIRCUITOS</div>
    </div>
    """, unsafe_allow_html=True)

    # ── FILTROS LATERALES ─────────────────────────────────────────────────────
    with st.sidebar:
        st.markdown("### 🔎 Filtros")

        años = sorted(tablas["races"]["year"].dropna().unique().astype(int))
        rango = st.select_slider(
            "Temporada", options=años,
            value=(min(años), max(años))
        )

        equipos_disp = sorted(df_master["constructor_name"].dropna().unique())
        equipo_sel = st.multiselect("Escudería", equipos_disp, placeholder="Todas")

    # Aplicar filtros
    df = df_master[
        (df_master["year"] >= rango[0]) &
        (df_master["year"] <= rango[1])
    ].copy()
    if equipo_sel:
        df = df[df["constructor_name"].isin(equipo_sel)]


    # ── KPI CARDS ─────────────────────────────────────────────────────────────
    total_circuitos = df["circuit_name"].nunique()
    paises          = df["country"].nunique()
    circuito_activo = (
        df.groupby("circuit_name")["raceId"].nunique()
        .idxmax()
    )
    carreras_max = int(df.groupby("circuit_name")["raceId"].nunique().max())

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-value">{total_circuitos}</div>
            <div class="kpi-label">Circuitos Únicos</div>
            <div class="kpi-sub">En el período seleccionado</div>
        </div>""", unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-value">{paises}</div>
            <div class="kpi-label">Países</div>
            <div class="kpi-sub">Con al menos un GP</div>
        </div>""", unsafe_allow_html=True)

    with col3:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-value">{carreras_max}</div>
            <div class="kpi-label">Carreras · Circuito Más Usado</div>
            <div class="kpi-sub">{circuito_activo}</div>
        </div>""", unsafe_allow_html=True)

    st.markdown('<div class="red-divider"></div>', unsafe_allow_html=True)


    # ── MAPA MUNDIAL ──────────────────────────────────────────────────────────
    st.markdown('<div class="section-title">Mapa Mundial de Circuitos</div>',
                unsafe_allow_html=True)
    st.markdown('<div class="section-sub">Tamaño del punto = carreras realizadas · color = victorias del equipo dominante</div>',
                unsafe_allow_html=True)

    # Datos por circuito
    circuitos_info = tablas["circuits"][["circuitId", "name", "country", "lat", "lng"]].copy()
    circuitos_info["lat"] = pd.to_numeric(circuitos_info["lat"], errors="coerce")
    circuitos_info["lng"] = pd.to_numeric(circuitos_info["lng"], errors="coerce")

    carreras_por_circuito = (
        df.groupby("circuit_name")
        .agg(
            carreras  =("raceId",    "nunique"),
            victorias =("is_win",    "sum"),
        )
        .reset_index()
    )

    # Constructor dominante por circuito
    dominante = (
        df[df["is_win"] == 1]
        .groupby(["circuit_name", "constructor_name"])["is_win"].sum()
        .reset_index()
    )
    dominante = (
        dominante.loc[dominante.groupby("circuit_name")["is_win"].idxmax()]
        .rename(columns={"constructor_name": "equipo_dominante", "is_win": "victorias_dominante"})
    )

    df_mapa = (
        carreras_por_circuito
        .merge(dominante[["circuit_name", "equipo_dominante", "victorias_dominante"]],
               on="circuit_name", how="left")
        .merge(circuitos_info.rename(columns={"name": "circuit_name"})[
                   ["circuit_name", "lat", "lng", "country"]],
               on="circuit_name", how="left")
        .dropna(subset=["lat", "lng"])
    )

    fig_mapa = px.scatter_geo(
        df_mapa,
        lat="lat", lon="lng",
        size="carreras",
        color="equipo_dominante",
        hover_name="circuit_name",
        hover_data={
            "country":            True,
            "carreras":           True,
            "equipo_dominante":   True,
            "victorias_dominante":True,
            "lat":                False,
            "lng":                False,
        },
        size_max=20,
        color_discrete_sequence=[
            ROJO, "#ff6b6b", "#ffffff", "#aaaaaa",
            "#0088ff", "#00cc44", "#ffaa00", "#aa00ff",
            "#00cccc", "#ff6600"
        ],
        projection="natural earth",
    )
    fig_mapa.update_geos(
        bgcolor=CARD,
        landcolor="#1e1e1e",
        oceancolor="#0a0a0a",
        showocean=True,
        showland=True,
        showcountries=True,
        countrycolor="#333",
        showcoastlines=True,
        coastlinecolor="#333",
        framecolor="#333",
    )
    fig_mapa.update_layout(
        **PLOTLY_LAYOUT,
        height=480,
        geo=dict(bgcolor=CARD),
        legend=dict(
            orientation="v",
            bgcolor="rgba(0,0,0,0.5)",
            font=dict(color=TEXTO, size=10),
            title=dict(text="Equipo Dominante", font=dict(color=GRIS))
        ),
    )
    st.plotly_chart(fig_mapa, use_container_width=True)

    st.markdown('<div class="red-divider"></div>', unsafe_allow_html=True)


    # ── FILA: Carreras por circuito + Ganadores históricos ────────────────────
    col_izq, col_der = st.columns([1, 1])

    with col_izq:
        st.markdown('<div class="section-title">Carreras Realizadas por Circuito</div>',
                    unsafe_allow_html=True)
        st.markdown('<div class="section-sub">Top 20 circuitos con más GPs</div>',
                    unsafe_allow_html=True)

        top_circuitos = (
            df.groupby("circuit_name")["raceId"].nunique()
            .nlargest(20).reset_index()
            .sort_values("raceId")
            .rename(columns={"raceId": "Carreras", "circuit_name": "Circuito"})
        )

        fig_circ = px.bar(
            top_circuitos,
            x="Carreras", y="Circuito",
            orientation="h",
            color="Carreras",
            color_continuous_scale=[[0, "#001a33"], [1, "#0088ff"]],
            labels={"Circuito": ""}
        )
        fig_circ.update_layout(
            **PLOTLY_LAYOUT, height=500,
            showlegend=False, coloraxis_showscale=False,
            xaxis=dict(gridcolor="#222", tickfont=dict(color=GRIS)),
            yaxis=dict(gridcolor="rgba(0,0,0,0)", tickfont=dict(color=TEXTO, size=11)),
        )
        st.plotly_chart(fig_circ, use_container_width=True)

    with col_der:
        st.markdown('<div class="section-title">Escudería Dominante por Circuito</div>',
                    unsafe_allow_html=True)
        st.markdown('<div class="section-sub">Equipo con más victorias en cada pista · Top 20</div>',
                    unsafe_allow_html=True)

        dom_top20 = df_mapa.nlargest(20, "victorias_dominante")[
            ["circuit_name", "country", "equipo_dominante", "victorias_dominante", "carreras"]
        ].rename(columns={
            "circuit_name":        "Circuito",
            "country":             "País",
            "equipo_dominante":    "Escudería Dominante",
            "victorias_dominante": "Victorias",
            "carreras":            "GPs Totales",
        }).reset_index(drop=True)

        st.dataframe(
            dom_top20,
            use_container_width=True,
            hide_index=True,
            height=500,
            column_config={
                "Victorias":   st.column_config.NumberColumn(format="%d"),
                "GPs Totales": st.column_config.NumberColumn(format="%d"),
            }
        )

    st.markdown('<div class="red-divider"></div>', unsafe_allow_html=True)


    # ── DETALLE CIRCUITO SELECCIONADO ─────────────────────────────────────────
    st.markdown('<div class="section-title">Detalle por Circuito</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">Selecciona un circuito para ver sus ganadores históricos</div>',
                unsafe_allow_html=True)

    circuitos_lista = sorted(df["circuit_name"].dropna().unique())
    circuito_sel = st.selectbox("Circuito", circuitos_lista)

    df_circ = df[df["circuit_name"] == circuito_sel]

    col_a, col_b = st.columns(2)

    with col_a:
        ganadores = (
            df_circ[df_circ["is_win"] == 1]
            .groupby("driver_name")["is_win"].sum()
            .nlargest(10).reset_index()
            .sort_values("is_win")
            .rename(columns={"driver_name": "Piloto", "is_win": "Victorias"})
        )

        fig_gan = px.bar(
            ganadores, x="Victorias", y="Piloto",
            orientation="h",
            color="Victorias",
            color_continuous_scale=[[0, "#3a0000"], [1, ROJO]],
            labels={"Piloto": ""}
        )
        fig_gan.update_layout(
            **PLOTLY_LAYOUT, height=300,
            title=dict(text="Pilotos más ganadores", font=dict(color=TEXTO, size=14)),
            showlegend=False, coloraxis_showscale=False,
            xaxis=dict(gridcolor="#222", tickfont=dict(color=GRIS)),
            yaxis=dict(gridcolor="rgba(0,0,0,0)", tickfont=dict(color=TEXTO)),
        )
        st.plotly_chart(fig_gan, use_container_width=True)

    with col_b:
        equipos_circ = (
            df_circ[df_circ["is_win"] == 1]
            .groupby("constructor_name")["is_win"].sum()
            .nlargest(10).reset_index()
            .sort_values("is_win")
            .rename(columns={"constructor_name": "Escudería", "is_win": "Victorias"})
        )

        fig_eq = px.bar(
            equipos_circ, x="Victorias", y="Escudería",
            orientation="h",
            color="Victorias",
            color_continuous_scale=[[0, "#001a33"], [1, "#0088ff"]],
            labels={"Escudería": ""}
        )
        fig_eq.update_layout(
            **PLOTLY_LAYOUT, height=300,
            title=dict(text="Escuderías más ganadoras", font=dict(color=TEXTO, size=14)),
            showlegend=False, coloraxis_showscale=False,
            xaxis=dict(gridcolor="#222", tickfont=dict(color=GRIS)),
            yaxis=dict(gridcolor="rgba(0,0,0,0)", tickfont=dict(color=TEXTO)),
        )
        st.plotly_chart(fig_eq, use_container_width=True)
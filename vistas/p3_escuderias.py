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
        <div class="page-title">ESCUDERÍAS</div>
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
    total_equipos   = df["constructor_name"].nunique()
    total_victorias = int(df["is_win"].sum())
    equipo_lider    = df.groupby("constructor_name")["is_win"].sum().idxmax()
    victorias_lider = int(df.groupby("constructor_name")["is_win"].sum().max())

    pts_por_carrera = (
        df.groupby("constructor_name")["points"].sum() /
        df.groupby("constructor_name")["raceId"].nunique()
    )
    equipo_eficiente = pts_por_carrera.idxmax()

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-value">{total_equipos}</div>
            <div class="kpi-label">Escuderías Activas</div>
            <div class="kpi-sub">En el período seleccionado</div>
        </div>""", unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-value">{victorias_lider}</div>
            <div class="kpi-label">Victorias · Líder</div>
            <div class="kpi-sub">{equipo_lider}</div>
        </div>""", unsafe_allow_html=True)

    with col3:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-value">{round(pts_por_carrera.max(), 1)}</div>
            <div class="kpi-label">Pts/Carrera · Más Eficiente</div>
            <div class="kpi-sub">{equipo_eficiente}</div>
        </div>""", unsafe_allow_html=True)

    st.markdown('<div class="red-divider"></div>', unsafe_allow_html=True)


    # ── FILA 1: Victorias por equipo + Participaciones ────────────────────────
    col1, col2 = st.columns(2)

    with col1:
        st.markdown('<div class="section-title">Victorias por Escudería</div>',
                    unsafe_allow_html=True)
        st.markdown('<div class="section-sub">Top 15 equipos con más victorias</div>',
                    unsafe_allow_html=True)

        top_vic = (
            df.groupby("constructor_name")["is_win"].sum()
            .nlargest(15).reset_index()
            .sort_values("is_win")
        )

        fig_vic = px.bar(
            top_vic, x="is_win", y="constructor_name",
            orientation="h",
            labels={"is_win": "Victorias", "constructor_name": ""},
            color="is_win",
            color_continuous_scale=[[0, "#3a0000"], [1, ROJO]],
        )
        fig_vic.update_layout(
            **PLOTLY_LAYOUT, height=420,
            showlegend=False, coloraxis_showscale=False,
            xaxis=dict(gridcolor="#222", tickfont=dict(color=GRIS)),
            yaxis=dict(gridcolor="rgba(0,0,0,0)", tickfont=dict(color=TEXTO)),
        )
        st.plotly_chart(fig_vic, use_container_width=True)

    with col2:
        st.markdown('<div class="section-title">Participaciones por Escudería</div>',
                    unsafe_allow_html=True)
        st.markdown('<div class="section-sub">Top 15 equipos con más carreras disputadas</div>',
                    unsafe_allow_html=True)

        top_part = (
            df.groupby("constructor_name")["raceId"].nunique()
            .nlargest(15).reset_index()
            .sort_values("raceId")
            .rename(columns={"raceId": "Carreras"})
        )

        fig_part = px.bar(
            top_part, x="Carreras", y="constructor_name",
            orientation="h",
            labels={"constructor_name": ""},
            color="Carreras",
            color_continuous_scale=[[0, "#001a33"], [1, "#0088ff"]],
        )
        fig_part.update_layout(
            **PLOTLY_LAYOUT, height=420,
            showlegend=False, coloraxis_showscale=False,
            xaxis=dict(gridcolor="#222", tickfont=dict(color=GRIS)),
            yaxis=dict(gridcolor="rgba(0,0,0,0)", tickfont=dict(color=TEXTO)),
        )
        st.plotly_chart(fig_part, use_container_width=True)

    st.markdown('<div class="red-divider"></div>', unsafe_allow_html=True)


    # ── FILA 2: Rendimiento histórico ─────────────────────────────────────────
    st.markdown('<div class="section-title">Rendimiento Histórico</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">Puntos por temporada · Top 6 escuderías</div>',
                unsafe_allow_html=True)

    top6 = (
        df.groupby("constructor_name")["points"].sum()
        .nlargest(6).index.tolist()
    )

    df_hist = (
        df[df["constructor_name"].isin(top6)]
        .groupby(["year", "constructor_name"])["points"]
        .sum().reset_index()
    )

    fig_hist = px.area(
        df_hist, x="year", y="points",
        color="constructor_name",
        labels={"year": "Temporada", "points": "Puntos", "constructor_name": "Escudería"},
        color_discrete_sequence=[ROJO, "#ff6b6b", "#ffffff", "#aaaaaa", "#0088ff", "#00cc44"]
    )
    fig_hist.update_traces(opacity=0.6)
    fig_hist.update_layout(
        **PLOTLY_LAYOUT, height=320,
        legend=dict(
            orientation="h", yanchor="bottom", y=1.02,
            bgcolor="rgba(0,0,0,0)", font=dict(color=TEXTO, size=11)
        ),
        xaxis=dict(gridcolor="#222", tickfont=dict(color=GRIS)),
        yaxis=dict(gridcolor="#222", tickfont=dict(color=GRIS)),
    )
    st.plotly_chart(fig_hist, use_container_width=True)

    st.markdown('<div class="red-divider"></div>', unsafe_allow_html=True)


    # ── TABLA DETALLE ─────────────────────────────────────────────────────────
    st.markdown('<div class="section-title">Tabla Detalle · Escuderías</div>',
                unsafe_allow_html=True)
    st.markdown('<div class="section-sub">Estadísticas completas en el período seleccionado</div>',
                unsafe_allow_html=True)

    tabla = (
        df.groupby(["constructor_name", "constructor_nationality"])
        .agg(
            Carreras  =("raceId",    "nunique"),
            Victorias =("is_win",    "sum"),
            Podios    =("is_podium", "sum"),
            Puntos    =("points",    "sum"),
        )
        .reset_index()
        .rename(columns={
            "constructor_name":        "Escudería",
            "constructor_nationality": "Nacionalidad"
        })
        .sort_values("Victorias", ascending=False)
        .reset_index(drop=True)
    )
    tabla["Pts/Carrera"] = (tabla["Puntos"] / tabla["Carreras"]).round(1)
    tabla["Win Rate %"]  = (tabla["Victorias"] / tabla["Carreras"] * 100).round(1)
    tabla = tabla.drop(columns=["Puntos"])

    st.dataframe(
        tabla,
        use_container_width=True,
        hide_index=True,
        height=400,
        column_config={
            "Victorias":   st.column_config.NumberColumn(format="%d"),
            "Podios":      st.column_config.NumberColumn(format="%d"),
            "Pts/Carrera": st.column_config.NumberColumn(format="%.1f"),
            "Win Rate %":  st.column_config.ProgressColumn(
                format="%.1f%%", min_value=0, max_value=100
            ),
        }
    )
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

# ── Colores globales ──────────────────────────────────────────────────────────
ROJO    = "#e10600"
FONDO   = "#0f0f0f"
CARD    = "#1a1a1a"
TEXTO   = "#f0f0f0"
GRIS    = "#888888"

PLOTLY_LAYOUT = dict(
    paper_bgcolor=CARD,
    plot_bgcolor=CARD,
    font=dict(family="Roboto", color=TEXTO, size=12),
    margin=dict(l=16, r=16, t=40, b=16),
    colorway=[ROJO, "#ff6b6b", "#ff9e9e", "#ffd0d0",
              "#ffffff", "#aaaaaa", "#666666"],
)


def mostrar(df_master, tablas):

    # ── ENCABEZADO ────────────────────────────────────────────────────────────
    st.markdown("""
    <div class="page-header">
        <div class="page-breadcrumb">FÓRMULA 1 · ANALYTICS</div>
        <div class="page-title">RESUMEN EJECUTIVO</div>
    </div>
    """, unsafe_allow_html=True)


    # ── FILTROS LATERALES ─────────────────────────────────────────────────────
    with st.sidebar:
        st.markdown("### 🔎 Filtros")

        años = sorted(tablas["races"]["year"].dropna().unique().astype(int))
        rango = st.select_slider(
            "Temporada",
            options=años,
            value=(min(años), max(años))
        )

        pilotos_disp = sorted(df_master["driver_name"].dropna().unique())
        piloto_sel = st.multiselect("Piloto", pilotos_disp, placeholder="Todos")

        equipos_disp = sorted(df_master["constructor_name"].dropna().unique())
        equipo_sel = st.multiselect("Escudería", equipos_disp, placeholder="Todas")

        circuitos_disp = sorted(df_master["circuit_name"].dropna().unique())
        circuito_sel = st.multiselect("Circuito", circuitos_disp, placeholder="Todos")

    # Aplicar filtros
    df = df_master[
        (df_master["year"] >= rango[0]) &
        (df_master["year"] <= rango[1])
    ].copy()
    if piloto_sel:
        df = df[df["driver_name"].isin(piloto_sel)]
    if equipo_sel:
        df = df[df["constructor_name"].isin(equipo_sel)]
    if circuito_sel:
        df = df[df["circuit_name"].isin(circuito_sel)]


    # ── KPI CARDS ─────────────────────────────────────────────────────────────
    total_carreras  = df["raceId"].nunique()
    total_victorias = int(df["is_win"].sum())
    total_podios    = int(df["is_podium"].sum())

    # Tasa pole → victoria
    poles = df[df["grid"] == 1]
    tasa_pole = round(poles["is_win"].sum() / len(poles) * 100, 1) if len(poles) > 0 else 0

    # Puntos promedio por carrera (top constructor del periodo)
    pts_constructor = (
        df.groupby("constructor_name")["points"].sum() /
        df.groupby("constructor_name")["raceId"].nunique()
    ).round(1)
    top_constructor = pts_constructor.idxmax() if len(pts_constructor) > 0 else "-"
    pts_max = pts_constructor.max() if len(pts_constructor) > 0 else 0

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-value">{total_carreras}</div>
            <div class="kpi-label">Carreras Analizadas</div>
            <div class="kpi-sub">{rango[0]} – {rango[1]}</div>
        </div>""", unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-value">{total_victorias}</div>
            <div class="kpi-label">Victorias Registradas</div>
            <div class="kpi-sub">Posición final = 1</div>
        </div>""", unsafe_allow_html=True)

    with col3:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-value">{tasa_pole}%</div>
            <div class="kpi-label">Tasa Pole → Victoria</div>
            <div class="kpi-sub">{len(poles)} poles en el período</div>
        </div>""", unsafe_allow_html=True)

    with col4:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-value">{pts_max}</div>
            <div class="kpi-label">Pts / Carrera · Líder</div>
            <div class="kpi-sub">{top_constructor}</div>
        </div>""", unsafe_allow_html=True)

    st.markdown('<div class="red-divider"></div>', unsafe_allow_html=True)


    # ── GRÁFICO PRINCIPAL: victorias por año ──────────────────────────────────
    st.markdown('<div class="section-title">Victorias por Temporada</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">Top 5 constructores · evolución histórica</div>',
                unsafe_allow_html=True)

    top5 = (
        df.groupby("constructor_name")["is_win"].sum()
        .nlargest(5).index.tolist()
    )

    df_linea = (
        df[df["constructor_name"].isin(top5)]
        .groupby(["year", "constructor_name"])["is_win"].sum()
        .reset_index()
    )

    fig_linea = px.line(
        df_linea,
        x="year", y="is_win",
        color="constructor_name",
        markers=True,
        labels={"year": "Temporada", "is_win": "Victorias", "constructor_name": "Escudería"},
        color_discrete_sequence=[ROJO, "#ff6b6b", "#ffffff", "#aaaaaa", "#555555"]
    )
    fig_linea.update_layout(
        **PLOTLY_LAYOUT,
        height=340,
        legend=dict(
            orientation="h", yanchor="bottom", y=1.02,
            bgcolor="rgba(0,0,0,0)", font=dict(color=TEXTO, size=11)
        ),
        xaxis=dict(gridcolor="#222", tickfont=dict(color=GRIS)),
        yaxis=dict(gridcolor="#222", tickfont=dict(color=GRIS)),
    )
    st.plotly_chart(fig_linea, use_container_width=True)

    st.markdown('<div class="red-divider"></div>', unsafe_allow_html=True)


    # ── FILA INFERIOR: barras + tabla ─────────────────────────────────────────
    col_izq, col_der = st.columns([1, 1])

    with col_izq:
        st.markdown('<div class="section-title">Top 10 Pilotos</div>', unsafe_allow_html=True)
        st.markdown('<div class="section-sub">Por victorias en el período seleccionado</div>',
                    unsafe_allow_html=True)

        top_pilotos = (
            df.groupby("driver_name")["is_win"].sum()
            .nlargest(10).reset_index()
            .sort_values("is_win")
        )

        fig_bar = px.bar(
            top_pilotos,
            x="is_win", y="driver_name",
            orientation="h",
            labels={"is_win": "Victorias", "driver_name": ""},
            color="is_win",
            color_continuous_scale=[[0, "#3a0000"], [1, ROJO]],
        )
        fig_bar.update_layout(
            **PLOTLY_LAYOUT,
            height=340,
            showlegend=False,
            coloraxis_showscale=False,
            xaxis=dict(gridcolor="#222", tickfont=dict(color=GRIS)),
            yaxis=dict(gridcolor="rgba(0,0,0,0)", tickfont=dict(color=TEXTO)),
        )
        st.plotly_chart(fig_bar, use_container_width=True)

    with col_der:
        st.markdown('<div class="section-title">Tabla Resumen</div>', unsafe_allow_html=True)
        st.markdown('<div class="section-sub">Estadísticas agregadas por escudería</div>',
                    unsafe_allow_html=True)

        tabla_res = (
            df.groupby("constructor_name")
            .agg(
                Carreras=("raceId",     "nunique"),
                Victorias=("is_win",    "sum"),
                Podios=("is_podium",    "sum"),
                Puntos=("points",       "sum"),
            )
            .reset_index()
            .rename(columns={"constructor_name": "Escudería"})
            .sort_values("Victorias", ascending=False)
            .head(10)
            .reset_index(drop=True)
        )
        tabla_res["Pts/Carrera"] = (tabla_res["Puntos"] / tabla_res["Carreras"]).round(1)
        tabla_res = tabla_res.drop(columns=["Puntos"])

        st.dataframe(
            tabla_res,
            use_container_width=True,
            hide_index=True,
            height=320,
            column_config={
                "Victorias":   st.column_config.NumberColumn(format="%d"),
                "Podios":      st.column_config.NumberColumn(format="%d"),
                "Pts/Carrera": st.column_config.NumberColumn(format="%.1f"),
            }
        )

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
        <div class="page-title">PILOTOS</div>
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

        nacionalidades = sorted(df_master["driver_nationality"].dropna().unique())
        nac_sel = st.multiselect("Nacionalidad", nacionalidades, placeholder="Todas")

    # Aplicar filtros
    df = df_master[
        (df_master["year"] >= rango[0]) &
        (df_master["year"] <= rango[1])
    ].copy()
    if equipo_sel:
        df = df[df["constructor_name"].isin(equipo_sel)]
    if nac_sel:
        df = df[df["driver_nationality"].isin(nac_sel)]


    # ── FILA 1: Top victorias + Top podios ────────────────────────────────────
    col1, col2 = st.columns(2)

    with col1:
        st.markdown('<div class="section-title">Top 15 · Victorias</div>', unsafe_allow_html=True)
        st.markdown('<div class="section-sub">Pilotos con más primeros lugares</div>',
                    unsafe_allow_html=True)

        top_vic = (
            df.groupby("driver_name")["is_win"].sum()
            .nlargest(15).reset_index()
            .sort_values("is_win")
        )

        fig_vic = px.bar(
            top_vic, x="is_win", y="driver_name",
            orientation="h",
            labels={"is_win": "Victorias", "driver_name": ""},
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
        st.markdown('<div class="section-title">Top 15 · Podios</div>', unsafe_allow_html=True)
        st.markdown('<div class="section-sub">Pilotos con más llegadas al podio</div>',
                    unsafe_allow_html=True)

        top_pod = (
            df.groupby("driver_name")["is_podium"].sum()
            .nlargest(15).reset_index()
            .sort_values("is_podium")
        )

        fig_pod = px.bar(
            top_pod, x="is_podium", y="driver_name",
            orientation="h",
            labels={"is_podium": "Podios", "driver_name": ""},
            color="is_podium",
            color_continuous_scale=[[0, "#1a1a3a"], [1, "#4444ff"]],
        )
        fig_pod.update_layout(
            **PLOTLY_LAYOUT, height=420,
            showlegend=False, coloraxis_showscale=False,
            xaxis=dict(gridcolor="#222", tickfont=dict(color=GRIS)),
            yaxis=dict(gridcolor="rgba(0,0,0,0)", tickfont=dict(color=TEXTO)),
        )
        st.plotly_chart(fig_pod, use_container_width=True)

    st.markdown('<div class="red-divider"></div>', unsafe_allow_html=True)


    # ── FILA 2: Evolución de puntos + Nacionalidades ───────────────────────────
    col3, col4 = st.columns([3, 2])

    with col3:
        st.markdown('<div class="section-title">Evolución de Puntos</div>', unsafe_allow_html=True)
        st.markdown('<div class="section-sub">Top 5 pilotos · puntos acumulados por temporada</div>',
                    unsafe_allow_html=True)

        top5_pilotos = (
            df.groupby("driver_name")["points"].sum()
            .nlargest(5).index.tolist()
        )

        df_evol = (
            df[df["driver_name"].isin(top5_pilotos)]
            .groupby(["year", "driver_name"])["points"]
            .sum().reset_index()
        )

        fig_evol = px.line(
            df_evol, x="year", y="points",
            color="driver_name", markers=True,
            labels={"year": "Temporada", "points": "Puntos", "driver_name": "Piloto"},
            color_discrete_sequence=[ROJO, "#ff6b6b", "#ffffff", "#aaaaaa", "#555555"]
        )
        fig_evol.update_layout(
            **PLOTLY_LAYOUT, height=340,
            legend=dict(
                orientation="h", yanchor="bottom", y=1.02,
                bgcolor="rgba(0,0,0,0)", font=dict(color=TEXTO, size=11)
            ),
            xaxis=dict(gridcolor="#222", tickfont=dict(color=GRIS)),
            yaxis=dict(gridcolor="#222", tickfont=dict(color=GRIS)),
        )
        st.plotly_chart(fig_evol, use_container_width=True)

    with col4:
        st.markdown('<div class="section-title">Victorias por Nacionalidad</div>',
                    unsafe_allow_html=True)
        st.markdown('<div class="section-sub">Top 10 países</div>', unsafe_allow_html=True)

        nac_vic = (
            df[df["is_win"] == 1]
            .groupby("driver_nationality")["is_win"].sum()
            .nlargest(10).reset_index()
            .sort_values("is_win")
            .rename(columns={"driver_nationality": "País", "is_win": "Victorias"})
        )

        fig_nac = px.bar(
            nac_vic, x="Victorias", y="País",
            orientation="h",
            color="Victorias",
            color_continuous_scale=[[0, "#1a2a1a"], [1, "#00cc44"]],
            labels={"País": ""}
        )
        fig_nac.update_layout(
            **PLOTLY_LAYOUT, height=340,
            showlegend=False, coloraxis_showscale=False,
            xaxis=dict(gridcolor="#222", tickfont=dict(color=GRIS)),
            yaxis=dict(gridcolor="rgba(0,0,0,0)", tickfont=dict(color=TEXTO)),
        )
        st.plotly_chart(fig_nac, use_container_width=True)

    st.markdown('<div class="red-divider"></div>', unsafe_allow_html=True)


    # ── TABLA DETALLE ─────────────────────────────────────────────────────────
    st.markdown('<div class="section-title">Tabla Detalle · Pilotos</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">Estadísticas completas en el período seleccionado</div>',
                unsafe_allow_html=True)

    tabla_pilotos = (
        df.groupby(["driver_name", "driver_nationality"])
        .agg(
            Carreras  =("raceId",     "nunique"),
            Victorias =("is_win",     "sum"),
            Podios    =("is_podium",  "sum"),
            Puntos    =("points",     "sum"),
        )
        .reset_index()
        .rename(columns={
            "driver_name":        "Piloto",
            "driver_nationality": "Nacionalidad"
        })
        .sort_values("Victorias", ascending=False)
        .reset_index(drop=True)
    )
    tabla_pilotos["Pts/Carrera"] = (
        tabla_pilotos["Puntos"] / tabla_pilotos["Carreras"]
    ).round(1)
    tabla_pilotos["Win Rate %"] = (
        tabla_pilotos["Victorias"] / tabla_pilotos["Carreras"] * 100
    ).round(1)
    tabla_pilotos = tabla_pilotos.drop(columns=["Puntos"])

    st.dataframe(
        tabla_pilotos,
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
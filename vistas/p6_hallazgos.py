import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np

ROJO   = "#e10600"
CARD   = "#1a1a1a"
TEXTO  = "#f0f0f0"
GRIS   = "#888888"
VERDE  = "#00cc44"
AZUL   = "#0088ff"
AMBAR  = "#ffaa00"

PLOTLY_LAYOUT = dict(
    paper_bgcolor=CARD,
    plot_bgcolor=CARD,
    font=dict(family="Roboto", color=TEXTO, size=12),
    margin=dict(l=16, r=16, t=40, b=16),
)


def hallazgo_card(numero, titulo, valor, descripcion, color=ROJO):
    st.markdown(f"""
    <div style="background:{CARD}; border:1px solid #2a2a2a;
                border-left:4px solid {color}; border-radius:6px;
                padding:16px 20px; margin-bottom:12px;">
        <div style="color:{GRIS}; font-size:11px; letter-spacing:2px;
                    text-transform:uppercase; margin-bottom:4px;">
            HALLAZGO {numero}
        </div>
        <div style="color:{TEXTO}; font-size:15px; font-weight:700;
                    margin-bottom:8px;">
            {titulo}
        </div>
        <div style="color:{color}; font-size:28px; font-weight:700;
                    font-variant-numeric:tabular-nums; margin-bottom:6px;">
            {valor}
        </div>
        <div style="color:{GRIS}; font-size:13px; line-height:1.5;">
            {descripcion}
        </div>
    </div>
    """, unsafe_allow_html=True)


def mostrar(df_master, tablas):

    # ── ENCABEZADO ────────────────────────────────────────────────────────────
    st.markdown("""
    <div class="page-header">
        <div class="page-breadcrumb">FÓRMULA 1 · ANALYTICS</div>
        <div class="page-title">HALLAZGOS Y CONCLUSIONES</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div style="background:#1a1a1a; border-left:4px solid #e10600;
                padding:12px 16px; border-radius:4px; margin-bottom:24px;">
        <span style="color:#888; font-size:13px;">
        Conclusiones analíticas derivadas del dataset histórico de Fórmula 1 (1950–2024).
        Cada hallazgo responde directamente a las preguntas de negocio planteadas.
        </span>
    </div>
    """, unsafe_allow_html=True)

    # Filtro de período en sidebar
    with st.sidebar:
        st.markdown("### 🔎 Filtros")
        años = sorted(tablas["races"]["year"].dropna().unique().astype(int))
        rango = st.select_slider(
            "Temporada", options=años,
            value=(min(años), max(años))
        )

    df = df_master[
        (df_master["year"] >= rango[0]) &
        (df_master["year"] <= rango[1])
    ].copy()


    # ── CALCULAR TODOS LOS STATS ──────────────────────────────────────────────

    # Pole → Victoria
    poles          = df[df["grid"] == 1]
    tasa_pole      = round(poles["is_win"].mean() * 100, 1) if len(poles) > 0 else 0

    # % victorias desde top 3
    total_wins     = int(df["is_win"].sum())
    wins_top3      = int(df[df["grid"] <= 3]["is_win"].sum())
    pct_wins_top3  = round(wins_top3 / total_wins * 100, 1) if total_wins > 0 else 0

    # Constructor dominante histórico
    top_constructor = df.groupby("constructor_name")["is_win"].sum().idxmax()
    wins_top_const  = int(df.groupby("constructor_name")["is_win"].sum().max())

    # Piloto más ganador
    top_piloto      = df.groupby("driver_name")["is_win"].sum().idxmax()
    wins_top_piloto = int(df.groupby("driver_name")["is_win"].sum().max())

    # Circuito más dominado
    dom_circuito = (
        df[df["is_win"] == 1]
        .groupby(["circuit_name", "constructor_name"])["is_win"].sum()
        .reset_index()
    )
    if len(dom_circuito) > 0:
        idx = dom_circuito["is_win"].idxmax()
        circ_dom      = dom_circuito.loc[idx, "circuit_name"]
        equipo_dom    = dom_circuito.loc[idx, "constructor_name"]
        wins_circ_dom = int(dom_circuito.loc[idx, "is_win"])
    else:
        circ_dom, equipo_dom, wins_circ_dom = "-", "-", 0

    # Tendencia pole última década vs anterior
    df_reciente  = df[df["year"] >= (rango[1] - 10)]
    df_anterior  = df[(df["year"] < (rango[1] - 10)) & (df["year"] >= (rango[1] - 20))]
    tasa_pole_rec = round(df_reciente[df_reciente["grid"] == 1]["is_win"].mean() * 100, 1) \
                    if len(df_reciente[df_reciente["grid"] == 1]) > 0 else 0
    tasa_pole_ant = round(df_anterior[df_anterior["grid"] == 1]["is_win"].mean() * 100, 1) \
                    if len(df_anterior[df_anterior["grid"] == 1]) > 0 else 0
    delta_pole    = round(tasa_pole_rec - tasa_pole_ant, 1)
    signo         = "+" if delta_pole >= 0 else ""


    # ── SECCIÓN 1: PREGUNTA 1 — Pilotos y equipos más exitosos ───────────────
    st.markdown('<div class="section-title">① ¿Cuáles son los pilotos y equipos más exitosos?</div>',
                unsafe_allow_html=True)
    st.markdown('<div class="red-divider"></div>', unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        hallazgo_card(
            "1A", f"El piloto más ganador es {top_piloto}",
            f"{wins_top_piloto} victorias",
            f"En el período {rango[0]}–{rango[1]}, {top_piloto} acumula más victorias "
            f"que cualquier otro piloto en el dataset.",
            color=ROJO
        )

        # Mini gráfico top 5 pilotos
        top5_p = (
            df.groupby("driver_name")["is_win"].sum()
            .nlargest(5).reset_index().sort_values("is_win")
        )
        fig_p = px.bar(top5_p, x="is_win", y="driver_name", orientation="h",
                       color="is_win",
                       color_continuous_scale=[[0,"#3a0000"],[1,ROJO]],
                       labels={"is_win":"Victorias","driver_name":""})
        fig_p.update_layout(**PLOTLY_LAYOUT, height=200, showlegend=False,
                            coloraxis_showscale=False,
                            xaxis=dict(gridcolor="#222", tickfont=dict(color=GRIS)),
                            yaxis=dict(gridcolor="rgba(0,0,0,0)", tickfont=dict(color=TEXTO)))
        st.plotly_chart(fig_p, use_container_width=True)

    with col2:
        hallazgo_card(
            "1B", f"La escudería dominante es {top_constructor}",
            f"{wins_top_const} victorias",
            f"{top_constructor} lidera el campeonato de constructores histórico "
            f"en el período seleccionado con la mayor cantidad de victorias.",
            color=AZUL
        )

        # Mini gráfico top 5 constructores
        top5_c = (
            df.groupby("constructor_name")["is_win"].sum()
            .nlargest(5).reset_index().sort_values("is_win")
        )
        fig_c = px.bar(top5_c, x="is_win", y="constructor_name", orientation="h",
                       color="is_win",
                       color_continuous_scale=[[0,"#001a33"],[1,AZUL]],
                       labels={"is_win":"Victorias","constructor_name":""})
        fig_c.update_layout(**PLOTLY_LAYOUT, height=200, showlegend=False,
                            coloraxis_showscale=False,
                            xaxis=dict(gridcolor="#222", tickfont=dict(color=GRIS)),
                            yaxis=dict(gridcolor="rgba(0,0,0,0)", tickfont=dict(color=TEXTO)))
        st.plotly_chart(fig_c, use_container_width=True)

    st.markdown('<div class="red-divider"></div>', unsafe_allow_html=True)


    # ── SECCIÓN 2: PREGUNTA 2 — Clasificación vs Victoria ────────────────────
    st.markdown('<div class="section-title">② ¿Qué tan importante es clasificar bien?</div>',
                unsafe_allow_html=True)
    st.markdown('<div class="red-divider"></div>', unsafe_allow_html=True)

    col3, col4 = st.columns(2)

    with col3:
        hallazgo_card(
            "2A", "La pole position es una ventaja decisiva",
            f"{tasa_pole}% de conversión",
            f"Un piloto que sale desde la pole position convierte en victoria "
            f"el {tasa_pole}% de las veces. Salir desde P6 o más atrás reduce "
            f"esa probabilidad drásticamente.",
            color=ROJO
        )

        hallazgo_card(
            "2B", "El top 3 de salida concentra la mayoría de victorias",
            f"{pct_wins_top3}% de las victorias",
            f"{wins_top3} de {total_wins} victorias totales fueron obtenidas "
            f"por pilotos que salieron desde las 3 primeras posiciones.",
            color=AMBAR
        )

    with col4:
        # Gráfico de tasa de victoria por posición de salida
        heatmap_data = (
            df[df["grid"].between(1, 10)]
            .dropna(subset=["grid", "position"])
            .groupby("grid")
            .agg(total=("raceId","count"), victorias=("is_win","sum"))
            .reset_index()
            .assign(tasa=lambda x: (x["victorias"] / x["total"] * 100).round(1))
        )

        fig_tasa = px.bar(
            heatmap_data,
            x="grid", y="tasa",
            labels={"grid": "Posición de Salida", "tasa": "Tasa de Victoria (%)"},
            color="tasa",
            color_continuous_scale=[[0,"#0f0f0f"],[0.3,"#3a0000"],[1,ROJO]],
        )
        fig_tasa.update_layout(
            **PLOTLY_LAYOUT, height=280,
            showlegend=False, coloraxis_showscale=False,
            xaxis=dict(gridcolor="#222", tickfont=dict(color=TEXTO),
                       tickvals=list(range(1,11)),
                       ticktext=[f"P{i}" for i in range(1,11)]),
            yaxis=dict(gridcolor="#222", tickfont=dict(color=GRIS)),
            title=dict(text="Tasa de victoria por posición de salida",
                       font=dict(color=TEXTO, size=13))
        )
        st.plotly_chart(fig_tasa, use_container_width=True)

    st.markdown('<div class="red-divider"></div>', unsafe_allow_html=True)


    # ── SECCIÓN 3: PREGUNTA 3 — Circuitos y escuderías ───────────────────────
    st.markdown('<div class="section-title">③ ¿Existen circuitos donde ciertas escuderías dominan?</div>',
                unsafe_allow_html=True)
    st.markdown('<div class="red-divider"></div>', unsafe_allow_html=True)

    col5, col6 = st.columns(2)

    with col5:
        hallazgo_card(
            "3A", f"{equipo_dom} domina en {circ_dom}",
            f"{wins_circ_dom} victorias",
            f"El circuito con mayor concentración de victorias de un solo equipo "
            f"es {circ_dom}, donde {equipo_dom} ha ganado {wins_circ_dom} veces. "
            f"Esto sugiere una afinidad técnica entre el equipo y las características del trazado.",
            color=VERDE
        )

    with col6:
        hallazgo_card(
            "3B", f"Tendencia de la pole position ({signo}{delta_pole}pp)",
            f"{tasa_pole_rec}% última década",
            f"En la última década la tasa de conversión pole→victoria es {tasa_pole_rec}%, "
            f"vs {tasa_pole_ant}% en la década anterior. "
            f"La ventaja de salir primero ha {'aumentado' if delta_pole >= 0 else 'disminuido'} "
            f"{abs(delta_pole)} puntos porcentuales.",
            color=AMBAR
        )

    st.markdown('<div class="red-divider"></div>', unsafe_allow_html=True)


    # ── RESUMEN VISUAL FINAL ──────────────────────────────────────────────────
    st.markdown('<div class="section-title">Resumen Visual · Los 4 KPIs del Proyecto</div>',
                unsafe_allow_html=True)
    st.markdown('<div class="section-sub">Valores calculados para el período seleccionado</div>',
                unsafe_allow_html=True)

    podios_top_piloto = int(df[df["driver_name"] == top_piloto]["is_podium"].sum())
    pts_top_const     = round(
        df[df["constructor_name"] == top_constructor]["points"].sum() /
        df[df["constructor_name"] == top_constructor]["raceId"].nunique(), 1
    )

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-value">{wins_top_piloto}</div>
            <div class="kpi-label">Victorias Totales · Líder</div>
            <div class="kpi-sub">{top_piloto}</div>
        </div>""", unsafe_allow_html=True)
    with c2:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-value">{podios_top_piloto}</div>
            <div class="kpi-label">Podios · Piloto Líder</div>
            <div class="kpi-sub">{top_piloto}</div>
        </div>""", unsafe_allow_html=True)
    with c3:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-value">{tasa_pole}%</div>
            <div class="kpi-label">Tasa Pole → Victoria</div>
            <div class="kpi-sub">Período completo</div>
        </div>""", unsafe_allow_html=True)
    with c4:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-value">{pts_top_const}</div>
            <div class="kpi-label">Pts/Carrera · Constructor</div>
            <div class="kpi-sub">{top_constructor}</div>
        </div>""", unsafe_allow_html=True)
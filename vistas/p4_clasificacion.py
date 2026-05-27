import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np

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
        <div class="page-title">CLASIFICACIÓN VS RESULTADO</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div style="background:#1a1a1a; border-left:4px solid #e10600;
                padding:12px 16px; border-radius:4px; margin-bottom:20px;">
        <span style="color:#e10600; font-weight:700; font-size:14px;">
        PREGUNTA ANALÍTICA
        </span><br>
        <span style="color:#f0f0f0; font-size:15px;">
        ¿Salir primero en clasificación realmente aumenta las probabilidades de ganar?
        </span>
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

        grid_max = st.slider("Posición de salida máxima", 1, 20, 20)

    # Aplicar filtros
    df = df_master[
        (df_master["year"] >= rango[0]) &
        (df_master["year"] <= rango[1])
    ].dropna(subset=["grid", "position"]).copy()

    df = df[(df["grid"] > 0) & (df["position"] > 0) & (df["grid"] <= grid_max)]

    if equipo_sel:
        df = df[df["constructor_name"].isin(equipo_sel)]


    # ── KPI CARDS ─────────────────────────────────────────────────────────────
    poles       = df[df["grid"] == 1]
    tasa_pole   = round(poles["is_win"].mean() * 100, 1) if len(poles) > 0 else 0

    top3_salida = df[df["grid"] <= 3]
    tasa_top3   = round(top3_salida["is_win"].mean() * 100, 1) if len(top3_salida) > 0 else 0

    fuera_top5  = df[df["grid"] > 5]
    tasa_fuera  = round(fuera_top5["is_win"].mean() * 100, 1) if len(fuera_top5) > 0 else 0

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-value">{tasa_pole}%</div>
            <div class="kpi-label">Tasa Victoria desde Pole</div>
            <div class="kpi-sub">Salida desde posición 1</div>
        </div>""", unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-value">{tasa_top3}%</div>
            <div class="kpi-label">Tasa Victoria desde Top 3</div>
            <div class="kpi-sub">Salida desde posición 1–3</div>
        </div>""", unsafe_allow_html=True)

    with col3:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-value">{tasa_fuera}%</div>
            <div class="kpi-label">Tasa Victoria desde P6+</div>
            <div class="kpi-sub">Salida desde posición 6 en adelante</div>
        </div>""", unsafe_allow_html=True)

    st.markdown('<div class="red-divider"></div>', unsafe_allow_html=True)


    # ── SCATTER PLOT ──────────────────────────────────────────────────────────
    st.markdown('<div class="section-title">Scatter Plot · Posición de Salida vs Resultado Final</div>',
                unsafe_allow_html=True)
    st.markdown('<div class="section-sub">Cada punto es una carrera · color indica escudería (top 6)</div>',
                unsafe_allow_html=True)

    top6 = (
        df.groupby("constructor_name")["is_win"].sum()
        .nlargest(6).index.tolist()
    )
    df_scatter = df[df["constructor_name"].isin(top6)].copy()

    # Línea de referencia diagonal (salida = llegada perfecta)
    ref_line = pd.DataFrame({"x": [1, 20], "y": [1, 20]})

    fig_scatter = px.scatter(
        df_scatter,
        x="grid", y="position",
        color="constructor_name",
        opacity=0.5,
        labels={
            "grid":             "Posición de Salida (Grid)",
            "position":         "Posición Final",
            "constructor_name": "Escudería"
        },
        color_discrete_sequence=[ROJO, "#ff6b6b", "#ffffff", "#aaaaaa", "#0088ff", "#00cc44"],
        hover_data=["driver_name", "race_name", "year"]
    )

    # Línea diagonal de referencia
    fig_scatter.add_trace(go.Scatter(
        x=[1, 20], y=[1, 20],
        mode="lines",
        line=dict(color="#444", dash="dash", width=1),
        name="Referencia",
        showlegend=False
    ))

    fig_scatter.update_layout(
        **PLOTLY_LAYOUT, height=420,
        legend=dict(
            orientation="h", yanchor="bottom", y=1.02,
            bgcolor="rgba(0,0,0,0)", font=dict(color=TEXTO, size=11)
        ),
        xaxis=dict(gridcolor="#222", tickfont=dict(color=GRIS),
                   title="Posición de Salida", range=[0.5, grid_max + 0.5]),
        yaxis=dict(gridcolor="#222", tickfont=dict(color=GRIS),
                   title="Posición Final", autorange="reversed"),
    )
    st.plotly_chart(fig_scatter, use_container_width=True)

    st.markdown('<div class="red-divider"></div>', unsafe_allow_html=True)


    # ── HEATMAP ───────────────────────────────────────────────────────────────
    st.markdown('<div class="section-title">Heatmap · Tasa de Victoria por Posición de Salida</div>',
                unsafe_allow_html=True)
    st.markdown('<div class="section-sub">% de victorias obtenidas desde cada posición de salida</div>',
                unsafe_allow_html=True)

    heatmap_data = (
        df[df["grid"] <= 10]
        .groupby("grid")
        .agg(total=("raceId", "count"), victorias=("is_win", "sum"))
        .reset_index()
        .assign(tasa=lambda x: (x["victorias"] / x["total"] * 100).round(1))
    )

    # Reshape para heatmap (1 fila, 10 columnas)
    pivot = heatmap_data.set_index("grid")["tasa"].reindex(range(1, 11), fill_value=0)

    fig_heat = go.Figure(data=go.Heatmap(
        z=[pivot.values],
        x=[f"P{i}" for i in range(1, 11)],
        y=["Tasa Victoria %"],
        colorscale=[[0, "#0f0f0f"], [0.3, "#3a0000"], [1, ROJO]],
        text=[[f"{v:.1f}%" for v in pivot.values]],
        texttemplate="%{text}",
        textfont=dict(size=13, color="white"),
        showscale=True,
        colorbar=dict(
            tickfont=dict(color=TEXTO),
            title=dict(text="%", font=dict(color=TEXTO))
        )
    ))
    fig_heat.update_layout(
        **PLOTLY_LAYOUT, height=160,
        xaxis=dict(tickfont=dict(color=TEXTO, size=13)),
        yaxis=dict(tickfont=dict(color=GRIS)),
    )
    st.plotly_chart(fig_heat, use_container_width=True)

    st.markdown('<div class="red-divider"></div>', unsafe_allow_html=True)


    # ── BOXPLOT ───────────────────────────────────────────────────────────────
    st.markdown('<div class="section-title">Boxplot · Distribución de Resultados por Posición de Salida</div>',
                unsafe_allow_html=True)
    st.markdown('<div class="section-sub">Posiciones de salida 1 al 10 · dispersión de resultados finales</div>',
                unsafe_allow_html=True)

    df_box = df[df["grid"] <= 10].copy()
    df_box["grid_label"] = "P" + df_box["grid"].astype(int).astype(str)

    orden = [f"P{i}" for i in range(1, 11)]

    fig_box = px.box(
        df_box,
        x="grid_label", y="position",
        category_orders={"grid_label": orden},
        labels={"grid_label": "Posición de Salida", "position": "Posición Final"},
        color="grid_label",
        color_discrete_sequence=[
            ROJO, "#ff4444", "#ff6666", "#ff8888", "#ffaaaa",
            "#aaaaaa", "#888888", "#666666", "#444444", "#333333"
        ],
    )
    fig_box.update_traces(
        marker=dict(size=3, opacity=0.5),
        line=dict(width=1.5)
    )
    fig_box.update_layout(
        **PLOTLY_LAYOUT, height=380,
        showlegend=False,
        xaxis=dict(gridcolor="#222", tickfont=dict(color=TEXTO)),
        yaxis=dict(gridcolor="#222", tickfont=dict(color=GRIS),
                   title="Posición Final", autorange="reversed"),
    )
    st.plotly_chart(fig_box, use_container_width=True)

    st.markdown('<div class="red-divider"></div>', unsafe_allow_html=True)


    # ── CONCLUSIÓN ANALÍTICA ──────────────────────────────────────────────────
    st.markdown('<div class="section-title">Conclusión Analítica</div>', unsafe_allow_html=True)

    # Calcular stats para la conclusión dinámica
    victorias_desde_top3 = int(df[df["grid"] <= 3]["is_win"].sum())
    total_victorias      = int(df["is_win"].sum())
    pct_top3             = round(victorias_desde_top3 / total_victorias * 100, 1) if total_victorias > 0 else 0

    victorias_desde_pole = int(df[df["grid"] == 1]["is_win"].sum())
    pct_pole             = round(victorias_desde_pole / total_victorias * 100, 1) if total_victorias > 0 else 0

    col_a, col_b, col_c = st.columns(3)

    with col_a:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-value">{pct_pole}%</div>
            <div class="kpi-label">De victorias vienen de Pole</div>
            <div class="kpi-sub">{victorias_desde_pole} de {total_victorias} victorias</div>
        </div>""", unsafe_allow_html=True)

    with col_b:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-value">{pct_top3}%</div>
            <div class="kpi-label">De victorias vienen del Top 3</div>
            <div class="kpi-sub">{victorias_desde_top3} de {total_victorias} victorias</div>
        </div>""", unsafe_allow_html=True)

    with col_c:
        ventaja = round(tasa_pole - tasa_fuera, 1)
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-value">+{ventaja}pp</div>
            <div class="kpi-label">Ventaja Pole vs P6+</div>
            <div class="kpi-sub">Puntos porcentuales de diferencia</div>
        </div>""", unsafe_allow_html=True)
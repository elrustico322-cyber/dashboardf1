import streamlit as st

st.set_page_config(
    page_title="F1 Analytics Dashboard",
    page_icon="🏎️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─── PALETA Y ESTILOS GLOBALES ───────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;500;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Roboto', sans-serif;
}

/* Fondo general */
.stApp {
    background-color: #0f0f0f;
    color: #f0f0f0;
}

/* Sidebar */
[data-testid="stSidebar"] {
    background-color: #1a1a1a;
    border-right: 2px solid #e10600;
}

[data-testid="stSidebar"] .stSelectbox label,
[data-testid="stSidebar"] .stMultiSelect label,
[data-testid="stSidebar"] p {
    color: #f0f0f0 !important;
    font-size: 13px;
}

/* Título del sidebar */
.sidebar-title {
    color: #e10600;
    font-size: 22px;
    font-weight: 700;
    letter-spacing: 2px;
    margin-bottom: 4px;
}

.sidebar-sub {
    color: #888;
    font-size: 11px;
    letter-spacing: 1px;
    margin-bottom: 20px;
}

/* Navegación personalizada */
.nav-button {
    display: block;
    width: 100%;
    padding: 10px 14px;
    margin: 4px 0;
    background: transparent;
    border: none;
    border-left: 3px solid transparent;
    color: #aaa;
    font-size: 13px;
    font-family: 'Roboto', sans-serif;
    cursor: pointer;
    text-align: left;
    transition: all 0.2s;
}

.nav-button:hover, .nav-button.active {
    border-left: 3px solid #e10600;
    color: #fff;
    background: rgba(225, 6, 0, 0.08);
}

/* Cards KPI */
.kpi-card {
    background: #1a1a1a;
    border: 1px solid #2a2a2a;
    border-top: 3px solid #e10600;
    border-radius: 6px;
    padding: 20px 16px;
    text-align: center;
}

.kpi-value {
    font-size: 36px;
    font-weight: 700;
    color: #e10600;
    font-variant-numeric: tabular-nums;
    line-height: 1;
}

.kpi-label {
    font-size: 12px;
    color: #888;
    letter-spacing: 1px;
    margin-top: 6px;
    text-transform: uppercase;
}

.kpi-sub {
    font-size: 11px;
    color: #555;
    margin-top: 4px;
}

/* Separador rojo */
.red-divider {
    height: 2px;
    background: linear-gradient(to right, #e10600, transparent);
    margin: 16px 0;
}

/* Títulos de sección */
.section-title {
    font-size: 18px;
    font-weight: 700;
    color: #fff;
    letter-spacing: 1px;
    margin-bottom: 4px;
}

.section-sub {
    font-size: 12px;
    color: #666;
    margin-bottom: 16px;
}

/* Encabezado de página */
.page-header {
    background: linear-gradient(135deg, #1a1a1a 0%, #111 100%);
    border-bottom: 2px solid #e10600;
    padding: 16px 0 12px 0;
    margin-bottom: 24px;
}

.page-title {
    font-size: 28px;
    font-weight: 700;
    color: #fff;
    letter-spacing: 2px;
}

.page-breadcrumb {
    font-size: 11px;
    color: #e10600;
    letter-spacing: 2px;
    text-transform: uppercase;
}

/* Scrollbar */
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: #111; }
::-webkit-scrollbar-thumb { background: #e10600; border-radius: 3px; }

/* Tablas */
[data-testid="stDataFrame"] {
    background: #1a1a1a;
}

/* Botones streamlit */
.stButton > button {
    background: #e10600;
    color: white;
    border: none;
    font-family: 'Roboto', sans-serif;
    font-weight: 500;
    letter-spacing: 1px;
}

.stButton > button:hover {
    background: #ff1a0e;
    color: white;
}

/* Selectbox */
.stSelectbox > div > div {
    background: #1a1a1a;
    border-color: #333;
    color: #f0f0f0;
}

</style>
""", unsafe_allow_html=True)


# ─── CARGA DE DATOS (con cache) ───────────────────────────────────────────────
@st.cache_data
def cargar_datos():
    import pandas as pd
    import numpy as np
    import os

    carpeta = "DatosF1"
    archivos = [f for f in os.listdir(carpeta) if f.endswith(".csv")]
    tablas = {}
    for archivo in archivos:
        nombre = archivo.replace(".csv", "")
        tablas[nombre] = pd.read_csv(os.path.join(carpeta, archivo))

    # Reemplazar \N por NaN
    for nombre, df in tablas.items():
        df.replace("\\N", np.nan, inplace=True)

    # Columnas numéricas clave
    tablas["results"]["position"]  = pd.to_numeric(tablas["results"]["position"],  errors="coerce")
    tablas["results"]["grid"]      = pd.to_numeric(tablas["results"]["grid"],      errors="coerce")
    tablas["results"]["points"]    = pd.to_numeric(tablas["results"]["points"],    errors="coerce")
    tablas["qualifying"]["position"] = pd.to_numeric(tablas["qualifying"]["position"], errors="coerce")

    # Nombre completo del piloto
    tablas["drivers"]["driver_name"] = tablas["drivers"]["forename"] + " " + tablas["drivers"]["surname"]

    return tablas

tablas = cargar_datos()


# ─── TABLA MAESTRA (con cache) ────────────────────────────────────────────────
@st.cache_data
def construir_master(_tablas):
    import pandas as pd
    import numpy as np

    results      = _tablas["results"]
    races        = _tablas["races"]
    circuits     = _tablas["circuits"]
    drivers      = _tablas["drivers"]
    constructors = _tablas["constructors"]
    status       = _tablas["status"]

    df = (
        results
        .merge(races[["raceId","year","circuitId","name"]].rename(columns={"name":"race_name"}),
               on="raceId", how="left")
        .merge(circuits[["circuitId","name","country","lat","lng"]].rename(columns={"name":"circuit_name"}),
               on="circuitId", how="left")
        .merge(drivers[["driverId","driver_name","nationality"]].rename(columns={"nationality":"driver_nationality"}),
               on="driverId", how="left")
        .merge(constructors[["constructorId","name","nationality"]].rename(
               columns={"name":"constructor_name","nationality":"constructor_nationality"}),
               on="constructorId", how="left")
        .merge(status[["statusId","status"]], on="statusId", how="left")
    )

    df["is_win"]    = (df["position"] == 1).astype(int)
    df["is_podium"] = (df["position"] <= 3).astype(int)

    return df

df_master = construir_master(tablas)


# ─── NAVEGACIÓN LATERAL ───────────────────────────────────────────────────────
with st.sidebar:
    st.markdown('<div class="sidebar-title">🏎️ F1 ANALYTICS</div>', unsafe_allow_html=True)
    st.markdown('<div class="sidebar-sub">DASHBOARD · 2009–2024</div>', unsafe_allow_html=True)
    st.markdown('<div class="red-divider"></div>', unsafe_allow_html=True)

    pagina = st.radio(
        "Navegación",
        options=[
            "📊 Resumen Ejecutivo",
            "🏁 Pilotos",
            "🔧 Escuderías",
            "🎯 Clasificación vs Resultado",
            "🌍 Circuitos",
            "💡 Hallazgos"
        ],
        label_visibility="collapsed"
    )

    st.markdown('<div class="red-divider"></div>', unsafe_allow_html=True)
    st.markdown('<div class="sidebar-sub">FUENTE: ERGAST API</div>', unsafe_allow_html=True)


# ─── ENRUTAMIENTO DE PÁGINAS ─────────────────────────────────────────────────
if pagina == "📊 Resumen Ejecutivo":
    from vistas.p1_resumen import mostrar
    mostrar(df_master, tablas)

elif pagina == "🏁 Pilotos":
    from vistas.p2_pilotos import mostrar
    mostrar(df_master, tablas)

elif pagina == "🔧 Escuderías":
    from vistas.p3_escuderias import mostrar
    mostrar(df_master, tablas)

elif pagina == "🎯 Clasificación vs Resultado":
    from vistas.p4_clasificacion import mostrar
    mostrar(df_master, tablas)
    
elif pagina == "🌍 Circuitos":
    from vistas.p5_circuitos import mostrar
    mostrar(df_master, tablas)

elif pagina == "💡 Hallazgos":
    from vistas.p6_hallazgos import mostrar
    mostrar(df_master, tablas)

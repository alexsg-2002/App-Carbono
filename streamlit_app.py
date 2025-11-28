import random
import io
import pandas as pd
import plotly.express as px
import streamlit as st

# ------------------ Función de simulación ------------------
def simular_huella_carbono(dias=30, seed=None):
    if seed is not None and seed != 0:
        random.seed(int(seed))
    actividades = ['Transporte', 'Energía', 'Residuos', 'Agua']
    lista_actividad = []
    lista_emisiones = []
    lista_reduccion = []
    lista_costos = []
    lista_categoria = []

    for actividad in actividades:
        for i in range(dias):
            if actividad == 'Transporte':
                emision = random.uniform(30, 100)
                reduccion = random.uniform(20, 40)
            elif actividad == 'Energía':
                emision = random.uniform(50, 150)
                reduccion = random.uniform(30, 60)
            elif actividad == 'Residuos':
                emision = random.uniform(10, 60)
                reduccion = random.uniform(10, 40)
            else:  # Agua
                emision = random.uniform(5, 30)
                reduccion = random.uniform(5, 20)

            costo = emision * 15  # USD por tonelada de CO2eq

            if emision < 40:
                categoria = "Bajo"
            elif emision <= 90:
                categoria = "Medio"
            else:
                categoria = "Alto"

            lista_actividad.append(actividad)
            lista_emisiones.append(round(emision, 3))
            lista_reduccion.append(round(reduccion, 2))
            lista_costos.append(round(costo, 2))
            lista_categoria.append(categoria)

    df = pd.DataFrame({
        'Actividad': lista_actividad,
        'Emisiones_tCO2eq': lista_emisiones,
        'Reduccion_Potencial_%': lista_reduccion,
        'Costo_Ambiental_USD': lista_costos,
        'Categoria_Impacto': lista_categoria
    })
    return df

# ------------------ Funciones auxiliares ------------------
def resumen_promedio(df):
    return df.groupby('Actividad', as_index=False)['Emisiones_tCO2eq'].mean().rename(columns={'Emisiones_tCO2eq':'Emisiones_promedio_tCO2eq'})

def descarga_csv(df):
    buffer = io.StringIO()
    df.to_csv(buffer, index=False)
    return buffer.getvalue().encode('utf-8')

# ------------------ Interfaz Streamlit ------------------
st.set_page_config(page_title="Huella de Carbono - Universidad", layout="wide")
st.title("📊 Evaluación de Huella de Carbono en la Universidad")

with st.sidebar:
    st.header("Controles de simulación")
    dias = st.slider("Días a simular (por actividad)", min_value=1, max_value=365, value=30)
    seed = st.number_input("Semilla aleatoria (0 = aleatorio)", min_value=0, value=0, step=1)
    num_corridas = st.slider("Número de corridas (incertidumbre)", min_value=1, max_value=50, value=1)
    escenario = st.selectbox("Escenario / Política", ["Base (sin medidas)", "Medidas moderadas (aplica 15% reducción)", "Medidas fuertes (aplica 35% reducción)"])
    st.markdown("---")
    st.write("Después de ajustar, presiona **Simular**.")
    btn_simular = st.button("Simular")

# Placeholder para datos y gráficos
df_global = None

if btn_simular:
    # ejecutar múltiples corridas si corresponde
    lista_dfs = []
    for run in range(num_corridas):
        s = seed + run if seed != 0 else None
        df_run = simular_huella_carbono(dias=dias, seed=s)
        # aplicar escenario
        if escenario == "Medidas moderadas (aplica 15% reducción)":
            df_run['Emisiones_tCO2eq'] = df_run['Emisiones_tCO2eq'] * 0.85
            df_run['Costo_Ambiental_USD'] = df_run['Emisiones_tCO2eq'] * 15
        elif escenario == "Medidas fuertes (aplica 35% reducción)":
            df_run['Emisiones_tCO2eq'] = df_run['Emisiones_tCO2eq'] * 0.65
            df_run['Costo_Ambiental_USD'] = df_run['Emisiones_tCO2eq'] * 15
        df_run['Corrida'] = run + 1
        lista_dfs.append(df_run)
    # concatenar
    df_global = pd.concat(lista_dfs, ignore_index=True)

    st.success(f"Simulación completada: {num_corridas} corrida(s), {dias} días por actividad.")
    st.session_state['df_sim'] = df_global  # guardamos en session_state para filtros posteriores

# Si hay datos en session_state, usarlo
if 'df_sim' in st.session_state:
    df_global = st.session_state['df_sim']

if df_global is not None:
    # Layout: 2 columnas para gráficos + tabla abajo
    col1, col2 = st.columns([1.2, 1])
    with col1:
        st.subheader("Promedio de emisiones por actividad")
        prom = resumen_promedio(df_global)
        fig_prom = px.bar(prom, x='Actividad', y='Emisiones_promedio_tCO2eq', title='Promedio de emisiones por actividad', labels={'Emisiones_promedio_tCO2eq':'tCO2eq (promedio)'})
        st.plotly_chart(fig_prom, use_container_width=True)

        st.subheader("Distribución de categorías por actividad")
        fig_cat = px.histogram(df_global, x='Categoria_Impacto', color='Actividad', barmode='group', title='Categorías de impacto por actividad')
        st.plotly_chart(fig_cat, use_container_width=True)

    with col2:
        st.subheader("Boxplot de emisiones")
        actividad_filtro = st.selectbox("Filtrar por actividad", ["Todas"] + sorted(df_global['Actividad'].unique().tolist()))
        if actividad_filtro != "Todas":
            df_plot = df_global[df_global['Actividad'] == actividad_filtro]
        else:
            df_plot = df_global
        fig_box = px.box(df_plot, x='Actividad', y='Emisiones_tCO2eq', title=f'Boxplot de emisiones ({actividad_filtro})')
        st.plotly_chart(fig_box, use_container_width=True)

        st.subheader("Estadísticas rápidas")
        stats = df_plot['Emisiones_tCO2eq'].describe().to_frame().T.round(3)
        st.dataframe(stats)

    st.markdown("---")
    st.subheader("Tabla de datos (muestra)")
    st.dataframe(df_global.head(200), use_container_width=True)

    # Descarga CSV
    csv_bytes = descarga_csv(df_global)
    st.download_button(label="📥 Descargar CSV completo", data=csv_bytes, file_name="huella_carbono_simulada.csv", mime="text/csv")

    # Métricas clave
    total_emisiones = df_global['Emisiones_tCO2eq'].sum().round(2)
    costo_total = df_global['Costo_Ambiental_USD'].sum().round(2)
    st.markdown("---")
    st.metric("Emisiones totales simuladas (tCO2eq)", f"{total_emisiones}")
    st.metric("Costo ambiental total estimado (USD)", f"{costo_total}")

else:
    st.info("Aún no hay datos simulados. Ajusta parámetros en la barra lateral y presiona **Simular**.")

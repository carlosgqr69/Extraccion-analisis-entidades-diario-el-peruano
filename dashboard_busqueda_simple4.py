import streamlit as st
import pandas as pd
from pathlib import Path
import math

st.set_page_config(page_title="Buscador El Peruano", page_icon="🔍", layout="wide")

st.markdown('''
<style>
    .titulo { font-size: 2rem; font-weight: bold; color: #1f77b4; text-align: center; }
    .card { background: #f8f9fa; padding: 1.5rem; border-radius: 0.5rem; border-left: 4px solid #1f77b4; margin: 1rem 0; }
    .badge { display: inline-block; padding: 0.25rem 0.5rem; border-radius: 0.25rem; font-size: 0.75rem; font-weight: bold; margin-right: 0.5rem; }
    .badge-decreto { background-color: #cfe2ff; color: #084298; }
    .badge-ley { background-color: #e2d9f3; color: #432874; }
    .badge-resolucion { background-color: #f8d7da; color: #721c24; }
    .badge-junta { background-color: #d1ecf1; color: #0c5460; }
    .badge-disolucion { background-color: #f8d7da; color: #721c24; }
    .badge-remate { background-color: #d4edda; color: #155724; }
    .texto-preview { 
        font-family: Arial, sans-serif; 
        font-size: 0.95rem; 
        line-height: 1.6; 
        color: #333;
        white-space: pre-wrap;
        margin-top: 1rem;
        background: white;
        padding: 1rem;
        border-radius: 0.5rem;
    }
</style>
''', unsafe_allow_html=True)

def cortar_texto(texto, max_chars=800):
    if len(texto) <= max_chars:
        return texto, False
    
    texto_corto = texto[:max_chars]
    ultimo_espacio = texto_corto.rfind(' ')
    if ultimo_espacio > max_chars * 0.7:
        return texto[:ultimo_espacio] + '...', True
    
    return texto[:max_chars] + '...', True

# CARGAR DATOS
@st.cache_data(show_spinner="Cargando datos...")
def cargar_datos():
    ruta = Path("base_datos_final/base_datos_completa.csv")
    
    if not ruta.exists():
        return None
    
    df = pd.read_csv(ruta, encoding='utf-8', low_memory=False)
    return df

df = cargar_datos()

if df is None:
    st.error(" No se encontró base_datos_completa.csv")
    st.info("Ejecuta la celda de CONSOLIDACIÓN en tu notebook primero")
    st.stop()

# Filtrar tipos relevantes
TIPOS_RELEVANTES = [
    'DECRETO_SUPREMO', 'RESOLUCION_SUPREMA', 'RESOLUCION_MINISTERIAL',
    'LEY', 'JUNTA_ACCIONISTAS', 'DISOLUCION', 'REMATE', 'AVISO'
]

if 'tipo' in df.columns:
    df = df[df['tipo'].isin(TIPOS_RELEVANTES)]

st.markdown('<h1 class="titulo"> Buscador Diario El Peruano</h1>', unsafe_allow_html=True)
st.markdown(f"<p style='text-align: center; color: gray;'>Base de datos con {len(df)} avisos legales</p>", unsafe_allow_html=True)

# Filtros
st.sidebar.markdown("##  Filtros")
busqueda = st.sidebar.text_input("Buscar en texto", placeholder="Ej: SUNAT, remate...")

tipos_disponibles = ['Todos']
if 'tipo' in df.columns:
    tipos_disponibles += sorted(df['tipo'].unique().tolist())
tipo = st.sidebar.selectbox("Tipo de documento", tipos_disponibles)

empresa = ""
if 'empresa' in df.columns:
    empresa = st.sidebar.text_input("Empresa", placeholder="Ej: TRANSPORTES...")

ruc = ""
if 'ruc' in df.columns:
    ruc = st.sidebar.text_input("RUC", placeholder="20100154057")

orden = st.sidebar.radio("Ordenar por fecha", ["Más recientes", "Más antiguos"])

# Aplicar filtros
df_filtrado = df.copy()

# Filtro por tipo
if tipo != 'Todos' and 'tipo' in df.columns:
    df_filtrado = df_filtrado[df_filtrado['tipo'] == tipo]

# Filtro por empresa
if empresa and 'empresa' in df.columns:
    df_filtrado = df_filtrado[df_filtrado['empresa'].str.contains(empresa, case=False, na=False)]

# Filtro por RUC
if ruc and 'ruc' in df.columns:
    df_filtrado = df_filtrado[df_filtrado['ruc'].astype(str).str.contains(ruc, na=False)]

# Filtro por búsqueda en texto
if busqueda:
    # Buscar en texto_completo o texto
    col_texto = None
    for col in ['texto_completo', 'texto', 'contenido']:
        if col in df_filtrado.columns:
            col_texto = col
            break
    
    if col_texto:
        df_filtrado = df_filtrado[df_filtrado[col_texto].str.contains(busqueda, case=False, na=False)]

# Ordenar por fecha
col_fecha = None
for col in ['fecha_boletin', 'fecha', 'fecha_publicacion']:
    if col in df_filtrado.columns:
        col_fecha = col
        break

if col_fecha:
    if orden == "Más recientes":
        df_filtrado = df_filtrado.sort_values(col_fecha, ascending=False)
    else:
        df_filtrado = df_filtrado.sort_values(col_fecha, ascending=True)

# Métricas
st.markdown("---")
col1, col2, col3, col4 = st.columns(4)
col1.metric(" Resultados", len(df_filtrado))

if 'tipo' in df_filtrado.columns:
    col2.metric(" Juntas", len(df_filtrado[df_filtrado['tipo'] == 'JUNTA_ACCIONISTAS']))
    col3.metric(" Disoluciones", len(df_filtrado[df_filtrado['tipo'] == 'DISOLUCION']))
    col4.metric(" Remates", len(df_filtrado[df_filtrado['tipo'] == 'REMATE']))

st.markdown("---")

# Paginación
RESULTADOS_POR_PAGINA = 10
total_resultados = len(df_filtrado)
total_paginas = math.ceil(total_resultados / RESULTADOS_POR_PAGINA) if total_resultados > 0 else 1

if 'pagina' not in st.session_state:
    st.session_state.pagina = 1

# Reset página si cambian filtros
filtros_actuales = f"{busqueda}_{tipo}_{empresa}_{ruc}_{orden}"
if 'filtros_anteriores' not in st.session_state:
    st.session_state.filtros_anteriores = filtros_actuales
elif st.session_state.filtros_anteriores != filtros_actuales:
    st.session_state.pagina = 1
    st.session_state.filtros_anteriores = filtros_actuales

if total_resultados > 0:
    # Navegación
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col1:
        if st.session_state.pagina > 1:
            if st.button(" Anterior"):
                st.session_state.pagina -= 1
                st.rerun()
    
    with col2:
        pagina_actual = st.selectbox(
            "Página",
            options=list(range(1, total_paginas + 1)),
            index=st.session_state.pagina - 1,
            key="selector_pagina"
        )
        if pagina_actual != st.session_state.pagina:
            st.session_state.pagina = pagina_actual
            st.rerun()
    
    with col3:
        if st.session_state.pagina < total_paginas:
            if st.button("Siguiente "):
                st.session_state.pagina += 1
                st.rerun()
    
    inicio = (st.session_state.pagina - 1) * RESULTADOS_POR_PAGINA
    fin = min(inicio + RESULTADOS_POR_PAGINA, total_resultados)
    
    st.markdown(f"### Mostrando {inicio + 1} - {fin} de {total_resultados} resultados")
    
    # Mostrar resultados
    for idx, row in df_filtrado.iloc[inicio:fin].iterrows():
        tipo_doc = row['tipo'] if 'tipo' in df_filtrado.columns and pd.notna(row['tipo']) else 'AVISO'
        
        # Badge con color
        badge_map = {
            'DECRETO_SUPREMO': ('DECRETO SUPREMO', 'badge-decreto'),
            'RESOLUCION_SUPREMA': ('RESOLUCIÓN SUPREMA', 'badge-resolucion'),
            'LEY': ('LEY', 'badge-ley'),
            'JUNTA_ACCIONISTAS': ('JUNTA', 'badge-junta'),
            'DISOLUCION': ('DISOLUCIÓN', 'badge-disolucion'),
            'REMATE': ('REMATE', 'badge-remate'),
        }
        
        badge_texto, badge_clase = badge_map.get(tipo_doc, (tipo_doc, 'badge'))
        badge = f'<span class="badge {badge_clase}">{badge_texto}</span>'
        
        # Metadata
        metadata_parts = []
        if col_fecha and pd.notna(row[col_fecha]):
            metadata_parts.append(f" Fecha: {row[col_fecha]}")
        if 'empresa' in df_filtrado.columns and pd.notna(row['empresa']) and str(row['empresa']).strip():
            metadata_parts.append(f" Empresa: {row['empresa']}")
        if 'ruc' in df_filtrado.columns and pd.notna(row['ruc']) and str(row['ruc']).strip():
            metadata_parts.append(f" RUC: {row['ruc']}")
        
        metadata = " | ".join(metadata_parts) if metadata_parts else "Sin metadata"
        
        st.markdown(
            f'<div class="card">{badge}<br><small>{metadata}</small></div>',
            unsafe_allow_html=True
        )
        
        # Mostrar texto
        col_texto = None
        for col in ['texto_completo', 'texto', 'contenido']:
            if col in df_filtrado.columns:
                col_texto = col
                break
        
        if col_texto and pd.notna(row[col_texto]):
            texto = str(row[col_texto])
            
            if len(texto.strip()) > 10:
                texto_preview, necesita_expansion = cortar_texto(texto, max_chars=800)
                st.markdown(f'<div class="texto-preview">{texto_preview}</div>', unsafe_allow_html=True)
                
                if necesita_expansion:
                    with st.expander("📄 Ver texto completo"):
                        st.text(texto)
            else:
                st.info("Sin texto disponible")
        else:
            st.info("Sin texto disponible")
        
        st.markdown("<br>", unsafe_allow_html=True)
    
    st.markdown("---")
    st.markdown(
        f"<p style='text-align: center;'>Página {st.session_state.pagina} de {total_paginas}</p>",
        unsafe_allow_html=True
    )
else:
    st.warning(" No se encontraron resultados con los filtros seleccionados")

# Descarga
if total_resultados > 0:
    st.markdown("---")
    
    if total_resultados <= 5000:
        csv = df_filtrado.to_csv(index=False, encoding='utf-8')
        st.download_button(
            " Descargar resultados (CSV)", 
            csv, 
            "resultados_peruano.csv", 
            "text/csv"
        )
    else:
        st.warning(f" Demasiados resultados ({total_resultados:,}). Usa filtros para reducir a menos de 5,000.")

st.markdown("---")
st.markdown("<p style='text-align: center; color: gray;'> Buscador Diario El Peruano</p>", unsafe_allow_html=True)

# Importar bibliotecas necesarias
import streamlit as st
import pandas as pd
import es_core_news_sm # Este es el modelo de español de spaCy
import io # Para manejar archivos en memoria
from openpyxl import Workbook # Para generar archivos Excel

# Cargar el modelo de spaCy una sola vez para optimizar el rendimiento
# Puedes descargarlo con: python -m spacy download es_core_news_sm
nlp = es_core_news_sm.load()

# Definir la función para analizar el texto
def analizar_texto(texto):
    """
    Analiza un texto para identificar formas verbales y sus atributos.
    Retorna un DataFrame con los resultados.
    """
    doc = nlp(texto)
    datos_verbo = []
    
    for token in doc:
        # Condición para identificar verbos
        if token.pos_ == "VERB":
            # Extraer información del verbo
            verbo = token.text
            lema = token.lemma_ # La forma base del verbo (ej. "correr")
            modo = "No identificado"
            tiempo = "No identificado"
            persona = "No identificado"
            
            # Usar 'Morph' para obtener la información morfológica
            if token.morph:
                morph_dict = token.morph.to_dict()
                
                # Identificar Modo
                if "Mood" in morph_dict:
                    modo = morph_dict["Mood"]
                
                # Identificar Tiempo
                if "Tense" in morph_dict:
                    tiempo = morph_dict["Tense"]
                
                # Identificar Persona
                if "Person" in morph_dict:
                    persona = morph_dict["Person"]
            
            # Guardar los datos
            datos_verbo.append([verbo, lema, modo, tiempo, persona])
    
    # Crear un DataFrame de pandas
    columnas = ["Forma Verbal", "Lema", "Modo", "Tiempo", "Persona"]
    df = pd.DataFrame(datos_verbo, columns=columnas)
    
    return df

# Configurar la aplicación de Streamlit
st.set_page_config(
    page_title="Analizador de Formas Verbales",
    page_icon="📖",
    layout="wide"
)

# Título y descripción
st.title("Analizador de Formas Verbales en Español 📖")
st.write("Sube un archivo de texto (.txt) o pega el texto directamente para analizar las formas verbales.")
st.write("---")

# Opción para subir archivo
st.header("1. Sube un archivo de texto")
uploaded_file = st.file_uploader("Elige un archivo .txt", type="txt")

# Opción para pegar texto
st.header("2. O pega el texto aquí")
text_input = st.text_area("Pega tu texto en este cuadro", height=200, placeholder="Escribe o pega tu texto aquí...")

# Botón para analizar
if st.button("Analizar Texto"):
    texto_a_analizar = ""
    
    # Prioridad: archivo subido
    if uploaded_file is not None:
        texto_a_analizar = uploaded_file.getvalue().decode("utf-8")
        st.success("Archivo subido y listo para analizar.")
    # Si no hay archivo, usar el texto pegado
    elif text_input:
        texto_a_analizar = text_input
        st.success("Texto listo para analizar.")
    else:
        st.warning("Por favor, sube un archivo o pega un texto para continuar.")
        st.stop()
    
    # Realizar el análisis
    with st.spinner("Analizando el texto..."):
        df_verbos = analizar_texto(texto_a_analizar)
    
    if not df_verbos.empty:
        st.success("Análisis completado. Resultados a continuación:")
        
        # Mostrar tabla de resultados
        st.header("Resultados del Análisis")
        st.dataframe(df_verbos)
        
        # Generar estadísticas
        st.header("Estadísticas de Verbos")
        st.markdown("### Conteo por Modo")
        st.bar_chart(df_verbos['Modo'].value_counts())
        
        st.markdown("### Conteo por Tiempo")
        st.bar_chart(df_verbos['Tiempo'].value_counts())
        
        # Generar y ofrecer la descarga del Excel
        st.header("Descargar Informe Excel")
        
        # Crear un archivo Excel en memoria
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df_verbos.to_excel(writer, sheet_name='Verbos', index=False)
            
            # Crear una hoja para las estadísticas
            estadisticas_df = pd.DataFrame({
                "Modo": df_verbos['Modo'].value_counts(),
                "Tiempo": df_verbos['Tiempo'].value_counts()
            })
            estadisticas_df.to_excel(writer, sheet_name='Estadísticas', index=True)
            
        excel_data = output.getvalue()
        
        # Botón de descarga
        st.download_button(
            label="Descargar Informe Excel",
            data=excel_data,
            file_name="informe_verbal.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    else:
        st.warning("No se encontraron verbos en el texto proporcionado.")

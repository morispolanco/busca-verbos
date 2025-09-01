import streamlit as st
import spacy
import pandas as pd
from io import BytesIO

# Cargar el modelo de spaCy para español
@st.cache_resource
def load_nlp():
    return spacy.load("es_core_news_sm")

nlp = load_nlp()

# Título de la aplicación
st.title("Analizador de Formas Verbales en Español")

# Instrucciones
st.write("Sube un archivo de texto (.txt) o pega el texto directamente. La aplicación identificará las formas verbales, incluyendo modo, tiempo, persona y número, y generará un informe estadístico en Excel.")

# Entrada de texto
text_input = st.text_area("Pega el texto aquí:", height=200)

# Subida de archivo
uploaded_file = st.file_uploader("Sube un archivo .txt", type=["txt"])

# Procesar el texto
text = ""
if uploaded_file is not None:
    text = uploaded_file.read().decode("utf-8")
elif text_input:
    text = text_input

if st.button("Analizar Texto") and text:
    # Procesar el texto con spaCy
    doc = nlp(text)
    
    # Lista para almacenar las formas verbales
    verbs = []
    
    for token in doc:
        if token.pos_ == "VERB":
            mood = token.morph.get("Mood", ["N/A"])[0]
            tense = token.morph.get("Tense", ["N/A"])[0]
            person = token.morph.get("Person", ["N/A"])[0]
            number = token.morph.get("Number", ["N/A"])[0]
            
            verbs.append({
                "Verbo": token.text,
                "Lema": token.lemma_,
                "Modo": mood,
                "Tiempo": tense,
                "Persona": person,
                "Número": number
            })
    
    if verbs:
        # Crear DataFrame con las formas verbales
        df_verbs = pd.DataFrame(verbs)
        
        # Generar estadísticas (conteo por combinación de modo, tiempo, persona, número)
        df_stats = df_verbs.groupby(["Modo", "Tiempo", "Persona", "Número"]).size().reset_index(name="Conteo")
        
        # Mostrar vista previa en la app
        st.subheader("Vista Previa de Formas Verbales")
        st.dataframe(df_verbs)
        
        st.subheader("Vista Previa de Estadísticas")
        st.dataframe(df_stats)
        
        # Generar Excel con múltiples hojas
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df_verbs.to_excel(writer, sheet_name="Formas Verbales", index=False)
            df_stats.to_excel(writer, sheet_name="Estadísticas", index=False)
        
        output.seek(0)
        
        # Botón de descarga
        st.download_button(
            label="Descargar Informe en Excel",
            data=output,
            file_name="informe_formas_verbales.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    else:
        st.warning("No se encontraron formas verbales en el texto proporcionado.")
else:
    if not text:
        st.info("Por favor, proporciona texto para analizar.")

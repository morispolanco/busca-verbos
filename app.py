import streamlit as st
import pandas as pd
import spacy
from spacy.lang.es import Spanish
import re
from collections import Counter
import io
import zipfile
from conjugation import conjugate

# Cargar el modelo de spaCy para español
@st.cache_resource
def load_spacy_model():
    try:
        nlp = spacy.load("es_core_news_lg")
    except OSError:
        st.warning("El modelo es_core_news_lg no está instalado. Usando modelo básico.")
        nlp = Spanish()
        # Añadir el componente de etiquetado POS si no está presente
        if "tagger" not in nlp.pipe_names:
            nlp.add_pipe("tagger")
    return nlp

nlp = load_spacy_model()

# Función para identificar verbos y sus características
def analyze_verbs(text):
    doc = nlp(text)
    verbs_info = []
    
    for token in doc:
        if token.pos_ == "VERB":
            # Obtener información básica
            verb_text = token.text.lower()
            lemma = token.lemma_.lower()
            
            # Intentar obtener más detalles sobre la conjugación
            try:
                conjugations = conjugate(lemma)
                verb_details = None
                
                # Buscar la conjugación que coincide con el verbo en el texto
                for mood, tenses in conjugations.items():
                    for tense, persons in tenses.items():
                        for person, form in persons.items():
                            if form.lower() == verb_text:
                                verb_details = {
                                    "verbo": verb_text,
                                    "infinitivo": lemma,
                                    "modo": mood,
                                    "tiempo": tense,
                                    "persona": person
                                }
                                break
                        if verb_details:
                            break
                    if verb_details:
                        break
                
                # Si no se encontró en las conjugaciones, usar información básica
                if not verb_details:
                    verb_details = {
                        "verbo": verb_text,
                        "infinitivo": lemma,
                        "modo": "No identificado",
                        "tiempo": "No identificado",
                        "persona": "No identificado"
                    }
                
                verbs_info.append(verb_details)
            
            except Exception as e:
                # Si hay un error con la conjugación, registrar información básica
                verbs_info.append({
                    "verbo": verb_text,
                    "infinitivo": lemma,
                    "modo": "Error",
                    "tiempo": "Error",
                    "persona": "Error"
                })
    
    return verbs_info

# Función para generar el informe estadístico
def generate_report(verbs_info):
    if not verbs_info:
        return None
    
    df = pd.DataFrame(verbs_info)
    
    # Contar frecuencias
    verb_counts = Counter([v["verbo"] for v in verbs_info])
    infinitive_counts = Counter([v["infinitivo"] for v in verbs_info])
    mode_counts = Counter([v["modo"] for v in verbs_info])
    tense_counts = Counter([v["tiempo"] for v in verbs_info])
    person_counts = Counter([v["persona"] for v in verbs_info])
    
    # Crear DataFrames para cada estadística
    df_verbs = pd.DataFrame.from_dict(verb_counts, orient='index', columns=['Frecuencia']).reset_index()
    df_verbs = df_verbs.rename(columns={'index': 'Verbo'})
    
    df_infinitives = pd.DataFrame.from_dict(infinitive_counts, orient='index', columns=['Frecuencia']).reset_index()
    df_infinitives = df_infinitives.rename(columns={'index': 'Infinitivo'})
    
    df_modes = pd.DataFrame.from_dict(mode_counts, orient='index', columns=['Frecuencia']).reset_index()
    df_modes = df_modes.rename(columns={'index': 'Modo'})
    
    df_tenses = pd.DataFrame.from_dict(tense_counts, orient='index', columns=['Frecuencia']).reset_index()
    df_tenses = df_tenses.rename(columns={'index': 'Tiempo'})
    
    df_persons = pd.DataFrame.from_dict(person_counts, orient='index', columns=['Frecuencia']).reset_index()
    df_persons = df_persons.rename(columns={'index': 'Persona'})
    
    # Crear un archivo Excel con múltiples hojas
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, sheet_name='Todos los Verbos', index=False)
        df_verbs.to_excel(writer, sheet_name='Frecuencia Verbos', index=False)
        df_infinitives.to_excel(writer, sheet_name='Frecuencia Infinitivos', index=False)
        df_modes.to_excel(writer, sheet_name='Frecuencia Modos', index=False)
        df_tenses.to_excel(writer, sheet_name='Frecuencia Tiempos', index=False)
        df_persons.to_excel(writer, sheet_name='Frecuencia Personas', index=False)
    
    output.seek(0)
    return output

# Configuración de la aplicación Streamlit
st.title("Analizador de Formas Verbales en Español")
st.markdown("""
Esta aplicación identifica todas las formas verbales en un texto en español, analizando su modo, tiempo y persona.
Sube un archivo de texto o pega el contenido directamente para generar un informe estadístico en Excel.
""")

# Opciones de entrada de texto
input_option = st.radio("Selecciona una opción:", ("Subir archivo de texto", "Pegar texto"))

text = ""
if input_option == "Subir archivo de texto":
    uploaded_file = st.file_uploader("Sube un archivo de texto", type=["txt"])
    if uploaded_file is not None:
        text = uploaded_file.read().decode("utf-8")
        st.text_area("Contenido del archivo:", text, height=200)
else:
    text = st.text_area("Pega el texto aquí:", height=200)

# Botón para analizar
if st.button("Analizar verbos") and text:
    with st.spinner("Analizando el texto..."):
        verbs_info = analyze_verbs(text)
        
        if verbs_info:
            st.success(f"Se encontraron {len(verbs_info)} formas verbales en el texto.")
            
            # Mostrar tabla con los verbos encontrados
            st.subheader("Formas verbales identificadas")
            df_verbs = pd.DataFrame(verbs_info)
            st.dataframe(df_verbs)
            
            # Generar y descargar el informe
            report = generate_report(verbs_info)
            if report:
                st.subheader("Descargar informe estadístico")
                st.download_button(
                    label="Descargar informe en Excel",
                    data=report,
                    file_name="analisis_verbos.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
        else:
            st.warning("No se encontraron formas verbales en el texto.")

# Instrucciones adicionales
st.sidebar.markdown("""
## Instrucciones
1. Selecciona una opción para ingresar el texto:
   - Sube un archivo de texto (.txt)
   - Pega el texto directamente en el área de texto
2. Haz clic en el botón "Analizar verbos"
3. Revisa los resultados en la tabla
4. Descarga el informe completo en Excel

## Notas
- La aplicación utiliza modelos de procesamiento de lenguaje natural para identificar los verbos.
- El informe en Excel contiene varias hojas con diferentes análisis estadísticos.
- Algunas formas verbales pueden no ser identificadas correctamente, especialmente en casos de uso no estándar o regional.
""")

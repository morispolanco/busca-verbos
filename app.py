import streamlit as st
import pandas as pd
import spacy
from collections import Counter
import io

# Configuración de la página
st.set_page_config(page_title="Analizador de Verbos Español", layout="wide")

# Función para cargar el modelo de spaCy
@st.cache_resource
def load_spacy_model():
    try:
        nlp = spacy.load("es_core_news_sm")
    except OSError:
        st.warning("Descargando modelo de lenguaje español (puede tardar unos segundos)...")
        from spacy.cli import download
        download("es_core_news_sm")
        nlp = spacy.load("es_core_news_sm")
    return nlp

nlp = load_spacy_model()

# Función para analizar verbos
def analyze_verbs(text):
    doc = nlp(text)
    verbs_info = []
    
    for token in doc:
        if token.pos_ == "VERB":
            verb_text = token.text.lower()
            lemma = token.lemma_.lower()
            
            # Extraer información morfológica
            morph = token.morph.to_dict()
            modo = morph.get("Mood", "No identificado")
            tiempo = morph.get("Tense", "No identificado")
            persona = morph.get("Person", "No identificado")
            numero = morph.get("Number", "")
            
            # Combinar persona y número
            if persona and numero:
                persona_numero = f"{persona} {numero}"
            else:
                persona_numero = persona or numero or "No identificado"
            
            verbs_info.append({
                "verbo": verb_text,
                "infinitivo": lemma,
                "modo": modo,
                "tiempo": tiempo,
                "persona": persona_numero
            })
    
    return verbs_info

# Función para generar informe
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
    
    # Crear DataFrames
    df_verbs = pd.DataFrame.from_dict(verb_counts, orient='index', columns=['Frecuencia']).reset_index().rename(columns={'index': 'Verbo'})
    df_infinitives = pd.DataFrame.from_dict(infinitive_counts, orient='index', columns=['Frecuencia']).reset_index().rename(columns={'index': 'Infinitivo'})
    df_modes = pd.DataFrame.from_dict(mode_counts, orient='index', columns=['Frecuencia']).reset_index().rename(columns={'index': 'Modo'})
    df_tenses = pd.DataFrame.from_dict(tense_counts, orient='index', columns=['Frecuencia']).reset_index().rename(columns={'index': 'Tiempo'})
    df_persons = pd.DataFrame.from_dict(person_counts, orient='index', columns=['Frecuencia']).reset_index().rename(columns={'index': 'Persona'})
    
    # Crear Excel
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

# Interfaz de usuario
st.title("🔍 Analizador de Formas Verbales en Español")
st.markdown("""
Esta aplicación identifica todas las formas verbales en un texto en español, analizando su modo, tiempo y persona.
Sube un archivo de texto o pega el contenido directamente para generar un informe estadístico en Excel.
""")

# Opciones de entrada
input_option = st.radio("Selecciona una opción:", ("Subir archivo de texto", "Pegar texto"), horizontal=True)

text = ""
if input_option == "Subir archivo de texto":
    uploaded_file = st.file_uploader("Sube un archivo de texto", type=["txt"])
    if uploaded_file is not None:
        text = uploaded_file.read().decode("utf-8")
        st.text_area("Contenido del archivo:", text, height=200)
else:
    text = st.text_area("Pega el texto aquí:", height=200)

# Botón de análisis
if st.button("Analizar verbos", type="primary") and text:
    with st.spinner("Analizando el texto..."):
        verbs_info = analyze_verbs(text)
        
        if verbs_info:
            st.success(f"Se encontraron {len(verbs_info)} formas verbales en el texto.")
            
            # Mostrar tabla con resultados
            st.subheader("Formas verbales identificadas")
            df_verbs = pd.DataFrame(verbs_info)
            st.dataframe(df_verbs, use_container_width=True)
            
            # Generar informe
            report = generate_report(verbs_info)
            if report:
                st.subheader("Descargar informe estadístico")
                st.download_button(
                    label="📥 Descargar informe en Excel",
                    data=report,
                    file_name="analisis_verbos.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
        else:
            st.warning("No se encontraron formas verbales en el texto.")

# Instrucciones en la barra lateral
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

# Pie de página
st.markdown("---")
st.markdown("Creado con ❤️ usando Streamlit | [Ver código fuente](https://github.com/tu_usuario/tu_repositorio)")

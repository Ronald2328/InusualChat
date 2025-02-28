import os
import logging
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'  
logging.getLogger('tensorflow').setLevel(logging.ERROR)
import requests
from bs4 import BeautifulSoup
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from googletrans import Translator
import json
import pickle
from pathlib import Path

# Importar configuración de Gemini y URL base
try:
    from config import GEMINI_API_KEY, SIMILARITY_THRESHOLD, BASE_URL
except ImportError:
    GEMINI_API_KEY = None
    SIMILARITY_THRESHOLD = 0.4
    BASE_URL = "https://en.wikipedia.org/wiki/Wikipedia:Unusual_articles"

# Importar Gemini (si la API_KEY está configurada)
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = GEMINI_API_KEY is not None
    if GEMINI_AVAILABLE:
        genai.configure(api_key=GEMINI_API_KEY)
        generation_config = {
            "temperature": 0.99,
            "top_p": 0.95,
            "top_k": 64,
            "max_output_tokens": 100,
            "response_mime_type": "text/plain",
        }
        model = genai.GenerativeModel(
            model_name="gemini-2.0-flash-exp",
            generation_config=generation_config,
        )
        chat_session = model.start_chat(
            history=[
                {"role": "user", "parts": ["Eres un asistente de búsqueda humorístico especializado en artículos inusuales de Wikipedia. Responde de manera mas breve, divertida y con un toque de sarcasmo."]},
                {"role": "model", "parts": ["¡Claro! Seré tu guía sarcástico por el extraño mundo de Wikipedia. Prepárate para descubrir cosas que no sabías que no necesitabas saber."]}
            ]
        )
except ImportError:
    GEMINI_AVAILABLE = False

# Inicializar el traductor de Google
translator = Translator()

def save_to_json(articles, filename="data/unusual_articles.json"):
    """
    Guarda los datos de los artículos inusuales en un archivo JSON.

    :param articles: Lista de artículos inusuales.
    :param filename: Nombre del archivo JSON.
    """
    Path("data").mkdir(exist_ok=True)
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(articles, f, ensure_ascii=False, indent=4)

def load_from_json(filename="data/unusual_articles.json"):
    """
    Carga los datos de los artículos inusuales desde un archivo JSON.

    :param filename: Nombre del archivo JSON.
    :return: Lista de artículos inusuales.
    """
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return []

def save_embeddings_pickle(embeddings, filename="data/article_embeddings.pkl"):
    """
    Guarda los embeddings de los artículos en un archivo pickle.

    :param embeddings: Lista de embeddings de artículos.
    :param filename: Nombre del archivo
    """
    Path("data").mkdir(exist_ok=True)
    with open(filename, 'wb') as f:
        pickle.dump(embeddings, f)

def load_embeddings_pickle(filename="data/article_embeddings.pkl"):
    """
    Carga los embeddings de los artículos desde un archivo pickle.

    :param filename: Nombre del archivo.
    :return: Lista de embeddings de artículos.
    """
    try:
        with open(filename, 'rb') as f:
            return pickle.load(f)
    except FileNotFoundError:
        return []

def translate_text(text, src_lang, dest_lang):
    """
    Traduce un texto de un idioma a otro utilizando Google Translate.

    :param text: Texto a traducir.
    :param src_lang: Idioma de origen.
    :param dest_lang: Idioma de destino.
    :return: Texto traducido.
    """
    translated = translator.translate(text, src=src_lang, dest=dest_lang)
    return translated.text
    
def scrape_unusual_articles():
    """
    Extrae los datos de los artículos inusuales de Wikipedia.

    :return: Lista de artículos inusuales.
    """
    cache_file = "data/unusual_articles.json"
    if os.path.exists(cache_file):
        return load_from_json(cache_file)
    
    response = requests.get(BASE_URL)
    soup = BeautifulSoup(response.content, 'html.parser')
    articles = []
    tables = soup.find_all('table', class_='wikitable')

    for table in tables:
        for row in table.find_all('tr'):
            cells = row.find_all(['td', 'th'])
            if len(cells) < 2:
                continue
            
            flag = None
            first_cell = cells[0]

            # Si la primera celda es un <th> con una imagen de bandera, extraerla y omitirla
            if first_cell.name == 'th' and first_cell.find('img'):
                flag_tag = first_cell.find('img')
                if flag_tag:
                    flag = flag_tag['src']
                cells = cells[1:]  # Omitir la celda de la bandera

            if len(cells) < 2:
                continue

            title_cell = cells[0].find_all('a', href=True)

            # Ignorar enlaces a archivos tipo "/wiki/File:"
            title_link = None
            for link in title_cell:
                if not link["href"].startswith("/wiki/File:"):
                    title_link = link
                    break
            
            if not title_link:
                continue  # No se encontró un título válido

            title = title_link.get_text(strip=True)
            link = "https://en.wikipedia.org" + title_link['href']
            description = cells[1].get_text(strip=True)

            articles.append({
                "title": title,
                "link": link,
                "description": description if description else "Descripción no disponible",
                "flag": f"https:{flag}" if flag else None
            })
    
    save_to_json(articles)
    return articles

def generate_embeddings(articles):
    """
    Genera embeddings para los artículos utilizando un modelo de Sentence Transformers.

    :param articles: Lista de artículos.
    :return: Lista de artículos con embeddings.
    """
    # Verificar si los embeddings ya han sido almacenados en caché
    cache_file = "data/article_embeddings.pkl"
    if os.path.exists(cache_file):
        return load_embeddings_pickle(cache_file)
    
    # Generar embeddings para los artículos
    model = SentenceTransformer('all-MiniLM-L6-v2')
    embeddings = []
    for article in articles:            
        embedding = model.encode(article['description'])
        embeddings.append({
            "title": article['title'],
            "link": article['link'],
            "description": article['description'],
            "embedding": embedding
        })
    
    save_embeddings_pickle(embeddings)
    return embeddings

def get_gemini_response(article_data, query):
    """
    Toma un artículo y una consulta y genera una respuesta utilizando Gemini.

    :param article_data: Datos del artículo.
    :return: Respuesta generada por Gemini.
    """
    if not GEMINI_AVAILABLE:
        return f"{article_data['title']}: {article_data['description']}"
    
    prompt = f"""
    El usuario preguntó: {query}.
    Con respecto a la pregunta se tiene: {article_data['title']} que es un artículo inusual de Wikipedia que trata sobre {article_data['description']}.
    Respondele sin omitir el titulo con la menor cantidad de palabras posibles, muy breve, pero con humor inofensivo y sarcasmo.  
    """
    response = chat_session.send_message(prompt) 
    return response.text + " → "

def find_best_match(query, embeddings):
    """
    Encuentra el mejor artículo coincidente con la consulta del usuario.

    :param query: Consulta del usuario.
    :param embeddings: Lista de embeddings de artículos.
    :return: Datos del mejor artículo coincidente.
    """
    # Traducir la consulta a inglés si es necesario
    detected_lang = translator.detect(query).lang
    if detected_lang != "en":
        query = translate_text(query, src_lang=detected_lang, dest_lang="en")
    
    # Generar el embedding de la consulta y calcular similitudes
    model = SentenceTransformer('all-MiniLM-L6-v2')
    query_embedding = model.encode(query)
    similarities = [(cosine_similarity([query_embedding], [entry['embedding']])[0][0], entry) for entry in embeddings]
    similarities.sort(reverse=True, key=lambda x: x[0])
    best_similarity, best_match = similarities[0]
    
    # Comprobar si la similitud es suficiente
    if best_similarity < SIMILARITY_THRESHOLD:
        # Si la similitud es baja, devolver un artículo aleatorio
        with open("funny_responses.txt", "r", encoding="utf-8") as file:
            FUNNY_RESPONSES = [line.strip() for line in file.readlines()]
        response = FUNNY_RESPONSES[np.random.randint(0, len(FUNNY_RESPONSES))]
    else:
        # Si la similitud es suficiente, obtener la respuesta de Gemini si está disponible
        response = (get_gemini_response(best_match, query) if GEMINI_AVAILABLE else f"{best_match['title']}: {best_match['description']}")
    
    # Traducir la respuesta al idioma detectado originalmente
    if translator.detect(response).lang == "en":
        response = translate_text(response, src_lang="en", dest_lang=detected_lang)
    
    return {
        "best_match": best_match["title"],
        "accuracy": best_similarity,
        "link": best_match["link"],
        "response": response,
        "raw_description": best_match["description"]
    }

def search_unusual_article(query):
    """
    Busca un artículo inusual basado en la consulta del usuario.

    :param query: Consulta del usuario.
    :return: Datos del artículo coincidente.
    """
    # Extraer artículos inusuales
    articles = scrape_unusual_articles()

    # Generar embeddings para los artículos
    embeddings = generate_embeddings(articles)

    # Encontrar el mejor artículo coincidente con la consulta
    result = find_best_match(query, embeddings)

    # Añadir el umbral de similitud a los resultados
    result["threshold"] = SIMILARITY_THRESHOLD

    return result
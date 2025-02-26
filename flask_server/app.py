from flask import Flask, request, jsonify
from flask_cors import CORS
import traceback
from scraping_and_search import search_unusual_article
import re

app = Flask(__name__)
CORS(app)  # Habilita CORS para permitir solicitudes desde diferentes orígenes

def markdown_to_html(text):
    """
    Convierte texto en formato Markdown a HTML básico sin afectar URLs dentro de enlaces.

    :param text: Texto en formato Markdown.
    :result text: Texto convertido a HTML.
    """

    links = {}
    
    def replace_link(match):
        """
        Reemplaza un enlace en formato Markdown por una clave única y guarda el enlace en un diccionario.

        :param match: Objeto de coincidencia de expresión regular.
        :result key: Clave única para reemplazar el enlace en el texto.
        """
        full_match = match.group(0)
        text_inside = match.group(1)
        url = match.group(2)
        key = f"{{{{LINK{len(links)}}}}}" 
        links[key] = f'<a href="{url}" target="_blank">{text_inside}</a>'
        return key  
    

    # Reemplazar enlaces con una clave única
    text = re.sub(r'\[(.*?)\]\((https?://[^\s]+)\)', replace_link, text)

    # Reemplazar formato Markdown por HTML
    text = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', text)
    text = re.sub(r'\*(.*?)\*', r'<em>\1</em>', text)
    text = re.sub(r'_(.*?)_', r'<em>\1</em>', text)

    for key, value in links.items():
        text = text.replace(key, value)

    return text

def procesar_consulta(query):
    """
    Procesa la consulta del usuario, busca un artículo inusual y genera una respuesta en HTML.
    
    :param query: Consulta proporcionada por el usuario.
    :result html_response: Respuesta en formato HTML con el contenido y un enlace si la precisión es suficiente.
    """
    result = search_unusual_article(query)
    result['response'] += f" [Ver artículo]({result['link']})"

    # Convertir Markdown a HTML
    response_text = markdown_to_html(result['response'])
    print(response_text)

    return response_text 

@app.route('/status', methods=['GET'])
def status():
    """
    Verifica el estado del servidor.
    
    :result JSON con estado "ok".
    """
    return jsonify({"status": "ok"})

@app.route('/query', methods=['POST'])
def process_query():
    """
    Procesa una consulta enviada por el usuario junto con contenido adicional.
    
    :param query: Texto de la consulta.
    :param content: Contenido relacionado con la consulta.
    :result JSON con la respuesta procesada o un mensaje de error.
    """
    try:
        data = request.json
        query = data.get('query')
        content = data.get('content')
        
        if not query or not content:
            return jsonify({"error": "Se requieren los campos 'query' y 'content'"}), 400
        
        # Procesar la consulta
        response = procesar_consulta(query)
        
        return jsonify({"response": response})
    
    except Exception as e:
        print(f"Error: {str(e)}")
        print(traceback.format_exc())
        return jsonify({"error": str(e)}), 500

@app.route('/chat', methods=['POST'])
def chat():
    """
    Procesa consultas simples sin contenido de página adicional.
    
    :param pregunta: Pregunta enviada por el usuario.
    :result JSON con la respuesta generada o un mensaje de error.
    """
    try:
        data = request.json
        pregunta = data.get('pregunta')
        
        if not pregunta:
            return jsonify({"error": "Se requiere el campo 'pregunta'"}), 400
        
        # Usamos la misma función para procesar consultas
        response = procesar_consulta(pregunta)
        
        return jsonify({"respuesta": response})
    
    except Exception as e:
        print(f"Error: {str(e)}")
        print(traceback.format_exc())
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)

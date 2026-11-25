import os
import requests
import time
from dotenv import load_dotenv

# carga las credenciales del archivo .env
load_dotenv()

# lee el client id y el client secret
client_id = os.getenv("SPOTIFY_CLIENT_ID")
client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")

# guarda el token y el momento en que caduca (inicializa las variables)
token = None
expira_en = 0

# FUNCIÓN : pide un token nuevo a Spotify y lo guarda
def pedir_token():
    global token, expira_en

    # comprueba que las credenciales existen (da error si no están en el archivo .env)
    if client_id is None or client_secret is None:
        raise Exception("Faltan SPOTIFY_CLIENT_ID o SPOTIFY_CLIENT_SECRET en el archivo .env")

    respuesta = requests.post(
        "https://accounts.spotify.com/api/token",       # url del endpoint del token
        auth=(client_id, client_secret),                # envía la cabecera authorization (requests lo codifica en base64)
        data={"grant_type": "client_credentials"},      # envía el cuerpo como formulario (client_credentials (forma de autorización) = la app se identifica sola)
    )
    
    datos = respuesta.json() # interpreta la respuesta como json
    
    # código de estado = 200
    if respuesta.status_code == 200:
        token = datos["access_token"]                   # guarda el token de acceso
        expira_en = time.time() + datos["expires_in"]   # calcula cuando caduca el token (ahora + duración en segundos)

    else:
        raise Exception("Error al obtener el token: " + str(datos))

# FUNCIÓN : devuelve un token válido
def obtener_token():
    # si no hay token o ha caducado pide uno nuevo
    if token is None or time.time() > expira_en - 60: # (1 minuto antes de margen)
        pedir_token()
    return token

# FUNCIÓN : devuelve los datos de una canción a partir de su id
def obtener_cancion(cancion_id):
    access_token = obtener_token() # pide un token válido

    try:
        # envía un get con la cabecera authorization (bearer + token)
        respuesta = requests.get(
            f"https://api.spotify.com/v1/tracks/{cancion_id}",      # url de la canción
            headers={"Authorization": f"Bearer {access_token}"},    # envía la cabecera authorization (bearer + access token)
        )
    except requests.exceptions.RequestException:  # no se puede conectar con Spotify
        return {"error": "No se ha podido conectar con Spotify"}

    # código de estado = 200
    if respuesta.status_code == 200:
        return respuesta.json() # interpreta la respuesta como json
    else:
        return {"error": "Spotify ha devuelto un error (código " + str(respuesta.status_code) + ")"}

# FUNCIÓN : devuelve los datos de un artista a partir de su id
def obtener_artista(artista_id):
    access_token = obtener_token() # pide un token válido

    try:
        # envía un get con la cabecera authorization (bearer + token)
        respuesta = requests.get(
            f"https://api.spotify.com/v1/artists/{artista_id}",     # url del artista
            headers={"Authorization": f"Bearer {access_token}"},    # envía la cabecera authorization (bearer + access token)
        )
    except requests.exceptions.RequestException:  # no se puede conectar con Spotify
        return {"error": "No se ha podido conectar con Spotify"}

    # código de estado = 200
    if respuesta.status_code == 200:
        return respuesta.json() # interpreta la respuesta como json
    else:
        return {"error": "Spotify ha devuelto un error (código " + str(respuesta.status_code) + ")"}

# FUNCIÓN : busca canciones o artistas en Spotify
def buscar(texto, tipo):
    access_token = obtener_token() # pide un token válido

    try:
        # envía un get con la cabecera authorization y los parámetros de la búsqueda
        respuesta = requests.get(
            "https://api.spotify.com/v1/search",                                # url de la búsqueda
            headers={"Authorization": f"Bearer {access_token}"},                # envía la cabecera authorization (bearer + access token)
            params={"q": texto, "type": tipo, "limit": 10, "market": "ES"},     # requests construye la url con estos parámetros
        )
    except requests.exceptions.RequestException:  # no se puede conectar con Spotify
        return {"error": "No se ha podido conectar con Spotify"}

    # código de estado = 200
    if respuesta.status_code == 200:
        return respuesta.json() # interpreta la respuesta como json
    else:
        return {"error": "Spotify ha devuelto un error (código " + str(respuesta.status_code) + ")"}
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from configuration.connections import make_connection
from service.spotify_service import buscar, obtener_cancion, obtener_artista
from typing import Literal

app = FastAPI()  # crea la aplicación

# CLASES DE PYDANTIC PARA VALIDAR DATOS

# define los datos que admite un usuario
class UserCreate(BaseModel):
    nombre: str = Field(..., min_length=1, max_length=50)
    email: str = Field(..., min_length=1, max_length=100)

# define los datos que admite una preferencia de usuario
class PreferenciaCreate(BaseModel):
    spotify_id: str = Field(..., min_length=1, max_length=50)
    tipo: Literal["track", "artist"]
    valoracion: Literal["like", "dislike"]

# define los datos que admite una playlist
class PlaylistCreate(BaseModel):
    nombre: str = Field(..., min_length=1, max_length=100)

# define los datos que admite una canción de una playlist
class PlaylistCancionCreate(BaseModel):
    spotify_id: str = Field(..., min_length=1, max_length=50)

# ENDPOINTS

@app.get("/")  # responde a los GET de "/"
def root():
    return {"message": "Hola Mundo"}  # devuelve un diccionario + FastAPI lo pasa a JSON

# endpoints de usuarios, preferencias y playlists:
    # 1. abre la conexión make_connection() y el cursor mydb.cursor()
    # 2. ejecuta la consulta mycursor.execute(CONSULTA)
    # 3. hace commit mydb.commit() si cambia datos (insert, update, delete)
    # 4. cierra el cursor mycursor.close() y la conexión mydb.close() 
    # 5. devuelve la respuesta o lanza un error (404 si no existe / 409 si ya existe)

# GESTIÓN DE USUARIOS

# ENDPOINT : crea un usuario
@app.post("/usuarios")
def post_usuario(user: UserCreate):
    mydb = make_connection()
    mycursor = mydb.cursor()

    # mira que no exista el email
    mycursor.execute("SELECT id FROM usuarios WHERE email = %s", (user.email,))
    if mycursor.fetchone() is not None:  # el email ya existe
        mycursor.close()
        mydb.close()
        raise HTTPException(status_code=409, detail="El email ya existe")

    # crea el usuario
    mycursor.execute("INSERT INTO usuarios (nombre, email) VALUES (%s, %s)", (user.nombre, user.email))
    mydb.commit()
    mycursor.close()
    mydb.close()
    return JSONResponse(content={"message": "Usuario creado"}, status_code=201)

# ENDPOINT : devuelve todos los usuarios
@app.get("/usuarios")
def get_usuarios():
    mydb = make_connection()
    mycursor = mydb.cursor()
    mycursor.execute("SELECT * FROM usuarios") # pide todas las filas de la tabla
    res = mycursor.fetchall() # recoge todas las filas
    mycursor.close()
    mydb.close()
    return res # devuelve la lista de filas encontradas

# ENDPOINT : devuelve un usuario por su id
@app.get("/usuarios/{user_id}")
def get_usuario(user_id: int):
    mydb = make_connection()
    mycursor = mydb.cursor()
    mycursor.execute("SELECT * FROM usuarios WHERE id = %s", (user_id,)) # pide la fila con ese id
    res = mycursor.fetchone() # recoge una sola fila (si hay)
    mycursor.close()
    mydb.close()
    
    if res is None: # no existe el usuario
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return res # devuelve la fila encontrada

# ENDPOINT : actualiza un usuario por su id
@app.put("/usuarios/{user_id}")
def put_usuario(user_id: int, user: UserCreate):
    mydb = make_connection()
    mycursor = mydb.cursor()
    
    # mira que exista el usuario
    mycursor.execute("SELECT id FROM usuarios WHERE id = %s", (user_id,))
    existe = mycursor.fetchone()
    if existe is None: # no existe el usuario
        mycursor.close()
        mydb.close()
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    # mira que el email no sea de otro usuario
    mycursor.execute("SELECT id FROM usuarios WHERE email = %s AND id != %s", (user.email, user_id))
    if mycursor.fetchone() is not None:  # el email ya existe
        mycursor.close()
        mydb.close()
        raise HTTPException(status_code=409, detail="El email ya existe")

    # actualiza el usuario
    mycursor.execute("UPDATE usuarios SET nombre = %s, email = %s WHERE id = %s", (user.nombre, user.email, user_id))
    mydb.commit()
    mycursor.close()
    mydb.close()
    return JSONResponse(content={"message": "Usuario actualizado"}, status_code=200)

# ENDPOINT : borra un usuario por su id
@app.delete("/usuarios/{user_id}")
def delete_usuario(user_id: int):
    mydb = make_connection()
    mycursor = mydb.cursor()
    mycursor.execute("DELETE FROM usuarios WHERE id = %s", (user_id,)) # borra la fila con ese id
    mydb.commit()
    filas = mycursor.rowcount # guarda cuantas filas ha borrado
    mycursor.close()
    mydb.close()

    if filas == 0: # no existe el usuario
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return JSONResponse(content={"message": "Usuario borrado"}, status_code=200)

# BÚSQUEDA DE SPOTIFY

# ENDPOINT : busca canciones o artistas en Spotify
@app.get("/buscar")
def buscar_spotify(q: str, tipo: Literal["track", "artist"] = "track"):  # q (obligatorio): texto de búsqueda / tipo (opcional) qué buscar (track por defecto o artist)
    datos = buscar(q, tipo)
    
    # Spotify falla o no responde
    if "error" in datos:  
        raise HTTPException(status_code=502, detail=datos["error"])
    return datos  # devuelve los resultados de Spotify

# GESTIÓN DE PREFERENCIAS (LIKE / DISLIKE)

# ENDPOINT : da like o dislike a una canción o artista (o cambia la valoración si ya existe)
@app.post("/usuarios/{user_id}/preferencias")
def dar_preferencia(user_id: int, preferencia: PreferenciaCreate):
    mydb = make_connection()
    mycursor = mydb.cursor()

    # mira que exista el usuario
    mycursor.execute("SELECT id FROM usuarios WHERE id = %s", (user_id,))
    if mycursor.fetchone() is None:  # no existe el usuario
        mycursor.close()
        mydb.close()
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    # mira si ya existe la preferencia
    mycursor.execute("SELECT id FROM preferencias WHERE usuario_id = %s AND spotify_id = %s AND tipo = %s", (user_id, preferencia.spotify_id, preferencia.tipo))
    preferencia_existente = mycursor.fetchone()

    if preferencia_existente: # actualiza la valoración (existe)
        mycursor.execute("UPDATE preferencias SET valoracion = %s WHERE id = %s", (preferencia.valoracion, preferencia_existente[0]))
        mensaje, codigo = "Preferencia actualizada", 200
        
    else: # crea la preferencia (no existe)
        mycursor.execute("INSERT INTO preferencias (usuario_id, spotify_id, tipo, valoracion) VALUES (%s, %s, %s, %s)", (user_id, preferencia.spotify_id, preferencia.tipo, preferencia.valoracion))
        mensaje, codigo = "Preferencia creada", 201

    mydb.commit()
    mycursor.close()
    mydb.close()
    return JSONResponse(status_code=codigo, content={"message": mensaje})

# ENDPOINT : devuelve las preferencias de un usuario
@app.get("/usuarios/{user_id}/preferencias")
def get_preferencias(user_id: int):
    mydb = make_connection()
    mycursor = mydb.cursor()

    # mira que exista el usuario
    mycursor.execute("SELECT id FROM usuarios WHERE id = %s", (user_id,))
    if mycursor.fetchone() is None:  # no existe el usuario
        mycursor.close()
        mydb.close()
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    # recoge todas las preferencias del usuario
    mycursor.execute("SELECT id, spotify_id, tipo, valoracion FROM preferencias WHERE usuario_id = %s", (user_id,))
    res = mycursor.fetchall()
    mycursor.close()
    mydb.close()
    return res

# ENDPOINT : devuelve las canciones y artistas con like de un usuario (con los datos de Spotify)
@app.get("/usuarios/{user_id}/favoritos")
def get_favoritos(user_id: int):
    mydb = make_connection()
    mycursor = mydb.cursor()

    # mira que exista el usuario
    mycursor.execute("SELECT id FROM usuarios WHERE id = %s", (user_id,))
    if mycursor.fetchone() is None:  # no existe el usuario
        mycursor.close()
        mydb.close()
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    # recoge los likes del usuario
    mycursor.execute("SELECT spotify_id, tipo FROM preferencias WHERE usuario_id = %s AND valoracion = 'like'", (user_id,))
    likes = mycursor.fetchall()
    mycursor.close()
    mydb.close()

    # pide a Spotify los datos de cada like
    favoritos = []
    for spotify_id, tipo in likes:
        if tipo == "track":
            datos = obtener_cancion(spotify_id)
        else:
            datos = obtener_artista(spotify_id)
            
        if "error" in datos:  # Spotify falla o no responde
            raise HTTPException(status_code=502, detail=datos["error"])
        favorito = {"spotify_id": spotify_id, "tipo": tipo, "nombre": datos["name"]}
        if tipo == "track":  # añade el artista de la canción
            favorito["artista"] = datos["artists"][0]["name"]
        favoritos.append(favorito)
    return favoritos

# ENDPOINT : borra una preferencia de un usuario (la deja sin valoración)
@app.delete("/usuarios/{user_id}/preferencias/{preferencia_id}")
def delete_preferencia(user_id: int, preferencia_id: int):
    mydb = make_connection()
    mycursor = mydb.cursor()
    
    # borra la preferencia
    mycursor.execute("DELETE FROM preferencias WHERE id = %s AND usuario_id = %s", (preferencia_id, user_id))
    mydb.commit()
    filas = mycursor.rowcount  # guarda cuántas filas ha borrado
    mycursor.close()
    mydb.close()
    
    if filas == 0: # no existe la preferencia
        raise HTTPException(status_code=404, detail="Preferencia no encontrada")
    return JSONResponse(content={"message": "Preferencia borrada"}, status_code=200)

# GESTIÓN DE PLAYLISTS

# ENDPOINT : crea una playlist para un usuario
@app.post("/usuarios/{user_id}/playlists")
def post_playlist(user_id: int, playlist: PlaylistCreate):
    mydb = make_connection()
    mycursor = mydb.cursor()

    # mira que exista el usuario
    mycursor.execute("SELECT id FROM usuarios WHERE id = %s", (user_id,))
    if mycursor.fetchone() is None:  # no existe el usuario
        mycursor.close()
        mydb.close()
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    # crea la playlist
    mycursor.execute("INSERT INTO playlists (usuario_id, nombre) VALUES (%s, %s)", (user_id, playlist.nombre))
    mydb.commit()
    mycursor.close()
    mydb.close()
    return JSONResponse(content={"message": "Playlist creada"}, status_code=201)

# ENDPOINT : devuelve las playlists de un usuario
@app.get("/usuarios/{user_id}/playlists")
def get_playlists(user_id: int):
    mydb = make_connection()
    mycursor = mydb.cursor()

    # mira que exista el usuario
    mycursor.execute("SELECT id FROM usuarios WHERE id = %s", (user_id,))
    if mycursor.fetchone() is None:  # no existe el usuario
        mycursor.close()
        mydb.close()
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    # recoge todas las playlists del usuario
    mycursor.execute("SELECT id, nombre, creado FROM playlists WHERE usuario_id = %s", (user_id,))
    res = mycursor.fetchall()
    mycursor.close()
    mydb.close()
    return res

# ENDPOINT : devuelve una playlist de un usuario con sus canciones
@app.get("/usuarios/{user_id}/playlists/{playlist_id}")
def get_playlist(user_id: int, playlist_id: int):
    mydb = make_connection()
    mycursor = mydb.cursor()

    # recoge la playlist (solo si es de ese usuario)
    mycursor.execute("SELECT id, usuario_id, nombre, creado FROM playlists WHERE id = %s AND usuario_id = %s", (playlist_id, user_id))
    playlist = mycursor.fetchone()
    if playlist is None:  # no existe la playlist
        mycursor.close()
        mydb.close()
        raise HTTPException(status_code=404, detail="Playlist no encontrada")

    # recoge los ids de Spotify de sus canciones
    mycursor.execute("SELECT spotify_id FROM playlist_canciones WHERE playlist_id = %s", (playlist_id,))
    filas = mycursor.fetchall()
    mycursor.close()
    mydb.close()
    return {"playlist": playlist, "canciones": [fila[0] for fila in filas]}

# ENDPOINT : cambia el nombre de una playlist de un usuario
@app.put("/usuarios/{user_id}/playlists/{playlist_id}")
def put_playlist(user_id: int, playlist_id: int, playlist: PlaylistCreate):
    mydb = make_connection()
    mycursor = mydb.cursor()

    # mira que exista la playlist (solo si es de ese usuario)
    mycursor.execute("SELECT id FROM playlists WHERE id = %s AND usuario_id = %s", (playlist_id, user_id))
    if mycursor.fetchone() is None:  # no existe la playlist
        mycursor.close()
        mydb.close()
        raise HTTPException(status_code=404, detail="Playlist no encontrada")

    # actualiza el nombre
    mycursor.execute("UPDATE playlists SET nombre = %s WHERE id = %s", (playlist.nombre, playlist_id))
    mydb.commit()
    mycursor.close()
    mydb.close()
    return JSONResponse(content={"message": "Playlist actualizada"}, status_code=200)

# ENDPOINT : borra una playlist de un usuario y sus canciones
@app.delete("/usuarios/{user_id}/playlists/{playlist_id}")
def delete_playlist(user_id: int, playlist_id: int):
    mydb = make_connection()
    mycursor = mydb.cursor()
    mycursor.execute("DELETE FROM playlists WHERE id = %s AND usuario_id = %s", (playlist_id, user_id))  # borra la fila con ese id
    mydb.commit()
    filas = mycursor.rowcount  # guarda cuántas filas ha borrado
    mycursor.close()
    mydb.close()

    if filas == 0:  # no existe la playlist
        raise HTTPException(status_code=404, detail="Playlist no encontrada")
    return JSONResponse(content={"message": "Playlist borrada"}, status_code=200)

# GESTIÓN DE CANCIONES DE UNA PLAYLIST

# ENDPOINT : añade una canción a una playlist de un usuario
@app.post("/usuarios/{user_id}/playlists/{playlist_id}/canciones")
def post_cancion_playlist(user_id: int, playlist_id: int, cancion: PlaylistCancionCreate):
    mydb = make_connection()
    mycursor = mydb.cursor()

    # mira que exista la playlist (solo si es de ese usuario)
    mycursor.execute("SELECT id FROM playlists WHERE id = %s AND usuario_id = %s", (playlist_id, user_id))
    if mycursor.fetchone() is None:  # no existe la playlist
        mycursor.close()
        mydb.close()
        raise HTTPException(status_code=404, detail="Playlist no encontrada")

    # mira si la canción ya está en la playlist
    mycursor.execute("SELECT id FROM playlist_canciones WHERE playlist_id = %s AND spotify_id = %s", (playlist_id, cancion.spotify_id))
    if mycursor.fetchone() is not None:  # la canción ya está en la playlist
        mycursor.close()
        mydb.close()
        raise HTTPException(status_code=409, detail="La canción ya está en la playlist")

    # añade la canción
    mycursor.execute("INSERT INTO playlist_canciones (playlist_id, spotify_id) VALUES (%s, %s)", (playlist_id, cancion.spotify_id))
    mydb.commit()
    mycursor.close()
    mydb.close()
    return JSONResponse(content={"message": "Canción añadida"}, status_code=201)

# ENDPOINT : quita una canción de una playlist de un usuario
@app.delete("/usuarios/{user_id}/playlists/{playlist_id}/canciones/{spotify_id}")
def delete_cancion_playlist(user_id: int, playlist_id: int, spotify_id: str):
    mydb = make_connection()
    mycursor = mydb.cursor()

    # mira que exista la playlist (solo si es de ese usuario)
    mycursor.execute("SELECT id FROM playlists WHERE id = %s AND usuario_id = %s", (playlist_id, user_id))
    if mycursor.fetchone() is None:  # no existe la playlist
        mycursor.close()
        mydb.close()
        raise HTTPException(status_code=404, detail="Playlist no encontrada")

    # quita la canción
    mycursor.execute("DELETE FROM playlist_canciones WHERE playlist_id = %s AND spotify_id = %s", (playlist_id, spotify_id))
    mydb.commit()
    filas = mycursor.rowcount  # guarda cuántas filas ha borrado
    mycursor.close()
    mydb.close()

    if filas == 0:  # no existe la canción en la playlist
        raise HTTPException(status_code=404, detail="Canción no encontrada en la playlist")
    return JSONResponse(content={"message": "Canción quitada"}, status_code=200)
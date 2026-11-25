-- crea la base de datos de la api
CREATE DATABASE IF NOT EXISTS api_musica;

-- selecciona la base de datos para usarla
USE api_musica;

-- crea la tabla de usuarios
CREATE TABLE IF NOT EXISTS usuarios (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(50) NOT NULL,
    email VARCHAR(100) NOT NULL UNIQUE,
    creado TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- crea la tabla de preferencias (likes y dislikes)
CREATE TABLE IF NOT EXISTS preferencias (
    id INT AUTO_INCREMENT PRIMARY KEY,
    usuario_id INT NOT NULL,                                -- id del usuario dueño de la preferencia
    spotify_id VARCHAR(50) NOT NULL,                        -- id de spotify de la canción o artista
    tipo ENUM('track', 'artist') NOT NULL,               	-- solo admite track o artist
    valoracion ENUM('like', 'dislike') NOT NULL,            -- solo admite like o dislike
    creado TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE,  	-- exige que el usuario exista y borra sus preferencias si se borra
    UNIQUE (usuario_id, spotify_id, tipo)                   				-- impide repetir la misma canción o artista para un usuario
);

-- crea la tabla de playlists
CREATE TABLE IF NOT EXISTS playlists (
    id INT AUTO_INCREMENT PRIMARY KEY,
    usuario_id INT NOT NULL,                                -- id del usuario dueño de la playlist
    nombre VARCHAR(100) NOT NULL,
    creado TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE   	-- exige que el usuario exista y borra sus playlists si se borra
);

-- crea la tabla de canciones de cada playlist
CREATE TABLE IF NOT EXISTS playlist_canciones (
    id INT AUTO_INCREMENT PRIMARY KEY,
    playlist_id INT NOT NULL,                               -- id de la playlist a la que pertenece
    spotify_id VARCHAR(50) NOT NULL,                        -- id de spotify de la canción
    agregada TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (playlist_id) REFERENCES playlists(id) ON DELETE CASCADE,  -- exige que la playlist exista y borra sus canciones si se borra
    UNIQUE (playlist_id, spotify_id)                        				-- impide repetir la misma canción en una playlist
);
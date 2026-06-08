================================================================================
              MANUAL DE JUEGO Y GUÍA DE USUARIO - BRICKSCRIPT
================================================================================

BrickScript es un motor unificado que permite ejecutar juegos clásicos de estilo
"Brick Game" (como Tetris, Snake y Tanques) a partir de archivos con código script 
personalizado (.brick).

--------------------------------------------------------------------------------
1. CÓMO JUGAR A CADA JUEGO
--------------------------------------------------------------------------------

### TETRIS ORIGINAL
- Archivo del juego: `games/tetris.brick`
- Cómo ejecutar:
    jugar.bat tetris
- Jugabilidad:
  Tetris clásico con las 7 piezas tradicionales (I, J, L, O, S, T, Z) y caída
  de gravedad estándar. Completa líneas para ganar puntos.
- Controles:
  * Flecha Izquierda: Mover a la izquierda.
  * Flecha Derecha: Mover a la derecha.
  * Flecha Abajo: Acelerar caída.
  * Flecha Arriba: Rotar pieza.

### TETRIS REMAKE (EXTENDIDO)
- Archivo del juego: `games/tetris_extended.brick`
- Cómo ejecutar:
    jugar.bat tetris_extended
- Jugabilidad:
  Tetris extendido con piezas no convencionales (P_PIECE y V_PIECE), colores 
  personalizados, probabilidades de aparición de piezas (`CHANCE`), y el
  Power-Up GEM_POWERUP (un bloque especial que limpia celdas).
- Controles: Mismos controles que la versión original.

---

### SNAKE ORIGINAL
- Archivo del juego: `games/snake.brick`
- Cómo ejecutar:
    jugar.bat snake
- Jugabilidad:
  Controla a la serpiente para comer manzanas rojas y crecer. Chocar con la
  pared o contra ti mismo causa Game Over inmediato.
- Controles:
  * Flechas Direccionales: Cambiar de dirección (Arriba, Abajo, Izquierda, Derecha).

### SNAKE EVOLUCIONADO
- Archivo del juego: `games/snake_evolved.brick`
- Cómo ejecutar:
    jugar.bat snake_evolved
- Jugabilidad:
  Elige entre 3 niveles de dificultad al iniciar (Baby, Enthusiast, Nyan Cat).
  * Baby: Velocidad moderada, sin peligros.
  * Enthusiast: Añade fruta venenosa (morada) y frutas inmortales (amarillas).
  * Nyan Cat: Velocidad extrema, cuerpo arcoíris, cabeza Nyan Cat y nubes como obstáculos.
- Controles: Mismos controles que la versión original.

---

### BRICK TANKS (NUEVO)
- Archivo del juego: `games/tanks.brick`
- Cómo ejecutar:
    jugar.bat tanks
- Jugabilidad:
  Juego de combate táctico de tanques. Eres un tanque azul (`PLAYER_TANK`) y
  debes destruir los tanques enemigos rojos y naranjas.
  * Muros Destructibles: Los bloques grises son muros que puedes destruir disparando.
  * Vida y Daño: Tienes barra de HP (puntos de vida). Los enemigos también te disparan.
  * Martillo Reparador: Aparece aleatoriamente y cura 50 HP.
  * Final Boss: Al llegar a 1000 puntos de score, los enemigos normales desaparecen y
    te enfrentas a la **FINAL_FORTRESS** (una fortaleza gigante de 5x5) que
    dispara ráfagas de proyectiles en múltiples direcciones. ¡Derrótala para ganar!
- Controles:
  * Flecha Arriba/Abajo/Izquierda/Derecha: Mover tanque en la dirección seleccionada.
  * Barra Espaciadora: Disparar proyectil.

--------------------------------------------------------------------------------
2. ENLACE AL VIDEO DE INTEGRACIÓN
--------------------------------------------------------------------------------
El video demostrativo muestra el funcionamiento sin errores de compilación ni 
ejecución de todos los juegos desde el mismo compilador (`compiler.py`) y 
ejecutable (`runtime.py`):

* **Enlace del Video:** https://drive.google.com/file/d/1vCExh2vD4tW-8Jb09yG-1bZ8Z3vD4k9/view?usp=sharing

================================================================================
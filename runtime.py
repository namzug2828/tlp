import sys
import json
import time
import random

try:
    import pygame
    HAS_PYGAME = True
except ImportError:
    HAS_PYGAME = False

if not HAS_PYGAME:
    class DummySound:
        def __init__(self, *args, **kwargs): pass
        def play(self, *args, **kwargs): pass
        def stop(self, *args, **kwargs): pass

    class DummyMusic:
        def load(self, *args, **kwargs): pass
        def play(self, *args, **kwargs): pass
        def stop(self, *args, **kwargs): pass

    class DummyMixer:
        def init(self, *args, **kwargs): pass
        music = DummyMusic()
        Sound = DummySound

    class DummyPygame:
        mixer = DummyMixer()
    
    pygame = DummyPygame()

try:
    import Tkinter as tk
    import tkMessageBox
except ImportError:
    import tkinter as tk
    from tkinter import messagebox as tkMessageBox

class Juego:
    def __init__(self, datos_juego):
        self.datos_juego = datos_juego
        self.tipo_juego = self.datos_juego.get('tipo_juego', 'TETRIS')
        config = self.datos_juego.get('config', {})
        self.ancho = config.get('grid_size', [10, 20])[0]
        self.alto = config.get('grid_size', [10, 20])[1]
        self.grid = [[0 for _ in range(self.ancho)] for _ in range(self.alto)]
        self.puntuacion = 0
        self.juego_terminado = False

        self.root = tk.Tk()

        pygame.mixer.init()

        
        if self.tipo_juego == 'TETRIS':
        
            pygame.mixer.music.load("assets/SIN_SENTIMIENTO.mp3")
            pygame.mixer.music.play(-1)

        elif self.tipo_juego == 'SNAKE':
        
            pygame.mixer.music.load("assets/DRAGON_BALL.mp3")
            pygame.mixer.music.play(-1)

        elif self.tipo_juego == 'TANKS':
        
            pygame.mixer.music.load("assets/TE_ENTIENDO.mp3")
            pygame.mixer.music.play(-1)

        

        # Efectos
        self.sonido_disparo = pygame.mixer.Sound(
            "assets/DISPARO.wav"
        )

        self.sonido_danio = pygame.mixer.Sound(
            "assets/DANO.wav"
        )

        self.sonido_hammer = pygame.mixer.Sound(
            "assets/HAMMER.wav"
        )

        self.root.title("BrickScript - " + self.tipo_juego)
        self.root.protocol("WM_DELETE_WINDOW", self.cerrar_ventana)

        self.taman_celda = 25
        self.ancho_canvas = self.ancho * self.taman_celda
        self.alto_canvas = self.alto * self.taman_celda

        self.canvas = tk.Canvas(self.root, width=self.ancho_canvas, height=self.alto_canvas, bg='#111111')
        self.canvas.pack(side=tk.LEFT, padx=10, pady=10)

        self.marco_score = tk.Frame(self.root, width=150, height=self.alto_canvas, bg='#222222')
        self.marco_score.pack(side=tk.RIGHT, fill=tk.Y, padx=10, pady=10)

        self.label_score = tk.Label(self.marco_score, text="PUNTUACION\n0", bg='#222222', fg='white', font=('Consolas', 16, 'bold'))
        self.label_score.pack(pady=40, padx=10)

        self.label_controles = tk.Label(self.marco_score, text="CONTROLES\nFlechas: Mover/Rotar", bg='#222222', fg='gray', font=('Consolas', 10))
        self.label_controles.pack(pady=20, padx=10)


        self.root.bind('<Key>', self.manejar_input_gui)

        self.shapes = {}
        for nombre, datos in self.datos_juego.get('shapes', {}).items():
            if isinstance(datos, list):
                self.shapes[nombre] = {
                    "color": "#00FFFF",
                    "chance": 10,
                    "states": datos,
                    "form": datos.get("form", "RECTANGLE")
                }
            elif isinstance(datos, dict):
                self.shapes[nombre] = {
                    "color": datos.get("color", "#00FFFF"),
                    "chance": int(datos.get("chance", 10)),
                    "states": datos.get("states", []),
                    "form": datos.get("form", "RECTANGLE")
                }

        self.powerups = {}

        for nombre, datos in self.datos_juego.get('powerups', {}).items():

            if isinstance(datos, dict):

                self.powerups[nombre] = {

                "color": datos.get("color", "#FFD700"),
                "chance": int(datos.get("chance", 0)),
                "states": datos.get("states", []),
                "form": datos.get("form", "RECTANGLE")
                }

        self.obstacles = {}

        for nombre, datos in self.datos_juego.get('obstacles', {}).items():

            if isinstance(datos, dict):

                self.obstacles[nombre] = {

                    "color": datos.get(
                        "color",
                        "#AAAAAA"
                    ),

                    "form": datos.get(
                        "form",
                        "CIRCLE"
                    )
                }

        if self.tipo_juego == 'TETRIS':
            self.pieza_actual = None
            self.pieza_x, self.pieza_y, self.pieza_rotacion = 0, 0, 0
            self.velocidad_gravedad = 0.4
            self.nombre_pieza_actual = None

            self.lineas_3_simultaneas = False

        if self.tipo_juego == 'SNAKE':

            self.serpiente_cuerpo = []
            self.serpiente_direccion = (1, 0)
            self.posicion_manzana = None
            self.posiciones_veneno = []
            self.posiciones_obstaculos = []
            self.contador_rondas = 0
            self.posicion_powerup = None
            self.inmune = False
            self.tiempo_inmunidad = 0
            self.contador_rondas = 0
            self.velocidad_gravedad = 0.15
            if self.datos_juego.get('levels'):
                self.nivel_actual = self.seleccionar_nivel()
            else:
                self.nivel_actual = "BABY"
            self.configurar_nivel()

        if self.tipo_juego == 'TANKS':

            self.player_x = 0
            self.player_y = 0
            self.player_w = 1
            self.player_h = 1
            self.player_hp = 200
            self.player_max_hp = 200
            self.player_color = "#0000FF"
            self.player_direccion = "UP"

            for name, shape in self.shapes.items():
                if shape.get('type') == 'PLAYER':
                    self.player_hp = shape.get('hp', 200)
                    self.player_max_hp = self.player_hp
                    self.player_color = shape.get('color', '#0000FF')
                    if shape.get('states'):
                        self.player_w = len(shape['states'][0][0])
                        self.player_h = len(shape['states'][0])
                    break

            self.enemigos = []
            self.enemigos_rapidos = []

            self.balas_jugador = []
            self.balas_enemigos = []

            self.posicion_hammer = None

            self.boss_activo = False
            self.boss_hp = 0
            self.boss_x = 0
            self.boss_y = 0

            self.timer_enemigos = 0

            self.velocidad_gravedad = 0.05
            self.tanks_generar_muros()

        self.timer_gravedad = 0
        self.ejecutar_evento('ON_START')
        self.timer_id = None


    def run(self):
        self.root.after(50, self.game_loop)
        self.root.mainloop()

    def game_loop(self):

        if self.tipo_juego == 'TANKS':

            self.tanks_game_tick()

        if self.juego_terminado:
            self.mostrar_game_over()
            return

        self.timer_gravedad += 0.05
        if self.timer_gravedad >= self.velocidad_gravedad:
            self.timer_gravedad = 0
            self.ejecutar_evento('ON_TICK')

        self.dibujar()

        self.timer_id = self.root.after(50, self.game_loop)

    def cerrar_ventana(self):
        pygame.mixer.music.stop()
        if self.timer_id:
            self.root.after_cancel(self.timer_id)
        self.root.destroy()
        sys.exit(0)


    def manejar_input_gui(self, event):
        key = event.keysym.upper()


        if self.tipo_juego == 'TETRIS':
            if key == 'UP': self.ejecutar_evento('ON_KEY_UP')
            elif key == 'DOWN': self.ejecutar_evento('ON_KEY_DOWN')
            elif key == 'LEFT': self.ejecutar_evento('ON_KEY_LEFT')
            elif key == 'RIGHT': self.ejecutar_evento('ON_KEY_RIGHT')
        elif self.tipo_juego == 'SNAKE':
            if key == 'UP': self.snake_cambiar_direccion('UP')
            elif key == 'DOWN': self.snake_cambiar_direccion('DOWN')
            elif key == 'LEFT': self.snake_cambiar_direccion('LEFT')
            elif key == 'RIGHT': self.snake_cambiar_direccion('RIGHT')

        elif self.tipo_juego == 'TANKS':

            if key == 'UP':
                if 'ON_KEY_UP' in self.datos_juego.get('events', {}):
                    self.ejecutar_evento('ON_KEY_UP')
                else:
                    self.player_direccion = "UP"
                    self.tanks_mover_jugador(0, -1)

            elif key == 'DOWN':
                if 'ON_KEY_DOWN' in self.datos_juego.get('events', {}):
                    self.ejecutar_evento('ON_KEY_DOWN')
                else:
                    self.player_direccion = "DOWN"
                    self.tanks_mover_jugador(0, 1)

            elif key == 'LEFT':
                if 'ON_KEY_LEFT' in self.datos_juego.get('events', {}):
                    self.ejecutar_evento('ON_KEY_LEFT')
                else:
                    self.player_direccion = "LEFT"
                    self.tanks_mover_jugador(-1, 0)

            elif key == 'RIGHT':
                if 'ON_KEY_RIGHT' in self.datos_juego.get('events', {}):
                    self.ejecutar_evento('ON_KEY_RIGHT')
                else:
                    self.player_direccion = "RIGHT"
                    self.tanks_mover_jugador(1, 0)

            elif key == 'SPACE':
                if 'ON_KEY_SPACE' in self.datos_juego.get('events', {}):
                    self.ejecutar_evento('ON_KEY_SPACE')
                else:
                    self.tanks_disparar()

    def seleccionar_nivel(self):

        ventana = tk.Toplevel(self.root)

        ventana.title("Seleccionar dificultad")
        ventana.geometry("300x200")

        nivel = tk.StringVar()
        nivel.set("BABY")

        tk.Label(
            ventana,
            text="Seleccione dificultad",
            font=("Consolas", 12)
        ).pack(pady=10)

        tk.Radiobutton(
            ventana,
            text="Baby",
            variable=nivel,
            value="BABY"
        ).pack()

        tk.Radiobutton(
            ventana,
            text="Enthusiast",
            variable=nivel,
            value="ENTHUSIAST"
        ).pack()

        tk.Radiobutton(
            ventana,
            text="Nyan Cat",
            variable=nivel,
            value="NYAN_CAT"
        ).pack()

        resultado = [None]

        def aceptar():
            resultado[0] = nivel.get()
            ventana.destroy()

        tk.Button(
            ventana,
            text="Jugar",
            command=aceptar
        ).pack(pady=15)

        ventana.transient(self.root)
        ventana.grab_set()

        self.root.wait_window(ventana)

        return resultado[0]


    def configurar_nivel(self):

        self.veneno_habilitado = False
        self.obstaculos_habilitados = False
        self.powerup_habilitado = False

        level_data = {}
        if self.datos_juego.get('levels'):
            nivel_keys = self.datos_juego['levels'].keys()
            matched_key = None
            for key in nivel_keys:
                if key.upper() == self.nivel_actual.upper():
                    matched_key = key
                    break
                if "ENTHU" in key.upper() and "ENTHU" in self.nivel_actual.upper():
                    matched_key = key
                    break
                if "ENTUS" in key.upper() and "ENTHU" in self.nivel_actual.upper():
                    matched_key = key
                    break
            
            if matched_key:
                level_data = self.datos_juego['levels'][matched_key]

        if level_data:
            speed_val = level_data.get("speed", 0.15)
            if speed_val > 1:
                self.velocidad_gravedad = speed_val / 1000.0
            else:
                self.velocidad_gravedad = speed_val
        else:
            if self.nivel_actual == "BABY":
                self.velocidad_gravedad = 0.15
            elif self.nivel_actual == "ENTHUSIAST":
                self.velocidad_gravedad = 0.12
            elif self.nivel_actual == "NYAN_CAT":
                self.velocidad_gravedad = 0.08

        if self.nivel_actual == "ENTHUSIAST":
            self.veneno_habilitado = True
            self.powerup_habilitado = True
        elif self.nivel_actual == "NYAN_CAT":
            self.veneno_habilitado = True
            self.obstaculos_habilitados = True
            self.powerup_habilitado = True


    def dibujar(self):
        self.canvas.delete("all")
        texto = "PUNTUACION\n" + str(self.puntuacion)

        if self.tipo_juego == 'TANKS':

            texto += "\n\nHP\n" + str(self.player_hp)

        self.label_score.config(text=texto)

        COLOR_GRID_FIJA = '#343434'
        COLOR_PIEZA = '#00FFFF'
        COLOR_SNAKE_CABEZA = '#00FF00'
        COLOR_SNAKE_CUERPO = '#33CC33'
        COLOR_FOOD = '#FF0000'

        for y in range(self.alto):
            for x in range(self.ancho):
                val_celda = self.grid[y][x]
                if val_celda != 0:
                     color = val_celda if not isinstance(val_celda, int) else COLOR_GRID_FIJA
                     self.dibujar_celda(x, y, color)

        if self.tipo_juego == 'TETRIS' and self.pieza_actual:
            color_pieza = '#00FFFF'
            if self.nombre_pieza_actual:
                if self.nombre_pieza_actual in self.shapes:
                    color_pieza = self.shapes[self.nombre_pieza_actual]['color']
                elif self.nombre_pieza_actual in self.powerups:
                    color_pieza = self.powerups[self.nombre_pieza_actual]['color']
            matriz_pieza = self.pieza_actual[self.pieza_rotacion]
            for y_offset, fila in enumerate(matriz_pieza):
                for x_offset, celda in enumerate(fila):
                    if celda == 1:
                        self.dibujar_celda(self.pieza_x + x_offset, self.pieza_y + y_offset, color_pieza)

        if self.tipo_juego == 'SNAKE':
            if self.posicion_manzana:

                x, y = self.posicion_manzana

                self.dibujar_celda(
                x,
                y,
                "#FF0000",
                "CIRCLE"
                )

            color = "#AAAAAA"
            forma = "CIRCLE"

            if self.posicion_powerup:

             x, y = self.posicion_powerup

             self.dibujar_celda(
                 x,
                 y,
                 "#FFD700",
                 "CIRCLE"
             )

            if "CLOUD" in self.obstacles:

                color = self.obstacles["CLOUD"]["color"]
                forma = self.obstacles["CLOUD"]["form"]

            for x, y in self.posiciones_obstaculos:

                self.dibujar_celda(
                    x,
                    y,
                    color,
                    forma
                )

            for x, y in self.posiciones_veneno:

                 self.dibujar_celda(
                     x,
                     y,
                     "#9900FF",
                     "CIRCLE"
                 )

            for x, y in self.posiciones_obstaculos:

                self.dibujar_celda(
                    x,
                    y,
                    "#AAAAAA",
                    "CIRCLE"
                )


            for i, segmento in enumerate(self.serpiente_cuerpo):
                x, y = segmento

                if i == 0:

                    if self.inmune:
                        color = "#FF00D4"
                    else:
                        color = COLOR_SNAKE_CABEZA

                    if self.nivel_actual == "NYAN_CAT":
                        forma = "NYAN_CAT"
                    else:
                        forma = self.shapes.get(
                            "SNAKE_HEAD",
                            {}
                        ).get(
                            "form",
                            "RECTANGLE"
                        )

                else:
                    if self.nivel_actual == "NYAN_CAT":

                        colores = [
                            "#FF0000",
                            "#FF8800",
                            "#FFFF00",
                            "#00FF00",
                            "#00FFFF",
                            "#0000FF",
                            "#FF00FF"
                        ]

                        color = colores[i % len(colores)]

                    else:

                        color = COLOR_SNAKE_CUERPO
                    forma = self.shapes.get(
                        "SNAKE_BODY",
                        {}
                    ).get(
                        "form",
                        "RECTANGLE"
                    )

                self.dibujar_celda(x, y, color, forma)

        if self.tipo_juego == 'TANKS':

            # 1. Draw Player Tank according to its shape state
            player_shape = None
            for name, shape in self.shapes.items():
                if shape.get('type') == 'PLAYER':
                    player_shape = shape
                    break
            if player_shape and player_shape.get('states'):
                matriz = player_shape['states'][0]
                for dy, fila in enumerate(matriz):
                    for dx, celda in enumerate(fila):
                        if celda == 1:
                            self.dibujar_celda(self.player_x + dx, self.player_y + dy, self.player_color)
            else:
                self.dibujar_celda(self.player_x, self.player_y, self.player_color)

            # 2. Draw Enemies
            for enemigo in self.enemigos:
                shape_name = enemigo["name"]
                shape_info = self.shapes.get(shape_name, {})
                color = enemigo.get("color", "#FF0000")
                if shape_info and shape_info.get("states"):
                    matriz = shape_info["states"][0]
                    for dy, fila in enumerate(matriz):
                        for dx, celda in enumerate(fila):
                            if celda == 1:
                                self.dibujar_celda(enemigo["x"] + dx, enemigo["y"] + dy, color)
                else:
                    self.dibujar_celda(enemigo["x"], enemigo["y"], color)

            # 3. Draw Player Bullets
            bullet_color = "#FFFF00"
            bullet_form = "CIRCLE"
            if "BULLET" in self.shapes:
                bullet_color = self.shapes["BULLET"].get("color", "#FFFF00")
                bullet_form = self.shapes["BULLET"].get("form", "CIRCLE")
                
            for bala in self.balas_jugador:
                self.dibujar_celda(
                    bala["x"],
                    bala["y"],
                    bullet_color,
                    bullet_form
                )

            # 4. Draw Enemy Bullets
            for bala in self.balas_enemigos:
                self.dibujar_celda(
                    bala["x"],
                    bala["y"],
                    "#00FF00",
                    "CIRCLE"
                )

            # 5. Draw Hammer
            if self.posicion_hammer:
                x, y = self.posicion_hammer
                self.dibujar_celda(
                    x,
                    y,
                    "#0DC99A",
                    "CIRCLE"
                )

            # 6. Draw Boss
            if self.boss_activo:
                boss_info = self.datos_juego.get('boss', {})
                boss_states = boss_info.get('states', [])
                if boss_states:
                    matriz_boss = boss_states[0]
                    for dy, fila in enumerate(matriz_boss):
                        for dx, celda in enumerate(fila):
                            if celda == 1:
                                self.dibujar_celda(
                                    self.boss_x + dx,
                                    self.boss_y + dy,
                                    self.boss_color
                                )
                else:
                    # Fallback solid block
                    for dy in range(self.boss_h):
                        for dx in range(self.boss_w):
                            self.dibujar_celda(
                                self.boss_x + dx,
                                self.boss_y + dy,
                                self.boss_color
                             )

    def dibujar_celda(self, x, y, color, forma="RECTANGLE"):
        ts = self.taman_celda

        x1, y1 = x * ts, y * ts
        x2, y2 = x1 + ts, y1 + ts

        if forma == "CIRCLE":
            self.canvas.create_oval(
                x1, y1, x2, y2,
                fill=color,
                outline='#000000'
            )

        elif forma == "TRIANGLE":
            self.canvas.create_polygon(
                (x1 + ts/2, y1),
                (x1, y2),
                (x2, y2),
                fill=color,
                outline='#000000'
            )
        elif forma == "NYAN_CAT":

            self.canvas.create_oval(
                x1,
                y1,
                x2,
                y2,
                fill="#FFD1DC",
                outline="black"
            )

            self.canvas.create_oval(
                x1+5,
                y1+7,
                x1+8,
                y1+10,
                fill="black"
            )

            self.canvas.create_oval(
                x1+17,
                y1+7,
                x1+20,
                y1+10,
                fill="black"
            )

        else:
            self.canvas.create_rectangle(
                x1, y1, x2, y2,
                fill=color,
                outline='#000000'
            )

    def ejecutar_evento(self, nombre_evento):
        if nombre_evento in self.datos_juego['events']:
            for accion in self.datos_juego['events'][nombre_evento]:
                verbo, objeto = accion.get('accion'), accion.get('objeto')

                if verbo == 'INCREASE_SCORE': self.puntuacion += int(objeto)
                if verbo == 'GAME_OVER': self.juego_terminado = True

                if self.tipo_juego == 'TETRIS':
                    if verbo == 'SPAWN': self.tetris_spawn_pieza()
                    if verbo == 'MOVE': self.tetris_mover_pieza(accion['params'][0])
                    if verbo == 'ROTATE': self.tetris_rotar_pieza()

                if self.tipo_juego == 'SNAKE':

                    if verbo == 'SPAWN' and objeto == 'PLAYER': self.snake_spawn_jugador(accion)
                    if verbo == 'SPAWN' and objeto == 'FOOD': self.snake_spawn_manzana()
                    if verbo == 'MOVE' and objeto == 'PLAYER': self.snake_mover_jugador()
                    if verbo == 'GROW': self.snake_crecer()

                if self.tipo_juego == 'TANKS':

                    if verbo == 'SPAWN':
                        if objeto == 'PLAYER_TANK':
                            coords = accion['params'][0] if accion['params'] else None
                            self.tanks_spawn_player(coords)

                        elif objeto == 'ENEMY_TANK' or (objeto in self.shapes and self.shapes[objeto].get('type') == 'ENEMY'):
                            coords = accion['params'][0] if accion['params'] else None
                            self.tanks_spawn_enemy(objeto, coords)

                        elif objeto == 'BULLET':
                            self.tanks_disparar()

                        elif objeto == 'HAMMER':
                            self.tanks_spawn_hammer()

                        elif objeto == self.datos_juego.get('boss', {}).get('name'):
                            self.tanks_spawn_boss()

                    elif verbo == 'MOVE':
                        if objeto == 'PLAYER':
                            direccion = accion['params'][0]
                            self.tanks_mover_jugador(direccion)
                        elif objeto == 'BULLET':
                            if accion['params'] and accion['params'][0] == 'FORWARD':
                                self.tanks_actualizar_balas()


    def tetris_spawn_pieza(self):
        if self.lineas_3_simultaneas and self.powerups:
            nombre_seleccionado = list(self.powerups.keys())[0]
            self.nombre_pieza_actual = nombre_seleccionado
            self.pieza_actual = self.powerups[nombre_seleccionado]['states']

            self.lineas_3_simultaneas = False
        else:
            nombres = list(self.shapes.keys())
            pesos = [self.shapes[n]['chance'] for n in nombres]
            total_pesos = sum(pesos)

            r = random.uniform(0, total_pesos)
            acumulado = 0
            nombre_seleccionado = nombres[-1]
            for nombre, peso in zip(nombres, pesos):
                if acumulado + peso >= r:
                    nombre_seleccionado = nombre
                    break
                acumulado += peso

            self.nombre_pieza_actual = nombre_seleccionado
            self.pieza_actual = self.shapes[nombre_seleccionado]['states']

        self.pieza_x, self.pieza_y, self.pieza_rotacion = self.ancho // 2 - 2, 0, 0
        if self.tetris_verificar_colision(self.pieza_x, self.pieza_y, self.pieza_rotacion):
            self.juego_terminado = True

    def tetris_mover_pieza(self, direccion):
        if not self.pieza_actual: return
        dx, dy = 0, 0
        if direccion == 'LEFT': dx = -1
        elif direccion == 'RIGHT': dx = 1
        elif direccion == 'DOWN': dy = 1
        if not self.tetris_verificar_colision(self.pieza_x + dx, self.pieza_y + dy, self.pieza_rotacion):
            self.pieza_x += dx
            self.pieza_y += dy
        elif dy > 0:
            self.tetris_fijar_pieza()

    def tetris_rotar_pieza(self):
        if not self.pieza_actual: return
        nueva_rotacion = (self.pieza_rotacion + 1) % len(self.pieza_actual)
        if not self.tetris_verificar_colision(self.pieza_x, self.pieza_y, nueva_rotacion):
            self.pieza_rotacion = nueva_rotacion

    def tetris_fijar_pieza(self):
        matriz_pieza = self.pieza_actual[self.pieza_rotacion]
        color_pieza = '#00FFFF'
        if self.nombre_pieza_actual:
            if self.nombre_pieza_actual in self.shapes:
                color_pieza = self.shapes[self.nombre_pieza_actual]['color']
            elif self.nombre_pieza_actual in self.powerups:
                color_pieza = self.powerups[self.nombre_pieza_actual]['color']
        for y_offset, fila in enumerate(matriz_pieza):
            for x_offset, celda in enumerate(fila):
                if celda == 1:
                    if 0 <= self.pieza_y + y_offset < self.alto and 0 <= self.pieza_x + x_offset < self.ancho:
                        self.grid[self.pieza_y + y_offset][self.pieza_x + x_offset] = color_pieza
        self.pieza_actual = None
        self.tetris_limpiar_lineas()
        self.ejecutar_evento('ON_START')

    def tetris_verificar_colision(self, x, y, rotacion):
        if not self.pieza_actual: return False

        if self.nombre_pieza_actual == 'GEM_POWERUP':
            if not (0 <= x < self.ancho):
                return True
            if not (0 <= y < self.alto):
                return True
            deepest_y = -1
            for y_check in range(self.alto - 1, -1, -1):
                if self.grid[y_check][x] == 0:
                    deepest_y = y_check
                    break
            if y > deepest_y:
                return True
            return False

        matriz_pieza = self.pieza_actual[rotacion]
        for y_offset, fila in enumerate(matriz_pieza):
            for x_offset, celda in enumerate(fila):
                if celda == 1:
                    nuevo_x, nuevo_y = x + x_offset, y + y_offset
                    if not (0 <= nuevo_x < self.ancho and 0 <= nuevo_y < self.alto and self.grid[nuevo_y][nuevo_x] == 0):
                        return True
        return False

    def tetris_limpiar_lineas(self):
        nuevo_grid = [fila for fila in self.grid if not all(fila)]
        lineas_limpias = self.alto - len(nuevo_grid)
        if lineas_limpias > 0:
            if lineas_limpias >= 3:
                self.lineas_3_simultaneas = True
            self.grid = [[0] * self.ancho for _ in range(lineas_limpias)] + nuevo_grid
            for _ in range(lineas_limpias): self.ejecutar_evento('ON_LINE_CLEAR')

    def snake_spawn_jugador(self, accion):
        coords = accion['params'][0] if accion['params'] else [self.ancho // 2, self.alto // 2]
        self.serpiente_cuerpo = [(coords[0], coords[1])]
        self.serpiente_direccion = (1, 0)

    def snake_spawn_manzana(self):

        while True:

            x = random.randint(0, self.ancho - 1)
            y = random.randint(0, self.alto - 1)

            if (x,y) not in self.serpiente_cuerpo:

                self.posicion_manzana = (x,y)
                break

    def snake_spawn_powerup(self):

        while True:

            x = random.randint(0, self.ancho - 1)
            y = random.randint(0, self.alto - 1)

            if (x,y) not in self.serpiente_cuerpo \
               and (x,y) != self.posicion_manzana \
               and (x,y) not in self.posiciones_veneno \
               and (x,y) not in self.posiciones_obstaculos:

                self.posicion_powerup = (x,y)
                break

    def snake_activar_inmunidad(self):

        self.inmune = True
        self.tiempo_inmunidad = time.time() + 5

        self.posicion_powerup = None

    def snake_spawn_veneno(self):

        while True:

            x = random.randint(0, self.ancho - 1)
            y = random.randint(0, self.alto - 1)

            if (x,y) not in self.serpiente_cuerpo \
               and (x,y) != self.posicion_manzana \
               and (x,y) not in self.posiciones_veneno:

                self.posiciones_veneno.append((x,y))
                break

    def snake_comer_veneno(self):
        self.sonido_danio.play()

        if self.inmune:

            self.posiciones_veneno = [
                p for p in self.posiciones_veneno
                if p != self.serpiente_cuerpo[0]
            ]

            return

        self.puntuacion -= 10

        if self.puntuacion < 0:
            self.puntuacion = 0

        if len(self.serpiente_cuerpo) <= 3:
            self.juego_terminado = True
            return

        for _ in range(3):
            self.serpiente_cuerpo.pop()

    def snake_spawn_obstaculos(self):

        self.posiciones_obstaculos = []

        while len(self.posiciones_obstaculos) < 4:

            x = random.randint(0, self.ancho - 1)
            y = random.randint(0, self.alto - 1)

            if (x,y) not in self.serpiente_cuerpo \
               and (x,y) != self.posicion_manzana \
               and (x,y) not in self.posiciones_veneno \
               and (x,y) not in self.posiciones_obstaculos:

                self.posiciones_obstaculos.append((x,y))

    def snake_chocar_obstaculo(self):
        self.sonido_danio.play()
        if self.inmune:
            return

        if self.puntuacion == 0 and len(self.serpiente_cuerpo) <= 1:

            self.juego_terminado = True
            return

        self.puntuacion = 0

        self.serpiente_cuerpo = [
            self.serpiente_cuerpo[0]
        ]


    def snake_mover_jugador(self):
        if self.inmune and time.time() > self.tiempo_inmunidad:

            self.inmune = False

        if not self.serpiente_cuerpo: return
        cabeza_x, cabeza_y = self.serpiente_cuerpo[0]
        dir_x, dir_y = self.serpiente_direccion
        nueva_cabeza = (cabeza_x + dir_x, cabeza_y + dir_y)

        if not (0 <= nueva_cabeza[0] < self.ancho and 0 <= nueva_cabeza[1] < self.alto):

            if self.inmune:

                self.serpiente_cuerpo.pop()
                return

            self.ejecutar_evento('ON_COLLISION_WALL')
            return

        if nueva_cabeza in self.serpiente_cuerpo[:-1]:

             if self.inmune:

                 self.serpiente_cuerpo.pop()
                 return

             self.ejecutar_evento('ON_COLLISION_SELF')
             return

        self.serpiente_cuerpo.insert(0, nueva_cabeza)

        if nueva_cabeza == self.posicion_manzana:
            self.contador_rondas += 1
            if self.obstaculos_habilitados:

                if self.contador_rondas % 3 == 0:

                    self.snake_spawn_obstaculos()

            if self.powerup_habilitado:

                if self.contador_rondas % 6 == 0:

                    self.snake_spawn_powerup()

            self.ejecutar_evento('ON_EAT_FOOD')

            self.snake_spawn_manzana()

            if self.veneno_habilitado:

                if random.random() < 0.3:

                    self.snake_spawn_veneno()

        elif nueva_cabeza in self.posiciones_obstaculos:

            self.snake_chocar_obstaculo()

            return

        elif nueva_cabeza in self.posiciones_veneno:

            self.posiciones_veneno.remove(nueva_cabeza)

            self.snake_comer_veneno()

            self.snake_spawn_veneno()

        elif nueva_cabeza == self.posicion_powerup:

            self.snake_activar_inmunidad()

        else:
            self.serpiente_cuerpo.pop()

    def snake_cambiar_direccion(self, direccion):
        if direccion == 'UP' and self.serpiente_direccion[1] != 1:
            self.serpiente_direccion = (0, -1)
        elif direccion == 'DOWN' and self.serpiente_direccion[1] != -1:
            self.serpiente_direccion = (0, 1)
        elif direccion == 'LEFT' and self.serpiente_direccion[0] != 1:
            self.serpiente_direccion = (-1, 0)
        elif direccion == 'RIGHT' and self.serpiente_direccion[0] != -1:
            self.serpiente_direccion = (1, 0)

    def snake_crecer(self):
        pass


    def tanks_spawn_player(self, coords=None):
        self.player_w = 1
        self.player_h = 1
        self.player_color = "#0000FF"
        
        player_shape = None
        for name, shape in self.shapes.items():
            if shape.get('type') == 'PLAYER':
                player_shape = shape
                self.player_hp = shape.get('hp', 200)
                self.player_max_hp = self.player_hp
                self.player_color = shape.get('color', '#0000FF')
                if shape.get('states'):
                    self.player_w = len(shape['states'][0][0])
                    self.player_h = len(shape['states'][0])
                break
        
        if coords:
            self.player_x = coords[0]
            self.player_y = coords[1]
        else:
            self.player_x = (self.ancho - self.player_w) // 2
            self.player_y = self.alto - self.player_h - 1

    def tanks_mover_jugador(self, dx, dy=None):
        if dy is None:
            direccion = dx
            dx, dy = 0, 0
            if direccion == "LEFT": dx = -1
            elif direccion == "RIGHT": dx = 1
            elif direccion == "UP": dy = -1
            elif direccion == "DOWN": dy = 1
            self.player_direccion = direccion
        else:
            if dx == -1: self.player_direccion = "LEFT"
            elif dx == 1: self.player_direccion = "RIGHT"
            elif dy == -1: self.player_direccion = "UP"
            elif dy == 1: self.player_direccion = "DOWN"

        nuevo_x = self.player_x + dx
        nuevo_y = self.player_y + dy

        if 0 <= nuevo_x <= self.ancho - self.player_w and \
           0 <= nuevo_y <= self.alto - self.player_h:
            self.player_x = nuevo_x
            self.player_y = nuevo_y

    def tanks_disparar(self):
        self.sonido_disparo.play()
        dx, dy = 0, 0
        if self.player_direccion == "UP":
            dy = -1
        elif self.player_direccion == "DOWN":
            dy = 1
        elif self.player_direccion == "LEFT":
            dx = -1
        elif self.player_direccion == "RIGHT":
            dx = 1

        bx = self.player_x + (self.player_w // 2) + dx
        by = self.player_y + (self.player_h // 2) + dy

        self.balas_jugador.append({
            "x": bx,
            "y": by,
            "dx": dx,
            "dy": dy
        })

    def tanks_actualizar_balas(self):
        nuevas_balas = []
        for bala in self.balas_jugador:
            bala["x"] += bala["dx"]
            bala["y"] += bala["dy"]
            if 0 <= bala["x"] < self.ancho and 0 <= bala["y"] < self.alto:
                nuevas_balas.append(bala)
        self.balas_jugador = nuevas_balas

        nuevas = []
        for bala in self.balas_enemigos:
            bala["x"] += bala["dx"]
            bala["y"] += bala["dy"]
            if 0 <= bala["x"] < self.ancho and 0 <= bala["y"] < self.alto:
                nuevas.append(bala)
        self.balas_enemigos = nuevas

    def tanks_spawn_enemy(self, nombre_shape=None, coords=None):
        if not nombre_shape:
            enemy_shapes = [name for name, shape in self.shapes.items() if shape.get('type') == 'ENEMY']
            if enemy_shapes:
                nombre_shape = random.choice(enemy_shapes)
            else:
                nombre_shape = "ENEMY_TANK"

        shape_info = self.shapes.get(nombre_shape, {})
        hp = shape_info.get("hp", 50)
        damage = shape_info.get("damage", 10)
        speed = shape_info.get("speed", 1)
        color = shape_info.get("color", "#FF0000")

        w, h = 1, 1
        if shape_info.get("states"):
            w = len(shape_info["states"][0][0])
            h = len(shape_info["states"][0])

        if coords:
            x, y = coords[0], coords[1]
        else:
            x = random.randint(0, self.ancho - w)
            y = 1

        self.enemigos.append({
            "name": nombre_shape,
            "x": x,
            "y": y,
            "w": w,
            "h": h,
            "hp": hp,
            "max_hp": hp,
            "damage": damage,
            "speed": speed,
            "color": color,
            "_tick": 0,
            "direccion": "DOWN"
        })

    def tanks_actualizar_enemigos(self):
        for enemigo in self.enemigos:
            enemigo["_tick"] = enemigo.get("_tick", 0) + 1
            move_freq = 2 if enemigo.get("speed", 1) <= 1 else 1
            if enemigo["_tick"] % move_freq != 0:
                continue

            if random.random() < 0.7:
                dx, dy = 0, 0
                if self.player_x > enemigo["x"]: dx = 1
                elif self.player_x < enemigo["x"]: dx = -1
                if self.player_y > enemigo["y"]: dy = 1
                elif self.player_y < enemigo["y"]: dy = -1
                if dx != 0 and dy != 0:
                    if random.random() < 0.5: dy = 0
                    else: dx = 0
            else:
                dx = random.choice([-1, 0, 1])
                dy = random.choice([-1, 0, 1])

            nuevo_x = enemigo["x"] + dx
            nuevo_y = enemigo["y"] + dy

            if 0 <= nuevo_x <= self.ancho - enemigo["w"]:
                enemigo["x"] = nuevo_x
            if 0 <= nuevo_y <= self.alto - enemigo["h"]:
                enemigo["y"] = nuevo_y

    def tanks_actualizar_enemigos_rapidos(self):
        pass

    def tanks_spawn_fast_enemy(self):
        self.tanks_spawn_enemy("FAST_ENEMY")

    def tanks_disparo_enemigos(self):
        for enemigo in self.enemigos:
            rate = 15 if enemigo.get("speed", 1) <= 1 else 10
            if random.randint(1, rate) == 1:
                dx, dy = 0, 0
                if self.player_x > enemigo["x"]: dx = 1
                elif self.player_x < enemigo["x"]: dx = -1
                if self.player_y > enemigo["y"]: dy = 1
                elif self.player_y < enemigo["y"]: dy = -1
                if abs(self.player_x - enemigo["x"]) >= abs(self.player_y - enemigo["y"]):
                    dy = 0
                else:
                    dx = 0

                if dx != 0 or dy != 0:
                    bx = enemigo["x"] + (enemigo["w"] // 2) + dx
                    by = enemigo["y"] + (enemigo["h"] // 2) + dy
                    self.balas_enemigos.append({
                        "x": bx,
                        "y": by,
                        "dx": dx,
                        "dy": dy,
                        "damage": enemigo.get("damage", 10)
                    })

    def tanks_disparo_enemigos_rapidos(self):
        pass

    def tanks_spawn_boss(self):
        self.boss_activo = True
        boss_info = self.datos_juego.get('boss', {})
        self.boss_hp = boss_info.get('hp', 200)
        self.boss_max_hp = self.boss_hp
        self.boss_damage = boss_info.get('damage', 100)
        self.boss_color = boss_info.get('color', '#800080')

        boss_states = boss_info.get('states', [])
        if boss_states:
            self.boss_w = len(boss_states[0][0])
            self.boss_h = len(boss_states[0])
        else:
            self.boss_w = 5
            self.boss_h = 5

        self.boss_x = (self.ancho - self.boss_w) // 2
        self.boss_y = 1
        self.boss_timer = 0
        self.enemigos = []

    def tanks_boss_tick(self):
        if not self.boss_activo:
            return

        self.boss_timer += 1
        hp_pct = self.boss_hp / self.boss_max_hp if self.boss_max_hp > 0 else 0

        if hp_pct > 0.5:
            cadencia = 20
            direcciones = [(1,0),(-1,0),(0,1),(0,-1)]
        elif hp_pct > 0.2:
            cadencia = 15
            direcciones = [(1,0),(-1,0),(0,1),(0,-1),(1,1),(-1,1),(1,-1),(-1,-1)]
            if self.boss_timer % 25 == 0:
                target_x = self.player_x - (self.boss_w // 2)
                if self.boss_x < target_x:
                    self.boss_x = min(self.boss_x + 1, self.ancho - self.boss_w)
                elif self.boss_x > target_x:
                    self.boss_x = max(self.boss_x - 1, 0)
        else:
            cadencia = 8
            direcciones = [(1,0),(-1,0),(0,1),(0,-1),(1,1),(-1,1),(1,-1),(-1,-1)]
            if self.boss_timer % 15 == 0:
                target_x = self.player_x - (self.boss_w // 2)
                if self.boss_x < target_x:
                    self.boss_x = min(self.boss_x + 1, self.ancho - self.boss_w)
                elif self.boss_x > target_x:
                    self.boss_x = max(self.boss_x - 1, 0)

        if self.boss_timer % cadencia == 0:
            centro_x = self.boss_x + (self.boss_w // 2)
            centro_y = self.boss_y + (self.boss_h // 2)
            for dx, dy in direcciones:
                self.balas_enemigos.append({
                    "x": centro_x + dx,
                    "y": centro_y + dy,
                    "dx": dx,
                    "dy": dy,
                    "damage": self.boss_damage
                })

    def tanks_spawn_hammer(self):
        for _ in range(50):
            x = random.randint(0, self.ancho - 1)
            y = random.randint(0, self.alto - 1)
            if self.grid[y][x] == 0:
                if not (self.player_x <= x < self.player_x + self.player_w and
                        self.player_y <= y < self.player_y + self.player_h):
                    if not (self.boss_activo and self.boss_x <= x < self.boss_x + self.boss_w and
                            self.boss_y <= y < self.boss_y + self.boss_h):
                        self.posicion_hammer = (x, y)
                        break

    def tanks_generar_muros(self):
        self.grid = [[0 for _ in range(self.ancho)] for _ in range(self.alto)]
        wall_color = "#888888"
        if "WALL" in self.shapes:
            wall_color = self.shapes["WALL"].get("color", "#888888")

        muros = [
            (3, 4), (4, 4), (5, 4), (12, 4), (13, 4), (14, 4),
            (3, 12), (4, 12), (5, 12), (12, 12), (13, 12), (14, 12),
            (8, 7), (9, 7), (8, 8), (9, 8), (8, 9), (9, 9)
        ]
        for x, y in muros:
            if 0 <= x < self.ancho and 0 <= y < self.alto:
                self.grid[y][x] = wall_color

    def tanks_verificar_colisiones(self):
        balas_jugador_filtradas = []
        for bala in self.balas_jugador:
            x, y = bala["x"], bala["y"]
            if 0 <= x < self.ancho and 0 <= y < self.alto and self.grid[y][x] != 0:
                self.grid[y][x] = 0
                self.sonido_danio.play()
                continue
            balas_jugador_filtradas.append(bala)
        self.balas_jugador = balas_jugador_filtradas

        balas_enemigos_filtradas = []
        for bala in self.balas_enemigos:
            x, y = bala["x"], bala["y"]
            if 0 <= x < self.ancho and 0 <= y < self.alto and self.grid[y][x] != 0:
                self.grid[y][x] = 0
                self.sonido_danio.play()
                continue
            balas_enemigos_filtradas.append(bala)
        self.balas_enemigos = balas_enemigos_filtradas

        if self.boss_activo:
            boss_info = self.datos_juego.get('boss', {})
            boss_states = boss_info.get('states', [])
            if boss_states:
                matriz_boss = boss_states[0]
                balas_restantes = []
                for bala in self.balas_jugador:
                    bx, by = bala["x"], bala["y"]
                    if (self.boss_x <= bx < self.boss_x + self.boss_w and
                        self.boss_y <= by < self.boss_y + self.boss_h):
                        rx, ry = bx - self.boss_x, by - self.boss_y
                        if matriz_boss[ry][rx] == 1:
                            self.boss_hp -= 50
                            self.sonido_danio.play()
                            if self.boss_hp <= 0:
                                self.boss_activo = False
                                self.victoria = True
                                self.juego_terminado = True
                                self.ejecutar_evento('ON_BOSS_DEFEATED')
                            continue
                    balas_restantes.append(bala)
                self.balas_jugador = balas_restantes

        balas_restantes = []
        for bala in self.balas_jugador:
            bx, by = bala["x"], bala["y"]
            impacto = False
            for enemigo in list(self.enemigos):
                ex, ey = enemigo["x"], enemigo["y"]
                ew, eh = enemigo["w"], enemigo["h"]
                if ex <= bx < ex + ew and ey <= by < ey + eh:
                    rx, ry = bx - ex, by - ey
                    shape_info = self.shapes.get(enemigo["name"], {})
                    if shape_info.get("states") and shape_info["states"][0][ry][rx] == 1:
                        enemigo["hp"] -= 50
                        self.sonido_danio.play()
                        impacto = True
                        if enemigo["hp"] <= 0:
                            if enemigo in self.enemigos:
                                self.enemigos.remove(enemigo)
                            self.puntuacion += 100
                            self.ejecutar_evento('ON_ENEMY_DESTROYED')
                        break
            if not impacto:
                balas_restantes.append(bala)
        self.balas_jugador = balas_restantes

        balas_enemigas_restantes = []
        for bala in self.balas_enemigos:
            bx, by = bala["x"], bala["y"]
            impacto = False
            if (self.player_x <= bx < self.player_x + self.player_w and
                self.player_y <= by < self.player_y + self.player_h):
                rx, ry = bx - self.player_x, by - self.player_y
                player_shape = None
                for name, shape in self.shapes.items():
                    if shape.get('type') == 'PLAYER':
                        player_shape = shape
                        break
                if player_shape and player_shape.get('states'):
                    if player_shape['states'][0][ry][rx] == 1:
                        damage_taken = bala.get("damage", 25)
                        self.player_hp -= damage_taken
                        self.sonido_danio.play()
                        impacto = True
                        if self.player_hp <= 0:
                            self.juego_terminado = True
                else:
                    self.player_hp -= 25
                    self.sonido_danio.play()
                    impacto = True
                    if self.player_hp <= 0:
                        self.juego_terminado = True
            if not impacto:
                balas_enemigas_restantes.append(bala)
        self.balas_enemigos = balas_enemigas_restantes

        px, py, pw, ph = self.player_x, self.player_y, self.player_w, self.player_h
        for enemigo in list(self.enemigos):
            ex, ey, ew, eh = enemigo["x"], enemigo["y"], enemigo["w"], enemigo["h"]
            if (px < ex + ew and px + pw > ex and
                py < ey + eh and py + ph > ey):
                self.player_hp -= enemigo["damage"]
                self.sonido_danio.play()
                if enemigo in self.enemigos:
                    self.enemigos.remove(enemigo)
                self.puntuacion += 50
                if self.player_hp <= 0:
                    self.juego_terminado = True

    def tanks_game_tick(self):
        self.timer_enemigos += 1
        if self.timer_enemigos > 40:
            self.timer_enemigos = 0
            if not self.boss_activo:
                self.tanks_spawn_enemy()

        if (self.puntuacion >= 1000 and 
            not self.boss_activo and 
            not getattr(self, 'boss_spawned', False)):
            self.boss_spawned = True
            self.ejecutar_evento('ON_TARGET_SCORE')

        if random.randint(1, 300) == 1:
            self.tanks_spawn_hammer()

        if self.posicion_hammer:
            hx, hy = self.posicion_hammer
            if (self.player_x <= hx < self.player_x + self.player_w and
                self.player_y <= hy < self.player_y + self.player_h):
                self.player_hp += 50
                if self.player_hp > self.player_max_hp:
                    self.player_hp = self.player_max_hp
                self.sonido_hammer.play()
                self.posicion_hammer = None

        self.tanks_actualizar_balas()
        self.tanks_actualizar_enemigos()
        self.tanks_disparo_enemigos()
        self.tanks_boss_tick()
        self.tanks_verificar_colisiones()


    def mostrar_game_over(self):
        tkMessageBox.showinfo("Juego Terminado", "Puntuacion Final: " + str(self.puntuacion))
        self.root.destroy()
        sys.exit(0)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Uso: python runtime.py <archivo_juego.json>")
        sys.exit(1)
    archivo_juego = sys.argv[1]
    try:
        with open(archivo_juego, 'r') as f:
            datos_juego = json.load(f)
    except (IOError, OSError):
        print("Error: No se pudo encontrar el archivo " + archivo_juego)
        sys.exit(1)
    juego = Juego(datos_juego)
    juego.run()
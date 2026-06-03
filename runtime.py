# -*- coding: utf-8 -*-
# runtime.py (VERSION CON INTERFAZ GRAFICA USANDO Tkinter y caracteres ASCII unicamente)

import sys
import json
import time
import random

# Tkinter es la libreria GUI estandar de Python, compatible con 2.7 y 3
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
        
        # --- Configuracion de la GUI ---
        self.root = tk.Tk()
        self.root.title("BrickScript - " + self.tipo_juego)
        # Configurar la accion al cerrar la ventana ('X' de la barra de titulo)
        self.root.protocol("WM_DELETE_WINDOW", self.cerrar_ventana)
        
        self.taman_celda = 25 # Pixeles por celda
        self.ancho_canvas = self.ancho * self.taman_celda
        self.alto_canvas = self.alto * self.taman_celda
        
        # Canvas para dibujar el juego
        self.canvas = tk.Canvas(self.root, width=self.ancho_canvas, height=self.alto_canvas, bg='#111111')
        self.canvas.pack(side=tk.LEFT, padx=10, pady=10)

        # Marco lateral para la puntuacion y controles
        self.marco_score = tk.Frame(self.root, width=150, height=self.alto_canvas, bg='#222222')
        self.marco_score.pack(side=tk.RIGHT, fill=tk.Y, padx=10, pady=10)
        
        self.label_score = tk.Label(self.marco_score, text="PUNTUACION\n0", bg='#222222', fg='white', font=('Consolas', 16, 'bold'))
        self.label_score.pack(pady=20, padx=10)
        
        # Labels adicionales para el modo Snake Evolved
        if self.tipo_juego == 'SNAKE':
            self.label_nivel = tk.Label(self.marco_score, text="NIVEL\nBABY", bg='#222222', fg='#00FFCC', font=('Consolas', 14, 'bold'))
            self.label_nivel.pack(pady=10, padx=10)
            
            self.label_powerup = tk.Label(self.marco_score, text="ESTADO\nNORMAL", bg='#222222', fg='gray', font=('Consolas', 10, 'bold'))
            self.label_powerup.pack(pady=10, padx=10)
            
            self.label_controles = tk.Label(self.marco_score, text="CONTROLES\nFlechas: Mover\n1, 2, 3: Niveles", bg='#222222', fg='gray', font=('Consolas', 9))
        else:
            self.label_controles = tk.Label(self.marco_score, text="CONTROLES\nFlechas: Mover/Rotar", bg='#222222', fg='gray', font=('Consolas', 10))
        
        self.label_controles.pack(pady=20, padx=10)

        # Configurar eventos de teclado. Usamos <Key> para capturar cualquier tecla
        self.root.bind('<Key>', self.manejar_input_gui)

        # Normalizar las shapes para asegurar retrocompatibilidad con JSONs antiguos
        self.shapes = {}
        for nombre, datos in self.datos_juego.get('shapes', {}).items():
            if isinstance(datos, list):
                self.shapes[nombre] = {
                    "color": "#00FFFF",
                    "chance": 10,
                    "states": datos,
                    "form": "RECTANGLE"
                }
            elif isinstance(datos, dict):
                self.shapes[nombre] = {
                    "color": datos.get("color", "#00FFFF"),
                    "chance": int(datos.get("chance", 10)),
                    "states": datos.get("states", []),
                    "form": datos.get("form", "RECTANGLE")
                }

        # Cargar los alimentos, obstáculos y power-ups si existen
        self.foods = self.datos_juego.get('foods', {})
        self.obstacles = self.datos_juego.get('obstacles', {})
        self.powerups = self.datos_juego.get('powerups', {})
        self.levels = self.datos_juego.get('levels', {})

        if self.tipo_juego == 'TETRIS':
            self.pieza_actual = None
            self.pieza_x, self.pieza_y, self.pieza_rotacion = 0, 0, 0
            self.velocidad_gravedad = 0.4
            self.nombre_pieza_actual = None
            self.lineas_3_simultaneas = False
        
        if self.tipo_juego == 'SNAKE':
            self.serpiente_cuerpo = []
            self.serpiente_direccion = (1, 0)
            self.posicion_comida = None
            
            # Inicialización del Manejador de Niveles y Estados
            self.nivel_actual = 'BABY'
            self.puntos_requeridos = {
                'BABY': 0,
                'ENTUSIASTA': 20,
                'NYAN_CAT': 50
            }
            self.invulnerable = False
            self.invulnerable_until = 0.0
            
            self.posiciones_veneno = []
            self.posicion_powerup = None
            self.posiciones_nubes = []
            
            # Configurar tick speed de BABY por defecto
            baby_speed = self.levels.get('BABY', {}).get('speed', 0.2)
            self.velocidad_gravedad = baby_speed
        
        self.timer_gravedad = 0
        self.ejecutar_evento('ON_START')
        
        if self.tipo_juego == 'SNAKE':
            # Configurar las entidades del nivel al arrancar
            self.cambiar_nivel(self.nivel_actual)
            
        self.timer_id = None # Para controlar el loop de Tkinter

    def run(self):
        # Inicia el ciclo principal de juego de Tkinter
        self.root.after(50, self.game_loop) 
        self.root.mainloop() 

    def game_loop(self):
        if self.juego_terminado:
            self.mostrar_game_over()
            return

        # Actualizar el estado del Power-Up (timer de invulnerabilidad)
        if self.tipo_juego == 'SNAKE' and self.invulnerable:
            tiempo_restante = self.invulnerable_until - time.time()
            if tiempo_restante <= 0:
                self.invulnerable = False
                if hasattr(self, 'label_powerup'):
                    self.label_powerup.config(text="ESTADO\nNORMAL", fg='gray')
            else:
                if hasattr(self, 'label_powerup'):
                    self.label_powerup.config(text="ESTADO\n¡INVENCIBLE!\n({:.1f}s)".format(tiempo_restante), fg='#FFD700')

        # Logica de TICK/Gravedad
        # El loop se ejecuta cada 50ms (0.05 segundos)
        self.timer_gravedad += 0.05 
        if self.timer_gravedad >= self.velocidad_gravedad:
            self.timer_gravedad = 0
            self.ejecutar_evento('ON_TICK')

        self.dibujar()

        # Programa el siguiente ciclo de juego
        self.timer_id = self.root.after(50, self.game_loop)
        
    def cerrar_ventana(self):
        # Detiene el loop de juego de forma segura
        if self.timer_id:
            self.root.after_cancel(self.timer_id)
        self.root.destroy()
        sys.exit(0)

    def cambiar_nivel(self, nuevo_nivel):
        if self.tipo_juego != 'SNAKE': return
        self.nivel_actual = nuevo_nivel
        
        # Obtener velocidad de tick definida en el archivo .brick o aplicar valores por defecto
        speed = self.levels.get(nuevo_nivel, {}).get('speed')
        if speed is None:
            if nuevo_nivel == 'BABY': speed = 0.2
            elif nuevo_nivel == 'ENTUSIASTA': speed = 0.15
            elif nuevo_nivel == 'NYAN_CAT': speed = 0.07
            else: speed = 0.15
        self.velocidad_gravedad = speed
        
        # Actualizar la interfaz visual del nivel
        if hasattr(self, 'label_nivel'):
            color_nivel = '#00FFCC'
            if nuevo_nivel == 'ENTUSIASTA': color_nivel = '#FF9900'
            elif nuevo_nivel == 'NYAN_CAT': color_nivel = '#FF0077'
            self.label_nivel.config(text="NIVEL\n" + nuevo_nivel, fg=color_nivel)
            
        # Configurar y reubicar entidades del nuevo nivel
        self.configurar_entidades_nivel()

    def configurar_entidades_nivel(self):
        if self.tipo_juego != 'SNAKE': return
        
        # Limpiar entidades anteriores
        self.posiciones_veneno = []
        self.posiciones_nubes = []
        self.posicion_powerup = None
        
        # Configurar según nivel
        if self.nivel_actual == 'ENTUSIASTA':
            # Spawnear 2 frutas venenosas
            for _ in range(2):
                pos = self.obtener_posicion_vacia()
                if pos: self.posiciones_veneno.append(pos)
                
        elif self.nivel_actual == 'NYAN_CAT':
            # Spawnear 2 frutas venenosas
            for _ in range(2):
                pos = self.obtener_posicion_vacia()
                if pos: self.posiciones_veneno.append(pos)
                
            # Spawnear 4 nubes obstáculo en posiciones fijas
            for _ in range(4):
                pos = self.obtener_posicion_vacia()
                if pos: self.posiciones_nubes.append(pos)

    def obtener_posicion_vacia(self):
        intentos = 0
        while intentos < 200:
            x, y = random.randint(0, self.ancho - 1), random.randint(0, self.alto - 1)
            # Evitar colisión con el cuerpo de la serpiente
            if (x, y) in self.serpiente_cuerpo:
                intentos += 1
                continue
            # Evitar comida normal
            if (x, y) == self.posicion_comida:
                intentos += 1
                continue
            # Evitar venenos
            if (x, y) in self.posiciones_veneno:
                intentos += 1
                continue
            # Evitar nubes obstáculo
            if (x, y) in self.posiciones_nubes:
                intentos += 1
                continue
            # Evitar power-ups
            if (x, y) == self.posicion_powerup:
                intentos += 1
                continue
            return (x, y)
        return None

    def verificar_transicion_nivel(self):
        if self.tipo_juego != 'SNAKE': return
        
        if self.puntuacion < self.puntos_requeridos['ENTUSIASTA']:
            adecuado = 'BABY'
        elif self.puntuacion < self.puntos_requeridos['NYAN_CAT']:
            adecuado = 'ENTUSIASTA'
        else:
            adecuado = 'NYAN_CAT'
            
        if adecuado != self.nivel_actual:
            self.cambiar_nivel(adecuado)

    def manejar_input_gui(self, event):
        key = event.keysym.upper()
        
        if self.tipo_juego == 'TETRIS':
            if key == 'UP': self.ejecutar_evento('ON_KEY_UP')
            elif key == 'DOWN': self.ejecutar_evento('ON_KEY_DOWN')
            elif key == 'LEFT': self.ejecutar_evento('ON_KEY_LEFT')
            elif key == 'RIGHT': self.ejecutar_evento('ON_KEY_RIGHT')
        elif self.tipo_juego == 'SNAKE':
            # Permite el cambio manual de niveles para depuración y video demostrativo
            if key == '1':
                self.cambiar_nivel('BABY')
                self.puntuacion = 0
            elif key == '2':
                self.cambiar_nivel('ENTUSIASTA')
                self.puntuacion = self.puntos_requeridos['ENTUSIASTA']
            elif key == '3':
                self.cambiar_nivel('NYAN_CAT')
                self.puntuacion = self.puntos_requeridos['NYAN_CAT']
            
            # Direcciones de movimiento
            elif key == 'UP': self.snake_cambiar_direccion('UP')
            elif key == 'DOWN': self.snake_cambiar_direccion('DOWN')
            elif key == 'LEFT': self.snake_cambiar_direccion('LEFT')
            elif key == 'RIGHT': self.snake_cambiar_direccion('RIGHT')

    def dibujar(self):
        self.canvas.delete("all") # Borrar todo en cada frame
        self.label_score.config(text="PUNTUACION\n" + str(self.puntuacion))
        
        # Colores por defecto
        COLOR_GRID_FIJA = '#343434'
        COLOR_SNAKE_CABEZA = '#00FF00'
        COLOR_SNAKE_CUERPO = '#33CC33'
        COLOR_FOOD = '#FF0000'
        
        # 1. Dibujar la cuadricula estatica (grid base)
        for y in range(self.alto):
            for x in range(self.ancho):
                val_celda = self.grid[y][x]
                if val_celda != 0:
                     color = val_celda if not isinstance(val_celda, int) else COLOR_GRID_FIJA
                     self.dibujar_celda(x, y, color)

        # 2. Dibujar la pieza actual de Tetris
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
        
        # 3. Dibujar Snake, Comidas, Venenos, Obstáculos y Powerups
        if self.tipo_juego == 'SNAKE':
            # Comida Normal
            if self.posicion_comida:
                x, y = self.posicion_comida
                color = self.foods.get('APPLE', {}).get('color', COLOR_FOOD)
                forma = self.foods.get('APPLE', {}).get('form', 'CIRCLE')
                self.dibujar_celda(x, y, color, forma)
                
            # Frutas Venenosas
            for x, y in self.posiciones_veneno:
                color = self.foods.get('POISON_FRUIT', {}).get('color', '#9900FF')
                forma = self.foods.get('POISON_FRUIT', {}).get('form', 'CIRCLE')
                self.dibujar_celda(x, y, color, forma)
                
            # Power-Up "No Morir"
            if self.posicion_powerup:
                x, y = self.posicion_powerup
                color = self.powerups.get('IMMORTAL_FRUIT', {}).get('color', '#FFFF00')
                forma = self.powerups.get('IMMORTAL_FRUIT', {}).get('form', 'CIRCLE')
                self.dibujar_celda(x, y, color, forma)
                
            # Nubes Obstáculo
            for x, y in self.posiciones_nubes:
                color = self.obstacles.get('CLOUD', {}).get('color', '#CCCCCC')
                forma = self.obstacles.get('CLOUD', {}).get('form', 'CLOUD')
                self.dibujar_celda(x, y, color, forma)

            # Cuerpo de la Serpiente
            for i, segmento in enumerate(self.serpiente_cuerpo):
                x, y = segmento

                if i == 0:
                    if self.nivel_actual == 'NYAN_CAT':
                        forma = 'NYAN_CAT'
                        color = '#FFC0CB'
                    else:
                        forma = self.shapes.get("SNAKE_HEAD", {}).get("form", "CIRCLE")
                        color = '#FFD700' if self.invulnerable else COLOR_SNAKE_CABEZA
                else:
                    if self.nivel_actual == 'NYAN_CAT':
                        forma = self.shapes.get("SNAKE_BODY", {}).get("form", "TRIANGLE")
                        # Efecto multicolor Nyan Cat
                        rainbow = ['#FF0055', '#FF9900', '#FFFF00', '#33FF00', '#00FFFF', '#9900FF', '#FF00FF']
                        color = rainbow[i % len(rainbow)]
                    else:
                        forma = self.shapes.get("SNAKE_BODY", {}).get("form", "RECTANGLE")
                        color = '#FFA500' if self.invulnerable else COLOR_SNAKE_CUERPO

                self.dibujar_celda(x, y, color, forma)

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
            self.canvas.create_text(
                x1 + ts/2,
                y1 + ts/2,
                text="😺",
                font=('Segoe UI Emoji', 16)
            )
        elif forma == "CLOUD":
            self.canvas.create_text(
                x1 + ts/2,
                y1 + ts/2,
                text="☁️",
                font=('Segoe UI Emoji', 16)
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
                
                if verbo == 'INCREASE_SCORE': 
                    self.puntuacion += int(objeto)
                    self.verificar_transicion_nivel()
                    
                if verbo == 'GAME_OVER': 
                    self.juego_terminado = True

                if self.tipo_juego == 'TETRIS':
                    if verbo == 'SPAWN': self.tetris_spawn_pieza()
                    if verbo == 'MOVE': self.tetris_mover_pieza(accion['params'][0])
                    if verbo == 'ROTATE': self.tetris_rotar_pieza()
                
                if self.tipo_juego == 'SNAKE':
                    if verbo == 'SPAWN' and objeto == 'PLAYER': self.snake_spawn_jugador(accion)
                    if verbo == 'SPAWN' and objeto == 'FOOD': self.snake_spawn_comida()
                    if verbo == 'MOVE' and objeto == 'PLAYER': self.snake_mover_jugador()
                    if verbo == 'GROW': self.snake_crecer()

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
            if not (0 <= x < self.ancho): return True
            if not (0 <= y < self.alto): return True
            deepest_y = -1
            for y_check in range(self.alto - 1, -1, -1):
                if self.grid[y_check][x] == 0:
                    deepest_y = y_check
                    break
            if y > deepest_y: return True
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
        
    def snake_spawn_comida(self):
        pos = self.obtener_posicion_vacia()
        if pos:
            self.posicion_comida = pos
                
    def snake_mover_jugador(self):
        if not self.serpiente_cuerpo: return
        cabeza_x, cabeza_y = self.serpiente_cuerpo[0]
        dir_x, dir_y = self.serpiente_direccion
        nueva_cabeza = (cabeza_x + dir_x, cabeza_y + dir_y)

        # Guardar la dirección real de este movimiento para validar giros en futuros ticks
        self.serpiente_direccion_actual = self.serpiente_direccion

        # 1. Verificar colisiones de pared con soporte de wrap-around en invulnerabilidad o nivel Nyan Cat
        colision_pared = not (0 <= nueva_cabeza[0] < self.ancho and 0 <= nueva_cabeza[1] < self.alto)
        if colision_pared:
            if self.invulnerable or self.nivel_actual == 'NYAN_CAT':
                nueva_cabeza = (nueva_cabeza[0] % self.ancho, nueva_cabeza[1] % self.alto)
                if self.nivel_actual == 'NYAN_CAT' and not self.invulnerable:
                    if self.puntuacion > 0:
                        self.puntuacion = 0
                        self.verificar_transicion_nivel()
                    else:
                        self.juego_terminado = True
                        return
            else:
                self.ejecutar_evento('ON_COLLISION_WALL')
                return

        # 2. Verificar colisiones con uno mismo (self-collision)
        if nueva_cabeza in self.serpiente_cuerpo[:-1]:
            if not self.invulnerable:
                if self.nivel_actual == 'NYAN_CAT':
                    if self.puntuacion > 0:
                        self.puntuacion = 0
                        self.verificar_transicion_nivel()
                    else:
                        self.juego_terminado = True
                        return
                else:
                    self.ejecutar_evento('ON_COLLISION_SELF')
                    return

        # 3. Colisión con Nubes Obstáculo
        if nueva_cabeza in self.posiciones_nubes:
            if not self.invulnerable:
                if self.puntuacion > 0:
                    self.puntuacion = 0
                    self.verificar_transicion_nivel()
                else:
                    self.juego_terminado = True
                    return

        # 4. Colisión con Frutas Venenosas
        if nueva_cabeza in self.posiciones_veneno:
            self.posiciones_veneno.remove(nueva_cabeza)
            pos = self.obtener_posicion_vacia()
            if pos: self.posiciones_veneno.append(pos)
            
            if not self.invulnerable:
                self.puntuacion = max(0, self.puntuacion - 10)
                if self.puntuacion == 0:
                    self.juego_terminado = True
                    return
                self.verificar_transicion_nivel()
            
            # Movimiento normal al comer veneno (no crece)
            self.serpiente_cuerpo.insert(0, nueva_cabeza)
            self.serpiente_cuerpo.pop()
            return

        # 5. Colisión con el Power-Up "No Morir"
        if nueva_cabeza == self.posicion_powerup:
            self.posicion_powerup = None
            self.invulnerable = True
            duration = self.powerups.get('IMMORTAL_FRUIT', {}).get('duration', 5)
            self.invulnerable_until = time.time() + duration
            
            self.serpiente_cuerpo.insert(0, nueva_cabeza)
            self.serpiente_cuerpo.pop()
            return

        # 6. Colisión con Comida Normal
        if nueva_cabeza == self.posicion_comida:
            self.serpiente_cuerpo.insert(0, nueva_cabeza)
            self.ejecutar_evento('ON_EAT_FOOD')
            
            # Chance de spawnear Power-Up en niveles altos (obtenido dinámicamente desde el bloque DEFINE)
            if self.nivel_actual in ['ENTUSIASTA', 'NYAN_CAT'] and not self.posicion_powerup:
                chance_val = self.powerups.get('IMMORTAL_FRUIT', {}).get('chance', 10)
                probabilidad = float(chance_val) / 100.0 # Ej: 10 -> 0.10 (10% de probabilidad)
                if random.random() < probabilidad:
                    pos = self.obtener_posicion_vacia()
                    if pos: self.posicion_powerup = pos
            return

        # 7. Movimiento Normal
        self.serpiente_cuerpo.insert(0, nueva_cabeza)
        self.serpiente_cuerpo.pop()

    def snake_cambiar_direccion(self, direccion):
        # Usar la dirección real del último movimiento para evitar giros de 180 grados en el mismo tick
        dir_actual = getattr(self, 'serpiente_direccion_actual', self.serpiente_direccion)
        if direccion == 'UP' and dir_actual[1] != 1:
            self.serpiente_direccion = (0, -1)
        elif direccion == 'DOWN' and dir_actual[1] != -1:
            self.serpiente_direccion = (0, 1)
        elif direccion == 'LEFT' and dir_actual[0] != 1:
            self.serpiente_direccion = (-1, 0)
        elif direccion == 'RIGHT' and dir_actual[0] != -1:
            self.serpiente_direccion = (1, 0)

    def snake_crecer(self):
        pass

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
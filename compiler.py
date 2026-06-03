# compiler.py
# Compilador universal para BrickScript (Version Final y Depurada)
# Uso: python compiler.py <archivo_entrada.brick>

import sys
import re
import json

def lexer(codigo_fuente):
    # Eliminar comentarios pero mantener codigos de color hexadecimales
    codigo_fuente = re.sub(r'#(?![0-9A-Fa-f]{6}\b|[0-9A-Fa-f]{3}\b).*', '', codigo_fuente)
    # Soporta numeros decimales (ej. 0.15, 0.07) e enteros
    token_regex = r'#[0-9A-Fa-f]{6}\b|#[0-9A-Fa-f]{3}\b|\b[A-Z_]+\b|\d+\.\d+|\d+|[\[\](),:]'
    tokens = re.findall(token_regex, codigo_fuente)
    return tokens

class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.posicion = 0
        self.ast = {
            "tipo_juego": None, 
            "config": {}, 
            "shapes": {}, 
            "foods": {}, 
            "obstacles": {}, 
            "powerups": {}, 
            "events": {},
            "levels": {}
        }

    def parse(self):
        while self.posicion < len(self.tokens):
            token_actual = self.tokens[self.posicion]
            if token_actual == 'GAME_TYPE':
                self.parsear_tipo_juego()
            elif token_actual == 'GAME_GRID':
                self.parsear_grid()
            elif token_actual == 'LEVELS':
                self.parsear_bloque_niveles()
            elif token_actual == 'DEFINE':
                self.parsear_shape()
            elif token_actual == 'ON':
                self.parsear_evento()
            else:
                self.posicion += 1
        return self.ast

    def consumir(self, token_esperado=None):
        if self.posicion < len(self.tokens):
            token = self.tokens[self.posicion]
            if token_esperado and token != token_esperado:
                raise Exception("Error de sintaxis: Se esperaba '" + token_esperado + "' pero se encontro '" + token + "'")
            self.posicion += 1
            return token
        if token_esperado:
            raise Exception("Error de sintaxis: Se esperaba '" + token_esperado + "' pero se llego al final del archivo.")
        return None

    def parsear_tipo_juego(self):
        self.consumir('GAME_TYPE')
        self.ast['tipo_juego'] = self.consumir()

    def parsear_grid(self):
        self.consumir('GAME_GRID')
        self.consumir('(')
        ancho = int(self.consumir())
        self.consumir(',')
        alto = int(self.consumir())
        self.consumir(')')
        self.ast['config']['grid_size'] = [ancho, alto]

    def parsear_bloque_niveles(self):
        self.consumir('LEVELS')
        while self.posicion < len(self.tokens) and self.tokens[self.posicion] != 'END':
            nombre_nivel = self.consumir()
            self.consumir(':')
            attrs = {}
            while self.posicion < len(self.tokens) and self.tokens[self.posicion] != 'END':
                attr = self.consumir()
                val = self.consumir()
                if attr == 'SPEED':
                    attrs['speed'] = float(val)
                elif attr == 'POWERUP_DURATION':
                    attrs['powerup_duration'] = int(val)
            self.consumir('END')
            self.ast['levels'][nombre_nivel] = attrs
        self.consumir('END')

    def parsear_shape(self):
        self.consumir('DEFINE')
        tipo = self.consumir()  # Puede ser 'SHAPE', 'FOOD', 'OBSTACLE' o 'POWERUP'
        nombre = self.consumir()
        self.consumir(':')
        forma = 'RECTANGLE'
        color = "#00FFFF"
        chance = 10
        efecto = None
        duracion = None

        # Parsear atributos opcionales en cualquier orden
        while self.posicion < len(self.tokens) and self.tokens[self.posicion] in ['FORM', 'COLOR', 'CHANCE', 'EFFECT', 'DURATION']:
            attr = self.consumir()
            if attr == 'FORM':
                forma = self.consumir()
            else:
                self.consumir(':')
                val = self.consumir()
                if attr == 'COLOR':
                    color = val
                elif attr == 'CHANCE':
                    chance = int(val)
                elif attr == 'EFFECT':
                    efecto = val
                elif attr == 'DURATION':
                    duracion = int(val)

        estados = []
        while self.posicion < len(self.tokens) and self.tokens[self.posicion] == 'STATE':
            self.consumir('STATE')
            self.consumir()
            self.consumir(':')
            matriz = []
            while self.posicion < len(self.tokens) and self.tokens[self.posicion] == '[':
                fila = []
                self.consumir('[')
                while self.tokens[self.posicion] != ']':
                    fila.append(int(self.consumir()))
                    if self.tokens[self.posicion] == ',': self.consumir(',')
                self.consumir(']')
                matriz.append(fila)
            estados.append(matriz)
        self.consumir('END')

        # Guardar en la coleccion correspondiente
        info = {
            "form": forma,
            "color": color,
            "chance": chance,
            "states": estados
        }
        if efecto is not None:
            info["effect"] = efecto
        if duracion is not None:
            info["duration"] = duracion

        if tipo == 'POWERUP':
            self.ast['powerups'][nombre] = info
        elif tipo == 'FOOD':
            self.ast['foods'][nombre] = info
        elif tipo == 'OBSTACLE':
            self.ast['obstacles'][nombre] = info
        else:
            self.ast['shapes'][nombre] = info

    # --- FUNCION CORREGIDA ---
    def parsear_evento(self):
        self.consumir('ON')
        nombre_evento = 'ON_' + self.consumir()
        self.consumir(':')
        acciones = []
        while self.posicion < len(self.tokens) and self.tokens[self.posicion] != 'END':
            verbo = self.consumir()
            
            # Si el comando es de una sola palabra, lo anadimos y continuamos
            if verbo == 'GAME_OVER':
                acciones.append({'accion': verbo, 'objeto': None, 'params': []})
                continue
            
            # Si no, parseamos el resto de la accion
            objeto = self.consumir()
            params = []
            if self.posicion < len(self.tokens) and self.tokens[self.posicion] == 'AT':
                self.consumir('AT')
                if self.tokens[self.posicion] == 'RANDOM':
                    params.append(self.consumir())
                else:
                    self.consumir('(')
                    x = int(self.consumir())
                    self.consumir(',')
                    y = int(self.consumir())
                    self.consumir(')')
                    params.append([x, y])
            elif self.posicion < len(self.tokens) and self.tokens[self.posicion] not in ['END', 'ON', 'DEFINE', 'SPAWN', 'MOVE', 'ROTATE', 'INCREASE_SCORE', 'SET_DIRECTION', 'GROW', 'GAME_OVER']:
                params.append(self.consumir())
            acciones.append({'accion': verbo, 'objeto': objeto, 'params': params})
        self.consumir('END')
        self.ast['events'][nombre_evento] = acciones

def generar_codigo(ast, archivo_salida):
    with open(archivo_salida, 'w') as f:
        json.dump(ast, f, indent=2)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Uso: python compiler.py <archivo_entrada.brick>")
        sys.exit(1)
    archivo_entrada = sys.argv[1]
    archivo_salida = archivo_entrada.replace('.brick', '.json')
    print("Compilando " + archivo_entrada + "...")
    try:
        with open(archivo_entrada, 'r') as f:
            codigo = f.read()
        tokens = lexer(codigo)
        parser = Parser(tokens)
        ast = parser.parse()
        generar_codigo(ast, archivo_salida)
        print("Compilacion exitosa! Archivo de juego creado en " + archivo_salida)
    except Exception as e:
        print("\n!!! ERROR DE COMPILACION !!!")
        print(str(e))
        sys.exit(1)
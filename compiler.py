# compiler.py
# Compilador universal para BrickScript (Version Final y Depurada)
# Uso: python compiler.py <archivo_entrada.brick>

import sys
import re
import json

def lexer(codigo_fuente):
    # Eliminar comentarios pero mantener codigos de color hexadecimales
    codigo_fuente = re.sub(r'#(?![0-9A-Fa-f]{6}\b|[0-9A-Fa-f]{3}\b).*', '', codigo_fuente)
    token_regex = r'#[0-9A-Fa-f]{6}\b|#[0-9A-Fa-f]{3}\b|\b[A-Z_]+\b|\d+|[\[\](),:]'
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
            "levels": {},
            "boss": {},
            "events": {}
        }

    def parse(self):
        while self.posicion < len(self.tokens):
            token_actual = self.tokens[self.posicion]
            if token_actual == 'GAME_TYPE':
                self.parsear_tipo_juego()
            elif token_actual == 'GAME_GRID':
                self.parsear_grid()
            elif token_actual == 'DEFINE':
                self.parsear_shape()
            elif token_actual == 'ON':
                self.parsear_evento()
            elif token_actual == 'LEVELS':
                self.parsear_levels()

            elif token_actual == 'BOSS':
                self.parsear_boss()
            
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

    def parsear_shape(self):
        self.consumir('DEFINE')
        tipo = self.consumir()  # Puede ser 'SHAPE' o 'POWERUP'
        nombre = self.consumir()
        self.consumir(':')
        forma = 'RECTANGLE'

        if self.posicion < len(self.tokens) and self.tokens[self.posicion] == 'FORM':
            self.consumir('FORM')
            forma = self.consumir()
        # Valores por defecto para atributos adicionales
        color = "#00FFFF"
        chance = 10
        effect = None
        duration = None
        tipo_entidad = None
        hp = None
        damage = None
        speed = None
        
        # Parsear atributos opcionales COLOR y CHANCE
        while self.posicion < len(self.tokens) and self.tokens[self.posicion] in [
                                                                                    'COLOR',
                                                                                    'CHANCE',
                                                                                    'EFFECT',
                                                                                    'DURATION',
                                                                                    'TYPE',
                                                                                    'HP', 
                                                                                    'DAMAGE',
                                                                                    'SPEED'
                                                                                  ]:
            attr = self.consumir()
            self.consumir(':')
            val = self.consumir()
            if attr == 'COLOR':
                color = val

            elif attr == 'CHANCE':
                chance = int(val)

            elif attr == 'EFFECT':
                 effect = val

            elif attr == 'DURATION':
                 duration = int(val)

            elif attr == 'TYPE':
                 tipo_entidad = val

            elif attr == 'HP':
                 hp = int(val)

            elif attr == 'DAMAGE':
                 damage = int(val)

            elif attr == 'SPEED':
                 speed = int(val)
                
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
        datos = {

            "form": forma,
            "color": color,
            "chance": chance,

            "type": tipo_entidad,

            "hp": hp,

            "damage": damage,

            "speed": speed,

            "states": estados,

            "effect": effect,
            "duration": duration
        }

        if tipo == 'SHAPE':
            self.ast['shapes'][nombre] = datos

        elif tipo == 'FOOD':
            self.ast['foods'][nombre] = datos

        elif tipo == 'OBSTACLE':
            self.ast['obstacles'][nombre] = datos

        elif tipo == 'POWERUP':
            self.ast['powerups'][nombre] = datos
    def parsear_levels(self):

        self.consumir('LEVELS')
        self.consumir(':')
    
        while self.tokens[self.posicion] != 'END':
        
            nivel = self.consumir()
    
            self.consumir(':')
    
            datos_nivel = {}
    
            while self.tokens[self.posicion] != 'END':
            
                atributo = self.consumir()
    
                self.consumir(':')
    
                valor = self.consumir()
    
                if atributo == 'SPEED':
                    datos_nivel["speed"] = int(valor)
    
                elif atributo == 'POWERUP_DURATION':
                    datos_nivel["powerup_duration"] = int(valor)
    
            self.consumir('END')
    
            self.ast["levels"][nivel] = datos_nivel
    
        self.consumir('END')
    


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

            #if verbo == 'VICTORY':
            
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

    def parsear_boss(self):

        self.consumir('BOSS')

        nombre = self.consumir()

        color = "#FF00FF"
        hp = 100
        damage = 50

        while self.tokens[self.posicion] in [
            'COLOR',
            'HP',
            'DAMAGE'
        ]:

            atributo = self.consumir()

            self.consumir(':')

            valor = self.consumir()

            if atributo == 'COLOR':
                color = valor

            elif atributo == 'HP':
                hp = int(valor)

            elif atributo == 'DAMAGE':
                damage = int(valor)

        estados = []

        while self.tokens[self.posicion] == 'STATE':

            self.consumir('STATE')

            self.consumir()

            self.consumir(':')

            matriz = []

            while self.tokens[self.posicion] == '[':

                fila = []

                self.consumir('[')

                while self.tokens[self.posicion] != ']':
                    fila.append(int(self.consumir()))

                    if self.tokens[self.posicion] == ',':
                        self.consumir(',')

                self.consumir(']')

                matriz.append(fila)

            estados.append(matriz)

        self.consumir('END')

        self.ast["boss"] = {

            "name": nombre,

            "color": color,

            "hp": hp,

            "damage": damage,

            "states": estados
        }

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
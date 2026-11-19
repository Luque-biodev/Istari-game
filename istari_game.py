#############################################################################################################
import pygame
import os
import numpy as np
import random
import math

pygame.init() #Inicia pygame

#960, 576
BASE_SIZE = (600, 360)     # resolución interna del juego
SCALE = 2                  # 400x3 = 1200, 240x3 = 720
WINDOW_SIZE = (BASE_SIZE[0] * SCALE, BASE_SIZE[1] * SCALE)

screen = pygame.display.set_mode(WINDOW_SIZE)
canvas = pygame.Surface(BASE_SIZE)     # aquí se dibuja todo
pygame.display.set_caption("ISTARI GAME") #Nombbre de la ventana

#SCALE
def screen_to_world(pos):
    """Ventana (píxeles reales) -> lienzo (píxeles del juego)."""
    return (pos[0] // SCALE, pos[1] // SCALE)

def world_to_screen(pos):
    """Lienzo -> ventana. Útil para debug fino o UI a resolución real."""
    return (pos[0] * SCALE, pos[1] * SCALE)

def mouse_world_pos():
    """Posición actual del ratón en coordenadas del juego."""
    return screen_to_world(pygame.mouse.get_pos())







# Creamos el reloj
clock = pygame.time.Clock()


#Personaje
personaje_activo = "gandalf"



#############################################################################################################


sprites = {}
params = {}

# CARGA DE TODOS LOS SPRITES y PARAMS.txt
def load_assets():

    for ruta_actual, carpetas, archivos in os.walk("sprites"):

        for archivo in archivos:

            ruta = os.path.join(ruta_actual, archivo)

            # ----------------
            # SPRITES
            # ----------------

            if archivo.endswith(".png"):

                sprite = pygame.image.load(ruta).convert()
                sprite.set_colorkey((163, 73, 164))

                sprites[archivo] = sprite

            # ----------------
            # PARAMS
            # ----------------

            elif archivo.endswith(".txt"):

                nombre = os.path.splitext(archivo)[0]


                print("archivo:", repr(archivo))
                print("nombre:", repr(nombre))


                params[nombre] = {}

                with open(ruta, "r") as file:

                    for linea in file:
                        linea = linea.strip()
                        if not linea or "=" not in linea:
                            continue
                        key, value = linea.split("=", 1)

                        #El problema es que entonces todo sería str:
                        try:
                            value = float(value)

                            if value.is_integer():
                                value = int(value)

                        except ValueError:
                            pass

                        params[nombre][key] = value

load_assets()




print(params)
print(params.keys())
print(sprites.keys())

#sprites["gandalf_down.png"]
#params["gandalf"]["speed"]
#params["gandalf"]["health"]
#params["gandalf"]["mana"]
print(sprites["gandalf_down.png"])
print(params["gandalf"]["speed"])

#############################################################################################################

zoom = 1.0


def actualizar_posicion(x, y, angle, speed):

    x += math.cos(angle) * speed
    y += math.sin(angle) * speed

    return x, y


def actualizar_direccion_visual(entity):
    angle = entity.angle
    eps = 1e-6

    # Diagonales: conservar la dirección actual si es una de las dos válidas
    diagonales = {
        math.pi / 4:      ("right", "down"),
        3 * math.pi / 4:  ("left", "down"),
        -math.pi / 4:     ("right", "up"),
        -3 * math.pi / 4: ("left", "up"),
    }
    for diag, opciones in diagonales.items():
        if abs(angle - diag) < eps:
            if entity.direction not in opciones:
                entity.direction = opciones[0]
            return

    if -math.pi / 4 < angle < math.pi / 4:
        entity.direction = "right"
    elif math.pi / 4 < angle < 3 * math.pi / 4:
        entity.direction = "down"
    elif -3 * math.pi / 4 < angle < -math.pi / 4:
        entity.direction = "up"
    else:
        entity.direction = "left"




#angle = -45°  → up/right → decides según la lógica que quieras
#angle = +45°  → down/right
#angle = +135° → down/left
#angle = -135° → up/left

#############################################################################################################
#CONTROLES
SHIFT = pygame.KMOD_SHIFT
CTRL  = pygame.KMOD_CTRL
ALT   = pygame.KMOD_ALT

def mods_actuales():
    m = pygame.key.get_mods()
    resultado = 0
    for mod in (SHIFT, CTRL, ALT):
        if m & mod:
            resultado |= mod
    return resultado

SHAKE_ACCEL_THRESHOLD = 150000

class MouseMotion:
    def __init__(self):
        self.prev_speed = 0.0
        self.speed = 0.0
        self.accel = 0.0

    def update(self, dt):
        dx, dy = pygame.mouse.get_rel()
        if dt <= 0:
            return
        self.speed = math.hypot(dx, dy) / dt
        self.accel = (self.speed - self.prev_speed) / dt
        self.prev_speed = self.speed

########################
#Una entidad es simplemente algo que existe en el mapa y que podemos colocar y dibujar.
class Entity:
    def __init__(self, x, y, sprite):
        self.x = x
        self.y = y
        self.sprite = sprite
        self.alive = True
        self.team = None

    @property
    def center(self):
        return (self.x + self.sprite.get_width() / 2,
                self.y + self.sprite.get_height() / 2)

    @property
    def rect(self):
        return pygame.Rect(self.x, self.y,
                           self.sprite.get_width(),
                           self.sprite.get_height())
    


    def draw(self, screen):
        screen.blit(self.sprite, (self.x, self.y))

    def move_by_angle(self, angle, speed):
        self.x, self.y = actualizar_posicion(
            self.x,
            self.y,
            angle,
            speed
        )
    
    def update(self, dt):
        pass

#Con draw(), cualquier cosa que herede de Entity podrá dibujarse.





###################################################

#Resumen de responsabilidades
#Clase	            Contiene	                                    No contiene
#Character	        attack, dash, run, move_dir, stats	            teclas, ratón, IA
#Player	            bindings, handle_event/held/mouse_motion	    lógica de ataques
#Enemy / NPC	    think() (IA)	                                teclas, ratón
####################################################
#Character: una Entity que tiene estadísticas
class Character(Entity):

    def __init__(self, name, x, y, sprite, params):
        super().__init__(x, y, sprite)

        self.name = name

        self.base_speed = params["speed"]
        self.speed = self.base_speed
        self.health = params["health"]
        self.mana = params["mana"]
        self.strength = params["strength"]
        self.intelligence = params["intelligence"]
        self.agility = params["agility"]

        self.attack_name = params["attack"]
        self.angle = 0
        self.direction = "down"

      # ----- Capacidades (las usan jugador, enemigos y NPCs) -----

    def attack(self, entities, target_pos):
        attacks[self.attack_name](self, entities, target_pos)

    def charged_attack(self, entities, target_pos):
        print(self.name, "ataque cargado")

    def dash(self):
        print(self.name, "dash")

    def run(self, active):
        self.speed = self.base_speed * (1.5 if active else 1.0)

    def move_dir(self, dx, dy):
        """Mueve en una dirección (dx, dy). Sin saber de dónde viene la orden."""
        if dx == 0 and dy == 0:
            return
        self.angle = math.atan2(dy, dx)
        actualizar_direccion_visual(self)
        self.sprite = sprites[f"{self.name}_{self.direction}.png"]
        self.move_by_angle(self.angle, self.speed)

    def take_damage(self, amount):
        self.health -= amount
        print(self.name, "recibe", amount, "-> vida", self.health)
        if self.health <= 0:
            self.alive = False


#player: un Entity,Character controlado por el jugador
class Player(Character):

    def __init__(self, name, x, y, sprite, params):
        super().__init__(name, x, y, sprite, params)
        self.registro_direccion = []
        self.mouse_motion = MouseMotion()
        self.team = "player"

        # Tablas de asociación: apuntan a MÉTODOS de Character
        self.keydown_bindings = {
            (pygame.K_SPACE, 0): lambda e, ents: self.dash(),
        }

            #Elemento	    Qué es	                    Valores
            #Primero	    Botón del ratón	            1 izquierdo, 2 central, 3 derecho
            #Segundo	    Modificadores pulsados	    0 ninguno, SHIFT, CTRL, ALT 
        self.mouse_bindings = {
            #Un lambda es una función pequeña sin nombre.
                # e: el evento de pygame (de ahí saca e.pos, la posición del click).
                # ents: la lista entities, donde attack añadirá el proyectil.
            (1, 0):     lambda e, ents: self.attack(ents, screen_to_world(e.pos)),
            (1, SHIFT): lambda e, ents: self.charged_attack(ents, screen_to_world(e.pos)),
            (3, 0): lambda e, ents: sword_slash(self, ents, screen_to_world(e.pos)),
        }

    def handle_event(self, event, entities):
        """Eventos discretos."""
        if event.type == pygame.KEYDOWN:
            accion = self.keydown_bindings.get((event.key, mods_actuales()))
        elif event.type == pygame.MOUSEBUTTONDOWN:
            accion = self.mouse_bindings.get((event.button, mods_actuales()))
        else:
            return

        if accion:
            accion(event, entities)

    def handle_held(self, teclas):
        """Entrada continua."""
        self.run(teclas[pygame.K_LSHIFT])
        #run es método en character, no necesita saber de teclas ni ratón, solo si el jugador quiere correr o no.

        dx = teclas[pygame.K_d] - teclas[pygame.K_a]
        dy = teclas[pygame.K_s] - teclas[pygame.K_w]

        self.move_dir(dx, dy)

        if dx or dy:
            self.registro_direccion.append(self.angle)
            self.registro_direccion = self.registro_direccion[-5:]

    def handle_mouse_motion(self, dt):
        self.mouse_motion.update(dt)
        if self.mouse_motion.accel > SHAKE_ACCEL_THRESHOLD:
            print("¡Sacudida!")



#############
class Enemy(Character):

    def __init__(self, name, x, y, sprite, params):
        super().__init__(name, x, y, sprite, params)
        self.attack_cooldown = 0

    def think(self, player, entities, dt):
        """IA: decide y llama a las mismas capacidades de Character."""
        dx = player.x - self.x
        dy = player.y - self.y
        dist = math.hypot(dx, dy)

        if dist > 200:
            self.move_dir(dx, dy)        # perseguir
        elif self.attack_cooldown <= 0:
            self.attack(entities, (player.x, player.y))
            self.attack_cooldown = 2.0   # segundos

        self.attack_cooldown -= dt
####################################################
####### ITEMS, OBJETOS Y EQUIPAMIENTO
##########################################




###################################################################
#ENTITIES FOR ATTACKS
####################################################
class Projectile(Entity):

    def __init__(self, x, y, sprite, angle, speed, damage):
        # Rotamos UNA vez, al crear (no cada frame)
        rotated = pygame.transform.rotate(sprite, -math.degrees(angle))
        rotated.set_colorkey((163, 73, 164))

        # Al rotar, el tamaño cambia: reposicionamos para mantener el centro
        cx = x + sprite.get_width() / 2
        cy = y + sprite.get_height() / 2
        super().__init__(cx - rotated.get_width() / 2,
                         cy - rotated.get_height() / 2,
                         rotated)


        self.angle = angle
        self.speed = speed
        self.damage = damage

        self.direction_x = math.cos(angle)
        self.direction_y = math.sin(angle)

    def update(self, dt):
        self.move_by_angle(self.angle, self.speed)
        if not (-50 < self.x < 1250 and -50 < self.y < 770):
            self.alive = False


# Hitbox para melee
# Es una entidad temporal que hace daño y desaparece:

class Hitbox(Entity):
    def __init__(self, x, y, sprite, lifetime, damage, team):
        super().__init__(x, y, sprite)
        self.lifetime = lifetime
        self.damage = damage
        self.team = team
        self.already_hit = set()   # para golpear una sola vez a cada objetivo

    def update(self, dt):
        self.lifetime -= dt
        if self.lifetime <= 0:
            self.alive = False
        




########################################
#############################################################################################################
def angle_to(origin, target_pos):
    """Ángulo desde el centro de 'origin' hasta un punto."""
    cx, cy = origin.center
    return math.atan2(target_pos[1] - cy, target_pos[0] - cx)

def compute_damage(attacker, p):
    """Daño base del ataque + stat del atacante * factor."""
    damage = p["damage"]
    stat = p.get("scaling_stat")
    if stat:
        damage += getattr(attacker, stat, 0) * p.get("scaling", 0)
    return damage


def spawn_projectile(attacker, entities, angle, sprite_name, params_name):
    """Crea un proyectil centrado en el atacante y lo añade a entities."""
    sprite = sprites[sprite_name]
    p = params[params_name]
    cx, cy = attacker.center

    projectile = Projectile(
        cx - sprite.get_width() / 2,
        cy - sprite.get_height() / 2,
        sprite,
        angle,
        p["speed"],
        compute_damage(attacker, p)      # antes: p["damage"]
    )
    projectile.team = attacker.team
    entities.append(projectile)
    return projectile

#Tipo	        Qué añade a entities	                    Clase nueva
#Proyectil	    Projectile que se mueve	                    ya la tienes
#Slash melee	Hitbox que vive unos frames y desaparece	Hitbox(Entity)
#Invocación	    un Enemy/NPC nuevo	                        ya la tienes


#Información ataques
def fireball(attacker, entities, target_pos):
    angle = angle_to(attacker, target_pos)
    spawn_projectile(attacker, entities, angle, "fireball1.png", "fireball")
#def sword_slash(attacker, entities):
    # crear hitbox del espadazo


# Melee: hitbox temporal delante del atacante
def sword_slash(attacker, entities, target_pos):
    p = params["slash"]
    sprite = sprites["slash1.png"]
    angle = angle_to(attacker, target_pos)
    cx, cy = attacker.center

    # Centro de la hitbox: delante del atacante
    hx = cx + math.cos(angle) * p["reach"]
    hy = cy + math.sin(angle) * p["reach"]

    entities.append(Hitbox(
        hx - sprite.get_width() / 2,      # centrado en (hx, hy)
        hy - sprite.get_height() / 2,
        sprite,
        lifetime=p["lifetime"],
        damage=compute_damage(attacker, p),
        team=attacker.team
    ))

# Invocación: crea un Character en el mapa
def summon_skeleton(attacker, entities, target_pos):
    entities.append(Enemy("skeleton", target_pos[0], target_pos[1],
                          sprites["skeleton_down.png"], params["skeleton"]))

attacks = {
    "fireball": fireball,
    "sword_slash": sword_slash,
    "summon_skeleton": summon_skeleton,
}






############################################################################################
def resolve_collisions(entities):
    attackers = [e for e in entities if isinstance(e, (Projectile, Hitbox))]
    targets   = [e for e in entities if isinstance(e, Character)]

    for a in attackers:
        for t in targets:
            if not a.alive or a.team == t.team:
                continue
            if isinstance(a, Hitbox) and t in a.already_hit:
                continue
            if a.rect.colliderect(t.rect):
                t.take_damage(a.damage)
                if isinstance(a, Hitbox):
                    a.already_hit.add(t)
                else:
                    a.alive = False




#############################################################################################################


#BACKGROUND
background = pygame.image.load("sprites/Map_small.png").convert()


entities = []

player = Player(
    personaje_activo,
    400,
    300,
    sprites["gandalf_down.png"],
    params["gandalf"]
)
player.team = "player"
entities = [player]

running = True
debug_hitboxes = False

def draw_debug(screen, entities, player):
    colores = {
        Projectile: (255, 255, 0),   # amarillo
        Hitbox:     (255, 0, 0),     # rojo
        Character:  (0, 255, 0),     # verde
    }
    for e in entities: 
        color = (255, 255, 255)
        for clase, c in colores.items():
            if isinstance(e, clase):
                color = c
                break
        pygame.draw.rect(screen, color, e.rect, 1)           # contorno de 1 px
        pygame.draw.circle(screen, color, (int(e.center[0]), int(e.center[1])), 2)  # centro



while running:
    dt = clock.tick(60) / 1000

    # ---------- EVENTOS ----------
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_F3:
            debug_hitboxes = not debug_hitboxes
        player.handle_event(event, entities)

    # ---------- INPUT CONTINUO ----------
    player.handle_held(pygame.key.get_pressed())
    player.handle_mouse_motion(dt)

    # ---------- UPDATE ----------
    for entity in entities[:]:
        if isinstance(entity, Enemy):
            entity.think(player, entities, dt)
        entity.update(dt)

    resolve_collisions(entities)
    entities[:] = [e for e in entities if e.alive]

    # ---------- DRAW ----------
    canvas.fill((30, 30, 30))
    canvas.blit(background, (0, 0))

    for entity in sorted(entities, key=lambda e: e.rect.bottom):
        entity.draw(canvas)              # antes: screen

    if debug_hitboxes:
        draw_debug(canvas, entities, player)

    pygame.transform.scale(canvas, WINDOW_SIZE, screen)   # nearest neighbor, sin suavizado
    pygame.display.flip()

pygame.quit()

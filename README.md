# ISTARI GAME

Juego 2D visto desde arriba, hecho con **Python + Pygame**. Controlas a **Gandalf**: te mueves en ocho direcciones y lanzas **bolas de fuego** hacia donde apunta el cursor.

---

## Controles

| Entrada | Acción |
|---------|--------|
| `W` `A` `S` `D` | Mover (arriba, izquierda, abajo, derecha). Se pueden combinar para ir en diagonal |
| `Shift izq.` (mantener) | Correr (velocidad ×1.5) |
| `Clic izquierdo` | Lanzar bola de fuego hacia el cursor |
| `F3` | Mostrar/ocultar hitboxes de depuración (verde: personajes, amarillo: proyectiles) |
| Cerrar ventana | Salir |

---

## Requisitos

- **Python 3.8 o superior**
- Librerías: `pygame` y `numpy` (el código importa ambas)

## Instalación

1. Entra en la carpeta del proyecto:

   ```bash
   cd ruta/al/proyecto
   ```

2. (Recomendado) Crea y activa un entorno virtual:

   ```bash
   python -m venv venv

   # Linux / macOS
   source venv/bin/activate

   # Windows (PowerShell)
   venv\Scripts\Activate.ps1
   ```

3. Instala las dependencias:

   ```bash
   pip install pygame numpy
   ```

## Ejecución

Desde la carpeta del proyecto (los recursos se cargan con rutas relativas):

```bash
python istari_game.py
```

Se abre una ventana de **1200 × 720** a 60 FPS. Al arrancar, la consola imprime los parámetros y sprites cargados.

---

## Estructura del proyecto

La carpeta `sprites/` debe estar junto a `istari_game.py`:

```
proyecto/
├── istari_game.py
└── sprites/
    ├── Map_small.png        # fondo del mapa
    ├── gandalf_up.png       # un sprite por dirección
    ├── gandalf_down.png
    ├── gandalf_left.png
    ├── gandalf_right.png
    ├── fireball1.png        # sprite del proyectil
    ├── gandalf.txt          # parámetros del personaje
    └── fireball.txt         # parámetros del ataque
```

### Archivos de parámetros (`.txt`)

Formato `clave=valor`, una por línea. Los números se convierten automáticamente a `int` o `float`; el resto queda como texto.

- **`gandalf.txt`**: `speed`, `health`, `mana`, `strength`, `intelligence`, `agility`, `attack` (nombre del ataque, `fireball`).
- **`fireball.txt`**: `speed`, `damage` y, opcionalmente, `scaling_stat` y `scaling`.

### Sprites

- Formato `.png`. El color `(163, 73, 164)` (magenta/púrpura) se usa como transparente.
- Los sprites del personaje siguen el patrón `<nombre>_<dirección>.png` (`up`, `down`, `left`, `right`).

---

## Mecánicas

- **Movimiento en 8 direcciones.** Se calcula un vector `(dx, dy)` a partir de las teclas, se convierte en ángulo con `atan2` y se avanza con `cos`/`sin` por la velocidad. Al pulsar dos teclas se obtiene la diagonal.
- **Dirección visual.** El ángulo decide qué sprite se muestra (arriba, abajo, izquierda o derecha). En las diagonales se conserva la dirección actual si ya era una de las dos válidas, para evitar parpadeos de sprite.
- **Correr.** Mantener `Shift izq.` multiplica la velocidad base por 1.5.
- **Bola de fuego.** Se crea en el centro del personaje y viaja en línea recta hacia la posición del cursor. Desaparece al chocar con un personaje de otro equipo o al salir de los límites del mapa.
- **Daño con escalado.** El daño final es `damage + stat_del_atacante × scaling`, donde `scaling_stat` es el nombre de un atributo del personaje (por ejemplo `intelligence`). Todo se define en los `.txt`, sin tocar el código.
- **Equipos y colisiones.** Cada entidad tiene un `team`. Un proyectil solo daña a personajes de otro equipo, y la colisión se resuelve con rectángulos (`colliderect`).
- **Orden de dibujado.** Las entidades se dibujan ordenadas por la base de su rectángulo (`rect.bottom`), de modo que las que están más abajo en pantalla se pintan encima.
- **Depuración.** `F3` dibuja el contorno y el centro de cada entidad.

## Estilo de programación

- **Resolución interna escalada.** Todo se dibuja en un lienzo de 600 × 360 que se escala ×2 sin suavizado (*nearest neighbor*) para conservar el aspecto pixel art. Las posiciones del ratón se convierten de ventana a lienzo con `screen_to_world`. Cambiando `BASE_SIZE` o `SCALE` el resto se ajusta solo.
- **Datos fuera del código.** Los sprites y los parámetros se cargan automáticamente recorriendo `sprites/` y se guardan en los diccionarios `sprites` y `params`. Añadir o ajustar un personaje o ataque es editar archivos.
- **Jerarquía de clases por responsabilidades.**
  - `Entity`: algo que existe en el mapa (posición, sprite, rectángulo, `draw`, `update`).
  - `Character`: una `Entity` con estadísticas y capacidades (`attack`, `move_dir`, `run`, `take_damage`). No sabe nada de teclas ni de ratón.
  - `Player`: un `Character` controlado por el jugador. Solo traduce entradas en llamadas a las capacidades de `Character`.
  - `Projectile`: una `Entity` con ángulo, velocidad y daño. Se rota una sola vez al crearla, no en cada frame.
- **Tablas de asociación (*bindings*).** Las entradas del jugador se asignan a acciones mediante diccionarios con clave `(botón, modificadores)` y funciones `lambda` como valor, en lugar de cadenas de `if`.
- **Ataques como funciones registradas.** Cada ataque es una función `(attacker, entities, target_pos)` guardada en el diccionario `attacks`. El personaje elige el suyo con el campo `attack` de su `.txt`.
- **Separación de entrada continua y discreta.** Los eventos puntuales (clics) pasan por `handle_event`; el movimiento y correr se leen cada frame en `handle_held`.
- **Bucle principal con `dt`.** Cada iteración sigue el mismo orden: eventos → entrada continua → actualización → colisiones → eliminación de entidades muertas → dibujado. El tiempo entre frames (`dt`) se calcula con `clock.tick(60)`.

---

## Solución de problemas

| Problema | Causa probable |
|----------|----------------|
| `FileNotFoundError: sprites/Map_small.png` | Ejecutas el script desde otra carpeta, o falta `sprites/`. |
| `KeyError: 'gandalf_down.png'` | Falta un sprite o está mal nombrado (se distinguen mayúsculas y minúsculas). |
| `KeyError: 'speed'` (u otra clave) | Falta esa línea en el `.txt` del personaje o del ataque. |
| `ModuleNotFoundError: pygame` | Instala las dependencias con `pip install pygame numpy`. |

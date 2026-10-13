<!-- Task T3: Implement the complete Top-Down Car Racing game in Python using the turtle module based on the specifications. -->

```python
import math
import time
import turtle

# ==========================================
# CONSTANTS & CONFIGURATION
# ==========================================
WINDOW_WIDTH = 900
WINDOW_HEIGHT = 700
FPS = 60
FRAME_TIME = int(1000 / FPS)  # ~16ms

# Physics Constants
MAX_SPEED = 7.0
REVERSE_SPEED = -2.5
ACCELERATION = 0.2
BRAKE_DECEL = 0.4
FRICTION = 0.96          # Natural deceleration when neutral
OFFROAD_FRICTION = 0.85  # Heavy drag on grass
TURN_RATE = 4.5          # Degrees per frame

# Colors
COLOR_GRASS = "#2e8b57"  # Sea Green
COLOR_TRACK = "#404040"  # Asphalt Grey
COLOR_CURB = "#ffffff"   # White
COLOR_WALL = "#8b0000"   # Dark Red (Inner Island)

# ==========================================
# GAME STATE MACHINE & CONTROLS
# ==========================================
game_state = "START"  # START, COUNTDOWN, RACING, PAUSED, GAME_OVER

# Input State Flags
keys = {
    "up": False,
    "down": False,
    "left": False,
    "right": False
}

def set_key(key, state):
    if key in keys:
        keys[key] = state

# ==========================================
# INITIALIZE SCREEN & TURTLES
# ==========================================
screen = turtle.Screen()
screen.setup(WINDOW_WIDTH, WINDOW_HEIGHT)
screen.title("Top-Down Car Racing - Arcade Edition")
screen.bgcolor(COLOR_GRASS)
screen.tracer(0)  # Manual screen updates for optimal 60 FPS performance

# Dedicated turtles for drawing and HUD to prevent clutter
drawer = turtle.Turtle()
drawer.hideturtle()
drawer.penup()

hud_turtle = turtle.Turtle()
hud_turtle.hideturtle()
hud_turtle.penup()

# Player Car Setup (Vector-based triangle for high-performance rotation)
car = turtle.Turtle()
car.shape("triangle")
car.color("red")
car.shapesize(stretch_wid=0.8, stretch_len=1.6)  # Width, Length proportions
car.penup()

# ==========================================
# TRACK & CHECKPOINT GEOMETRY
# ==========================================
# The track is an oval circuit defined by an outer boundary and an inner barrier island.
# Center of track: (0, 0), Outer radii: Rx=420, Ry=310, Inner radii: Rx=240, Ry=150
OUTER_RX, OUTER_RY = 400, 290
INNER_RX, INNER_RY = 200, 110

# Checkpoints for lap validation (ordered sequence across the track)
# Each checkpoint is defined by a center (x, y) and a threshold radius.
CHECKPOINTS = [
    {"pos": (0, 245), "radius": 70, "id": 1},    # Top straight
    {"pos": (300, 0), "radius": 70, "id": 2},    # Right curve
    {"pos": (0, -245), "radius": 70, "id": 3},   # Bottom straight
    {"pos": (-300, 0), "radius": 70, "id": 4},   # Left curve / Finish line approach
]

# Game Variables
car_x = -300.0
car_y = 0.0
car_angle = 0.0      # Degrees
car_speed = 0.0      # Scalar velocity
current_checkpoint = 0
lap_count = 0
total_laps = 3
start_time = 0.0
elapsed_time = 0.0
countdown_value = 3
countdown_timer = 0

def reset_game():
    global car_x, car_y, car_angle, car_speed, current_checkpoint, lap_count, start_time, elapsed_time
    car_x = -300.0
    car_y = 0.0
    car_angle = 0.0
    car_speed = 0.0
    current_checkpoint = 0
    lap_count = 0
    start_time = time.time()
    elapsed_time = 0.0

# ==========================================
# DRAWING ENVIRONMENT
# ==========================================
def draw_track():
    drawer.clear()
    
    # 1. Draw Outer Track Boundary (Asphalt)
    drawer.goto(0, -OUTER_RY - 20)
    drawer.pendown()
    drawer.color(COLOR_CURB)
    drawer.begin_fill()
    # Draw oval using parametric approximation
    for i in range(361):
        rad = math.radians(i)
        x = (OUTER_RX + 20) * math.cos(rad)
        y = (OUTER_RY + 20) * math.sin(rad)
        drawer.goto(x, y)
    drawer.end_fill()

    drawer.penup()
    drawer.goto(0, -OUTER_RY)
    drawer.pendown()
    drawer.color(COLOR_TRACK)
    drawer.begin_fill()
    for i in range(361):
        rad = math.radians(i)
        x = OUTER_RX * math.cos(rad)
        y = OUTER_RY * math.sin(rad)
        drawer.goto(x, y)
    drawer.end_fill()

    # 2. Draw Inner Grass Island (Blocks out the center of the oval track)
    drawer.penup()
    drawer.goto(0, -INNER_RY)
    drawer.pendown()
    drawer.color(COLOR_GRASS)
    drawer.begin_fill()
    for i in range(361):
        rad = math.radians(i)
        x = INNER_RX * math.cos(rad)
        y = INNER_RY * math.sin(rad)
        drawer.goto(x, y)
    drawer.end_fill()

    # 3. Draw Inner Island Border Wall
    drawer.penup()
    drawer.goto(0, -INNER_RY)
    drawer.pendown()
    drawer.color(COLOR_WALL)
    drawer.pensize(4)
    for i in range(361):
        rad = math.radians(i)
        x = INNER_RX * math.cos(rad)
        y = INNER_RY * math.sin(rad)
        drawer.goto(x, y)
    drawer.penup()
    drawer.pensize(1)

    # 4. Draw Start/Finish Line
    drawer.goto(-300, -OUTER_RY)
    drawer.setheading(90)
    drawer.pendown()
    drawer.color("white")
    drawer.pensize(6)
    drawer.forward(OUTER_RY - INNER_RY)
    drawer.penup()
    drawer.pensize(1)

draw_track()

# ==========================================
# PHYSICS & COLLISION LOGIC
# ==========================================
def update_physics():
    global car_x, car_y, car_angle, car_speed, current_checkpoint, lap_count, game_state, elapsed_time

    # Determine surface friction based on position
    # Ellipse equation: (x/R_x)^2 + (y/R_y)^2 <= 1
    outer_check = (car_x / OUTER_RX)**2 + (car_y / OUTER_RY)**2
    inner_check = (car_x / INNER_RX)**2 + (car_y / INNER_RY)**2

    on_track = (outer_check <= 1.0) and (inner_check >= 1.0)
    current_friction = FRICTION if on_track else OFFROAD_FRICTION
    max_spd = MAX_SPEED if on_track else (MAX_SPEED * 0.4)  # Severe penalty off-road

    # 1. Acceleration and Deceleration Input
    if keys["up"]:
        car_speed = min(car_speed + ACCELERATION, max_spd)
    elif keys["down"]:
        if car_speed > 0:
            car_speed = max(car_speed - BRAKE_DECEL, 0)
        else:
            car_speed = max(car_speed - ACCELERATION, REVERSE_SPEED)
    else:
        # Apply natural drag / friction
        car_speed *= current_friction
        if abs(car_speed) < 0.05:
            car_speed = 0.0

    # 2. Steering Input (Only active when moving)
    if abs(car_speed) > 0.2:
        turn_multiplier = car_speed / MAX_SPEED  # Steer response scales with speed
        if keys["left"]:
            car_angle = (car_angle + TURN_RATE * turn_multiplier) % 360
        if keys["right"]:
            car_angle = (car_angle - TURN_RATE * turn_multiplier) % 360

    # 3. Positional Translation (Polar to Cartesian)
    rad = math.radians(car_angle)
    dx = car_speed * math.cos(rad)
    dy = car_speed * math.sin(rad)

    next_x = car_x + dx
    next_y = car_y + dy

    # 4. Boundary Collisions (Walls & Track Edge bounce)
    next_outer = (next_x / OUTER_RX)**2 + (next_y / OUTER_RY)**2
    next_inner = (next_x / INNER_RX)**2 + (next_y / INNER_RY)**2

    if next_outer > 1.0 or next_inner < 1.0:
        # Bounce / Reflect back and penalize speed
        car_speed *= -0.4
    else:
        car_x = next_x
        car_y = next_y

    # Update Car Turtle Transform
    car.goto(car_x, car_y)
    car.setheading(car_angle)

    # 5. Checkpoint & Lap Tracking
    cp = CHECKPOINTS[current_checkpoint]
    dist_to_cp = math.hypot(car_x - cp["pos"][0], car_y - cp["pos"][1])
    if dist_to_cp < cp["radius"]:
        current_checkpoint = (current_checkpoint + 1) % len(CHECKPOINTS)
        if current_checkpoint == 0:
            lap_count += 1
            if lap_count >= total_laps:
                game_state = "GAME_OVER"

    # Update Game Timer
    if game_state == "RACING":
        elapsed_time = time.time() - start_time

# ==========================================
# HUD & SCREEN RENDERING
# ==========================================
def draw_hud():
    hud_turtle.clear()
    
    if game_state == "START":
        hud_turtle.goto(0, 50)
        hud_turtle.color("yellow")
        hud_turtle.write("TOP-DOWN CAR RACING", align="center", font=("Arial", 28, "bold"))
        hud_turtle.goto(0, -10)
        hud_turtle.color("white")
        hud_turtle.write("Use ARROW KEYS to drive.", align="center", font=("Arial", 16, "normal"))
        hud_turtle.goto(0, -50)
        hud_turtle.write("Press [SPACEBAR] to Start Race", align="center", font=("Arial", 16, "bold"))
        hud_turtle.goto(0, -100)
        hud_turtle.write("Press [P] to Pause during gameplay", align="center", font=("Arial", 12, "italic"))

    elif game_state == "COUNTDOWN":
        hud_turtle.goto(0, 0)
        hud_turtle.color("cyan")
        txt = str(countdown_value) if countdown_value > 0 else "GO!"
        hud_turtle.write(txt, align="center", font=("Arial", 48, "bold"))

    elif game_state == "RACING" or game_state == "PAUSED":
        # Speedometer & Stats HUD at top
        hud_turtle.goto(-WINDOW_WIDTH // 2 + 30, WINDOW_HEIGHT // 2 - 40)
        hud_turtle.color("white")
        speed_kmh = int(abs(car_speed) * 25)
        hud_turtle.write(f"Speed: {speed_kmh} KM/H", align="left", font=("Arial", 14, "bold"))

        hud_turtle.goto(0, WINDOW_HEIGHT // 2 - 40)
        hud_turtle.write(f"Lap: {min(lap_count + 1, total_laps)} / {total_laps}", align="center", font=("Arial", 14, "bold"))

        hud_turtle.goto(WINDOW_WIDTH // 2 - 30, WINDOW_HEIGHT // 2 - 40)
        hud_turtle.write(f"Time: {elapsed_time:.2f}s", align="right", font=("Arial", 14, "bold"))

        if game_state == "PAUSED":
            hud_turtle.goto(0, 0)
            hud_turtle.color("yellow")
            hud_turtle.write("GAME PAUSED\nPress [P] to Resume", align="center", font=("Arial", 24, "bold"))

    elif game_state == "GAME_OVER":
        hud_turtle.goto(0, 60)
        hud_turtle.color("lime")
        hud_turtle.write("RACE FINISHED!", align="center", font=("Arial", 32, "bold"))
        hud_turtle.goto(0, 0)
        hud_turtle.color("white")
        hud_turtle.write(f"Total Time: {elapsed_time:.2f} seconds", align="center", font=("Arial", 18, "normal"))
        hud_turtle.goto(0, -50)
        hud_turtle.write("Press [R] to Restart or [ESC] to Quit", align="center", font=("Arial", 14, "bold"))

# ==========================================
# GAME FLOW & CONTROLLER TRIGGERS
# ==========================================
def start_countdown():
    global game_state, countdown_value, countdown_timer
    game_state = "COUNTDOWN"
    countdown_value = 3
    run_countdown_step()

def run_countdown_step():
    global countdown_value, game_state, start_time
    if game_state != "COUNTDOWN":
        return
    
    if countdown_value > 0:
        countdown_value -= 1
        screen.ontimer(run_countdown_step, 1000)
    else:
        game_state = "RACING"
        start_time = time.time()

def toggle_pause():
    global game_state
    if game_state == "RACING":
        game_state = "PAUSED"
    elif game_state == "PAUSED":
        game_state = "RACING"

def handle_spacebar():
    global game_state
    if game_state == "START":
        start_countdown()

def handle_restart():
    global game_state
    if game_state == "GAME_OVER":
        reset_game()
        start_countdown()

def handle_quit():
    screen.bye()

# ==========================================
# EVENT LISTENERS BINDING
# ==========================================
screen.listen()

# State-based arrow keys (Prevents OS key-repeat stuttering)
screen.onkeypress(lambda: set_key("up", True), "Up")
screen.onkeyrelease(lambda: set_key("up", False), "Up")
screen.onkeypress(lambda: set_key("down", True), "Down")
screen.onkeyrelease(lambda: set_key("down", False), "Down")
screen.onkeypress(lambda: set_key("left", True), "Left")
screen.onkeyrelease(lambda: set_key("left", False), "Left")
screen.onkeypress(lambda: set_key("right", True), "Right")
screen.onkeyrelease(lambda: set_key("right", False), "Right")

# WASD alternative mappings
screen.onkeypress(lambda: set_key("up", True), "w")
screen.onkeyrelease(lambda: set_key("up", False), "w")
screen.onkeypress(lambda: set_key("down", True), "s")
screen.onkeyrelease(lambda: set_key("down", False), "s")
screen.onkeypress(lambda: set_key("left", True), "a")
screen.onkeyrelease(lambda: set_key("left", False), "a")
screen.onkeypress(lambda: set_key("right", True), "d")
screen.onkeyrelease(lambda: set_key("right", False), "d")

# Game Flow Controls
screen.onkeypress(handle_spacebar, "space")
screen.onkeypress(toggle_pause, "p")
screen.onkeypress(handle_restart, "r")
screen.onkeypress(handle_quit, "Escape")

# ==========================================
# MAIN GAME LOOP (60 FPS TARGET)
# ==========================================
def game_loop():
    if game_state == "RACING":
        update_physics()
        car.showturtle()
    else:
        car.hideturtle()

    draw_hud()
    screen.update()
    
    # Tick loop every ~16ms for stable 60 FPS
    screen.ontimer(game_loop, FRAME_TIME)

# Initialize position and start loop
car.goto(car_x, car_y)
game_loop()
screen.mainloop()
```

### Usage Note
1. Ensure Python 3 is installed with standard `turtle` library support.
2. Run the script directly: `python <script_name>.py`.
3. **Controls:**
   - **Start Game:** Press `Spacebar`.
   - **Steer/Accelerate:** Use `Arrow Keys` or `W/A/S/D`.
   - **Pause/Resume:** Press `P`.
   - **Restart (after game over):** Press `R`.
   - **Quit:** Press `Escape`.

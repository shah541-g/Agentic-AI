import turtle
import math
import random

# --- Constants & Configuration ---
SCREEN_WIDTH = 600
SCREEN_HEIGHT = 600
GRAVITY = 0.15          # Adds a nice arc to projectiles
TURRET_POS = (0, -260)
TARGET_RADIUS = 20
PROJECTILE_RADIUS = 6

# --- Game State Variables ---
score = 0
lives = 3
ammo = 10
game_active = True

turret_angle = 45       # Initial launch angle in degrees
projectile_active = False
proj_x, proj_y = TURRET_POS
proj_vx, proj_vy = 0, 0

# --- Screen Setup ---
screen = turtle.Screen()
screen.setup(SCREEN_WIDTH, SCREEN_HEIGHT)
screen.bgcolor("#1a1a2e")
screen.title("Target Shooter Game")
screen.tracer(0)  # Turn off automatic updates for smooth manual frame rendering

# --- Turtles for Game Elements ---
# 1. HUD Writer Turtle
hud_turtle = turtle.Turtle()
hud_turtle.hideturtle()
hud_turtle.penup()
hud_turtle.color("white")

# 2. Turret/Cannon Turtle
turret = turtle.Turtle()
turret.hideturtle()
turret.penup()

# 3. Projectile Turtle
bullet = turtle.Turtle()
bullet.hideturtle()
bullet.penup()
bullet.shape("circle")
bullet.shapesize(PROJECTILE_RADIUS / 10)
bullet.color("#e94560")

# 4. Target Turtles (List of dictionaries for active targets)
targets = []

def create_target(x, y):
    """Creates a target turtle object with properties."""
    t = turtle.Turtle()
    t.hideturtle()
    t.penup()
    t.shape("circle")
    t.shapesize(TARGET_RADIUS / 10)
    t.color("#0f3460")
    t.goto(x, y)
    t.showturtle()
    return {"turtle": t, "x": x, "y": y, "dx": random.choice([-1.5, 1.5])}

def init_targets():
    """Spawns initial targets on the upper half of the screen."""
    global targets
    for t in targets:
        t["turtle"].clear()
        t["turtle"].hideturtle()
    targets = []
    
    # Spawn 4 targets at different X positions
    x_positions = [-180, -60, 60, 180]
    for x in x_positions:
        y = random.randint(120, 220)
        targets.append(create_target(x, y))

# --- Controls ---
def aim_left():
    global turret_angle
    if game_active:
        turret_angle = min(170, turret_angle + 5)

def aim_right():
    global turret_angle
    if game_active:
        turret_angle = max(10, turret_angle - 5)

def fire():
    global projectile_active, proj_x, proj_y, proj_vx, proj_vy, ammo
    if game_active and not projectile_active and ammo > 0:
        ammo -= 1
        projectile_active = True
        proj_x, proj_y = TURRET_POS
        
        # Convert angle to radians and calculate velocity components
        rad = math.radians(turret_angle)
        speed = 14
        proj_vx = speed * math.cos(rad)
        proj_vy = speed * math.sin(rad)
        bullet.goto(proj_x, proj_y)
        bullet.showturtle()

def restart_game():
    global score, lives, ammo, game_active, projectile_active
    score = 0
    lives = 3
    ammo = 10
    game_active = True
    projectile_active = False
    bullet.hideturtle()
    init_targets()

# Bind keyboard events
screen.listen()
screen.onkeypress(aim_left, "Left")
screen.onkeypress(aim_right, "Right")
screen.onkeypress(fire, "space")
screen.onkeypress(restart_game, "r")

# --- Drawing Functions ---
def draw_hud():
    hud_turtle.clear()
    # Top-left HUD: Score & Lives & Ammo
    hud_turtle.goto(-SCREEN_WIDTH//2 + 20, SCREEN_HEIGHT//2 - 40)
    hud_turtle.write(f"Score: {score}  Lives: {lives}  Ammo: {ammo}", font=("Arial", 14, "bold"))
    
    if not game_active:
        hud_turtle.goto(0, 0)
        if lives <= 0:
            hud_turtle.write("GAME OVER\nPress 'R' to Restart", align="center", font=("Arial", 22, "bold"))
        else:
            hud_turtle.write("YOU WIN!\nPress 'R' to Restart", align="center", font=("Arial", 22, "bold"))

def draw_turret():
    turret.clear()
    turret.goto(TURRET_POS)
    turret.setheading(turret_angle)
    
    # Draw cannon base
    turret.goto(TURRET_POS[0], TURRET_POS[1] - 10)
    turret.pendown()
    turret.color("#533483")
    turret.begin_fill()
    turret.circle(15)
    turret.end_fill()
    turret.penup()
    
    # Draw cannon barrel
    turret.goto(TURRET_POS)
    turret.pendown()
    turret.pensize(6)
    turret.color("#e94560")
    turret.forward(35)
    turret.pensize(1)
    turret.penup()

# --- Main Game Loop ---
def game_loop():
    global projectile_active, proj_x, proj_y, proj_vx, proj_vy, lives, game_active, ammo
    
    if game_active:
        # 1. Update Target Positions (oscillate horizontally)
        for t in targets:
            t["x"] += t["dx"]
            # Bounce off screen edges
            if t["x"] > SCREEN_WIDTH//2 - 40 or t["x"] < -SCREEN_WIDTH//2 + 40:
                t["dx"] *= -1
            t["turtle"].goto(t["x"], t["y"])
            
            # Draw a decorative inner ring for the target
            t["turtle"].color("#e94560" if (t["x"]//10)%2 == 0 else "#0f3460")

        # 2. Update Projectile Physics
        if projectile_active:
            proj_vx *= 0.99  # slight air resistance
            proj_vy -= GRAVITY  # apply gravity
            proj_x += proj_vx
            proj_y += proj_vy
            bullet.goto(proj_x, proj_y)
            
            # Collision Detection with Targets
            for t in targets[:]:
                # Euclidean distance check
                dist = math.hypot(proj_x - t["x"], proj_y - t["y"])
                if dist < (TARGET_RADIUS + PROJECTILE_RADIUS):
                    # HIT!
                    score += 10
                    projectile_active = False
                    bullet.hideturtle()
                    
                    # Remove and respawn target
                    t["turtle"].clear()
                    t["turtle"].hideturtle()
                    targets.remove(t)
                    
                    # Respawn new target higher up
                    new_x = random.randint(-200, 200)
                    new_y = random.randint(100, 240)
                    targets.append(create_target(new_x, new_y))
                    break

            # Miss Condition (OutOfBounds or hit ground)
            if proj_y < -SCREEN_HEIGHT//2 or abs(proj_x) > SCREEN_WIDTH//2:
                projectile_active = False
                bullet.hideturtle()
                lives -= 1

            # Check Game Over Conditions
            if lives <= 0 or (ammo <= 0 and not projectile_active and score < 40):
                if lives <= 0 or ammo <= 0:
                    game_active = False

        draw_turret()
        draw_hud()
        
    screen.update()
    screen.ontimer(game_loop, 20)  # Run ~50 FPS

# --- Initialize and Start ---
init_targets()
game_loop()
screen.mainloop()

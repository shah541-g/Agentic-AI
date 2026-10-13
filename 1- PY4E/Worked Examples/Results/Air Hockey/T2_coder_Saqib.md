<!-- Task T2: Write the complete Python code for the Air Hockey game using the turtle module, incorporating paddle controls for two players, puck movement with wall and paddle bouncing logic, goal scoring, and a score display. -->

```python
import turtle
import math
import time

# --- Game Window Setup ---
screen = turtle.Screen()
screen.title("Python Air Hockey")
screen.bgcolor("#1a1a2e")
screen.setup(width=800, height=600)
screen.tracer(0)  # Turn off automatic updates for smooth manual animation

# --- Draw Rink Markings ---
rink = turtle.Turtle()
rink.hideturtle()
rink.speed(0)
rink.color("#ffffff")
rink.pensize(3)

# Outer boundary
rink.penup()
rink.goto(-380, -280)
rink.pendown()
rink.goto(380, -280)
rink.goto(380, 280)
rink.goto(-380, 280)
rink.goto(-380, -280)

# Center line
rink.penup()
rink.goto(0, -280)
rink.setheading(90)
rink.pendown()
while rink.ycor() < 280:
    rink.forward(15)
    rink.penup()
    rink.forward(15)
    rink.pendown()

# Center circle
rink.penup()
rink.goto(0, -60)
rink.setheading(0)
rink.pendown()
rink.circle(60)

# Goal boxes (Left and Right)
goal_width = 140

# Left Goal
rink.penup()
rink.goto(-380, goal_width / 2)
rink.setheading(0)
rink.pendown()
rink.forward(30)
rink.right(90)
rink.forward(goal_width)
rink.right(90)
rink.forward(30)

# Right Goal
rink.penup()
rink.goto(380, goal_width / 2)
rink.setheading(180)
rink.pendown()
rink.forward(30)
rink.left(90)
rink.forward(goal_width)
rink.left(90)
rink.forward(30)

# --- Game Objects ---

# Scoreboard
score_a = 0
score_b = 0
scoreboard = turtle.Turtle()
scoreboard.hideturtle()
scoreboard.speed(0)
scoreboard.color("white")
scoreboard.penup()
scoreboard.goto(0, 240)
scoreboard.write("0   :   0", align="center", font=("Courier", 36, "bold"))

def update_scoreboard():
    scoreboard.clear()
    scoreboard.write(f"{score_a}   :   {score_b}", align="center", font=("Courier", 36, "bold"))

# Puck
puck = turtle.Turtle()
puck.shape("circle")
puck.color("#e94560")
puck.penup()
puck.speed(0)
puck.shapesize(stretch_wid=0.8, stretch_len=0.8) # Puck radius ~ 8px
puck.goto(0, 0)
puck.dx = 4.5
puck.dy = 4.5

# Paddle A (Left Player)
paddle_a = turtle.Turtle()
paddle_a.shape("circle")
paddle_a.color("#0f3460")
paddle_a.penup()
paddle_a.speed(0)
paddle_a.shapesize(stretch_wid=2, stretch_len=2) # Paddle radius ~ 20px
paddle_a.goto(-250, 0)

# Paddle B (Right Player)
paddle_b = turtle.Turtle()
paddle_b.shape("circle")
paddle_b.color("#0f3460")
paddle_b.penup()
paddle_b.speed(0)
paddle_b.shapesize(stretch_wid=2, stretch_len=2) # Paddle radius ~ 20px
paddle_b.goto(250, 0)

# --- Controls State Management (Smooth Movement) ---
keys_pressed = {
    "w": False, "s": False, "a": False, "d": False,
    "Up": False, "Down": False, "Left": False, "Right": False
}

def set_key(key, state):
    if key in keys_pressed:
        keys_pressed[key] = state

# Key bindings
screen.listen()
screen.onkeypress(lambda: set_key("w", True), "w")
screen.onkeyrelease(lambda: set_key("w", False), "w")
screen.onkeypress(lambda: set_key("s", True), "s")
screen.onkeyrelease(lambda: set_key("s", False), "s")
screen.onkeypress(lambda: set_key("a", True), "a")
screen.onkeyrelease(lambda: set_key("a", False), "a")
screen.onkeypress(lambda: set_key("d", True), "d")
screen.onkeyrelease(lambda: set_key("d", False), "d")

screen.onkeypress(lambda: set_key("Up", True), "Up")
screen.onkeyrelease(lambda: set_key("Up", False), "Up")
screen.onkeypress(lambda: set_key("Down", True), "Down")
screen.onkeyrelease(lambda: set_key("Down", False), "Down")
screen.onkeypress(lambda: set_key("Left", True), "Left")
screen.onkeyrelease(lambda: set_key("Left", False), "Left")
screen.onkeypress(lambda: set_key("Right", True), "Right")
screen.onkeyrelease(lambda: set_key("Right", False), "Right")

def move_paddles():
    speed = 6
    # Paddle A movement (Left side: x from -360 to -20)
    y_a = paddle_a.ycor()
    x_a = paddle_a.xcor()
    if keys_pressed["w"] and y_a < 260: paddle_a.sety(y_a + speed)
    if keys_pressed["s"] and y_a > -260: paddle_a.sety(y_a - speed)
    if keys_pressed["a"] and x_a > -360: paddle_a.setx(x_a - speed)
    if keys_pressed["d"] and x_a < -20: paddle_a.setx(x_a + speed)

    # Paddle B movement (Right side: x from 20 to 360)
    y_b = paddle_b.ycor()
    x_b = paddle_b.xcor()
    if keys_pressed["Up"] and y_b < 260: paddle_b.sety(y_b + speed)
    if keys_pressed["Down"] and y_b > -260: paddle_b.sety(y_b - speed)
    if keys_pressed["Left"] and x_b > 20: paddle_b.setx(x_b - speed)
    if keys_pressed["Right"] and x_b < 360: paddle_b.setx(x_b + speed)

# --- Main Game Loop ---
running = True

def reset_puck(scoring_player):
    global score_a, score_b
    puck.goto(0, 0)
    puck.dx *= -1
    puck.dy = 4.5 * (1 if scoring_player == "left" else -1)
    time.sleep(0.5)

while running:
    screen.update()
    move_paddles()

    # Move puck
    puck.setx(puck.xcor() + puck.dx)
    puck.sety(puck.ycor() + puck.dy)

    # --- Wall Collisions ---
    # Top & Bottom boundaries
    if puck.ycor() > 265:
        puck.sety(265)
        puck.dy *= -1
    elif puck.ycor() < -265:
        puck.sety(-265)
        puck.dy *= -1

    # Left & Right boundaries (checking for goals vs side-wall bounces)
    if puck.xcor() > 365:
        if -70 <= puck.ycor() <= 70:  # Goal condition for Player A
            score_a += 1
            update_scoreboard()
            reset_puck("right")
        else:
            puck.setx(365)
            puck.dx *= -1

    elif puck.xcor() < -365:
        if -70 <= puck.ycor() <= 70:  # Goal condition for Player B
            score_b += 1
            update_scoreboard()
            reset_puck("left")
        else:
            puck.setx(-365)
            puck.dx *= -1

    # --- Paddle Collisions ---
    # Distance threshold for collision (Puck radius 8 + Paddle radius 20 = 28)
    # Using squared distance to avoid sqrt performance overhead
    
    # Paddle A collision
    dist_a_sq = (puck.xcor() - paddle_a.xcor())**2 + (puck.ycor() - paddle_a.ycor())**2
    if dist_a_sq < 30**2:
        # Push puck outside the paddle to prevent sticking/glitching
        overlap = 30 - math.sqrt(dist_a_sq)
        puck.setx(puck.xcor() + overlap)
        
        # Calculate dynamic bounce angle based on relative hit position
        dx = puck.xcor() - paddle_a.xcor()
        dy = puck.ycor() - paddle_a.ycor()
        angle = math.atan2(dy, dx)
        speed_magnitude = math.hypot(puck.dx, puck.dy) * 1.05  # Slight energy boost on hit
        speed_magnitude = min(speed_magnitude, 12)  # Cap max speed
        
        puck.dx = speed_magnitude * math.cos(angle)
        puck.dy = speed_magnitude * math.sin(angle)

    # Paddle B collision
    dist_b_sq = (puck.xcor() - paddle_b.xcor())**2 + (puck.ycor() - paddle_b.ycor())**2
    if dist_b_sq < 30**2:
        # Push puck outside the paddle
        overlap = 30 - math.sqrt(dist_b_sq)
        puck.setx(puck.xcor() - overlap)
        
        dx = puck.xcor() - paddle_b.xcor()
        dy = puck.ycor() - paddle_b.ycor()
        angle = math.atan2(dy, dx)
        speed_magnitude = math.hypot(puck.dx, puck.dy) * 1.05
        speed_magnitude = min(speed_magnitude, 12)
        
        puck.dx = speed_magnitude * math.cos(angle)
        puck.dy = speed_magnitude * math.sin(angle)

    time.sleep(0.016)  # Cap loop frequency (~60 FPS)

turtle.done()
```

### Usage Note
1. Ensure Python is installed with access to the built-in `turtle` module.
2. Run the script using any standard Python interpreter (`python air_hockey.py`).
3. **Controls:**
   - **Player 1 (Left):** Use `W` (Up), `S` (Down), `A` (Left), `D` (Right). Confined to the left half of the rink.
   - **Player 2 (Right):** Use the **Arrow Keys** (`Up`, `Down`, `Left`, `Right`). Confined to the right half of the rink.
4. The game continuously tracks scores at the top center of the window. Hitting the puck into the opponent's net registers a point and resets the puck.

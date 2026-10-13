"""
Space Invaders Game using Python's Turtle Graphics Module
---------------------------------------------------------
A complete, runnable clone of Space Invaders built entirely using Python's
built-in standard library (turtle, math, random, time).
"""

import math
import random
import time
import turtle

# ==========================================
# CONSTANTS & CONFIGURATION
# ==========================================
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
PLAYER_Y = -240
ALIEN_ROWS = 4
ALIEN_COLS = 8
ALIEN_START_X = -280
ALIEN_START_Y = 200
ALIEN_SPACING_X = 75
ALIEN_SPACING_Y = 45

# ==========================================
# GAME STATE VARIABLES
# ==========================================
score = 0
lives = 3
game_over = False
game_won = False

# Movement flags for smooth continuous player movement
moving_left = False
moving_right = False

# ==========================================
# SCREEN SETUP
# ==========================================
screen = turtle.Screen()
screen.setup(width=SCREEN_WIDTH, height=SCREEN_HEIGHT)
screen.bgcolor("black")
screen.title("Space Invaders - Turtle Clone")
screen.tracer(0)  # Disable automatic screen updates for manual frame control

# ==========================================
# HUD / SCOREBOARD SETUP
# ==========================================
scoreboard = turtle.Turtle()
scoreboard.speed(0)
scoreboard.color("white")
scoreboard.penup()
scoreboard.hideturtle()
scoreboard.goto(0, SCREEN_HEIGHT // 2 - 40)


def update_scoreboard():
    scoreboard.clear()
    scoreboard.write(
        f"Score: {score}  |  Lives: {lives}",
        align="center",
        font=("Courier", 16, "bold"),
    )


update_scoreboard()

# ==========================================
# PLAYER SETUP
# ==========================================
player = turtle.Turtle()
player.speed(0)
player.shape("triangle")
player.color("green")
player.penup()
player.goto(0, PLAYER_Y)
player.setheading(90)  # Point upwards

# ==========================================
# PLAYER LASER SETUP
# ==========================================
laser = turtle.Turtle()
laser.speed(0)
laser.shape("square")
laser.color("yellow")
laser.shapesize(stretch_wid=0.2, stretch_len=1)  # Thin vertical laser beam
laser.penup()
laser.hideturtle()
laser_active = False
laser_speed = 15

# ==========================================
# ALIEN SWARM SETUP
# ==========================================
aliens = []
alien_direction = 2  # Positive = moving right, Negative = moving left
alien_speed = 1.5
alien_drop_distance = 20


def create_alien_swarm():
    global aliens
    for row in range(ALIEN_ROWS):
        for col in range(ALIEN_COLS):
            a = turtle.Turtle()
            a.speed(0)
            a.shape("invader" if "invader" in screen.getshapes() else "square")
            # Alternate colors per row for retro aesthetic
            colors = ["red", "orange", "yellow", "cyan"]
            a.color(colors[row % len(colors)])
            a.penup()
            x = ALIEN_START_X + (col * ALIEN_SPACING_X)
            y = ALIEN_START_Y - (row * ALIEN_SPACING_Y)
            a.goto(x, y)
            aliens.append(a)


create_alien_swarm()

# ==========================================
# INPUT FUNCTIONS & HANDLERS
# ==========================================


def start_move_left():
    global moving_left
    moving_left = True


def stop_move_left():
    global moving_left
    moving_left = False


def start_move_right():
    global moving_right
    moving_right = True


def stop_move_right():
    global moving_right
    moving_right = False


def fire_laser():
    global laser_active, game_over, game_won
    if game_over or game_won:
        return
    if not laser_active:
        laser.goto(player.xcor(), player.ycor() + 20)
        laser.showturtle()
        laser_active = True


# Keyboard Event Listeners
screen.listen()
screen.onkeypress(start_move_left, "Left")
screen.onkeyrelease(stop_move_left, "Left")
screen.onkeypress(start_move_right, "Right")
screen.onkeyrelease(stop_move_right, "Right")
screen.onkeypress(fire_laser, "space")

# Also support 'a' and 'd' for alternative controls
screen.onkeypress(start_move_left, "a")
screen.onkeyrelease(stop_move_left, "a")
screen.onkeypress(start_move_right, "d")
screen.onkeyrelease(stop_move_right, "d")

# ==========================================
# CORE GAME LOGIC LOOP
# ==========================================


def game_loop():
    global score, lives, game_over, game_won, laser_active, alien_direction, alien_speed

    if game_over or game_won:
        return

    # 1. Update Player Position based on continuous input flags
    x = player.xcor()
    if moving_left and x > -SCREEN_WIDTH // 2 + 30:
        player.setx(x - 6)
    if moving_right and x < SCREEN_WIDTH // 2 - 30:
        player.setx(x + 6)

    # 2. Update Laser Position
    if laser_active:
        y = laser.ycor() + laser_speed
        laser.sety(y)
        # Deactivate if it goes off the top of the screen
        if y > SCREEN_HEIGHT // 2:
            laser.hideturtle()
            laser_active = False

    # 3. Update Alien Swarm Position & Boundary Checks
    edge_reached = False
    for a in aliens:
        a.setx(a.xcor() + alien_direction)
        # Check if any active alien hits the left or right wall bounds
        if a.xcor() > SCREEN_WIDTH // 2 - 30 or a.xcor() < -SCREEN_WIDTH // 2 + 30:
            edge_reached = True

    if edge_reached:
        alien_direction *= -1  # Reverse horizontal direction
        for a in aliens:
            a.sety(a.ycor() - alien_drop_distance)  # Drop down

    # 4. Collision Detection: Laser vs Aliens
    if laser_active:
        for a in aliens[:]:  # Iterate over a copy of the list for safe removal
            if laser.distance(a) < 20:
                # Collision detected!
                laser.hideturtle()
                laser_active = False
                a.hideturtle()
                aliens.remove(a)
                score += 100
                update_scoreboard()

                # Slightly increase swarm speed as aliens are destroyed
                alien_speed = min(4.0, alien_speed + 0.05)
                break

    # 5. Collision Detection: Aliens vs Player or Bottom Boundary (Loss condition)
    for a in aliens:
        if a.distance(player) < 25 or a.ycor() <= PLAYER_Y + 10:
            game_over = True
            break

    # 6. Check Win/Loss End Game Conditions
    if game_over:
        laser.hideturtle()
        scoreboard.goto(0, 0)
        scoreboard.color("red")
        scoreboard.write(
            "GAME OVER\nPress 'R' to Restart",
            align="center",
            font=("Courier", 24, "bold"),
        )
        screen.update()
        return

    if not aliens:
        game_won = True
        laser.hideturtle()
        scoreboard.goto(0, 0)
        scoreboard.color("green")
        scoreboard.write(
            "VICTORY!\nPress 'R' to Restart",
            align="center",
            font=("Courier", 24, "bold"),
        )
        screen.update()
        return

    # Refresh screen and schedule next frame (approx. ~50 FPS)
    screen.update()
    screen.ontimer(game_loop, 20)


# ==========================================
# RESTART MECHANISM
# ==========================================


def restart_game():
    global score, lives, game_over, game_won, laser_active, aliens, alien_direction, alien_speed

    # Reset state variables
    score = 0
    lives = 3
    game_over = False
    game_won = False
    laser_active = False
    alien_direction = 2
    alien_speed = 1.5

    # Clear existing aliens from screen
    for a in aliens:
        a.hideturtle()
    aliens.clear()

    # Reset HUD text position and content
    scoreboard.color("white")
    scoreboard.goto(0, SCREEN_HEIGHT // 2 - 40)
    update_scoreboard()

    # Reset player position
    player.goto(0, PLAYER_Y)
    laser.hideturtle()

    # Recreate alien swarm and restart loop
    create_alien_swarm()
    game_loop()


screen.onkeypress(restart_game, "r")
screen.onkeypress(restart_game, "R")

# Initialize and start the game loop
game_loop()
screen.mainloop()

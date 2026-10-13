<!-- Task T3: Write documentation and setup instructions explaining how to run the Python turtle Flappy Bird game, including any prerequisites. -->

# Python Turtle Flappy Bird: Documentation & Setup Guide

Welcome to the documentation and setup instructions for the **Flappy Bird** clone built entirely using Python's built-in `turtle` graphics library! 

---

## 1. Prerequisites

Before running the game, ensure your environment meets the following requirements:

* **Python 3.x:** Make sure Python is installed on your system. You can verify this by running `python --version` (or `python3 --version`) in your terminal or command prompt.
* **Turtle Module:** The `turtle` module is a standard part of the Python Standard Library, meaning **no external packages or `pip install` commands are required**. 

---

## 2. Setup Instructions

Follow these simple steps to get the game up and running on your machine:

1. **Create the Script File:**
   Open your favorite code editor (such as VS Code, PyCharm, or IDLE) or a plain text editor. Create a new file and save it as `flappy_bird.py`.

2. **Paste the Game Code:**
   Copy the complete Python script provided below and paste it into your `flappy_bird.py` file:

   ```python
   import random
   import turtle

   # --- Setup Screen ---
   screen = turtle.Screen()
   screen.title("Flappy Bird in Turtle")
   screen.setup(width=400, height=600)
   screen.bgcolor("skyblue")
   screen.tracer(0, 0)  # CRITICAL: Disable auto-updates for performance

   # --- Constants & Variables ---
   GRAVITY = -0.5
   JUMP_STRENGTH = 9
   PIPE_SPEED = -3.5
   PIPE_GAP = 160
   SPAWN_INTERVAL = 100  # frames (~60 FPS target)

   bird_y = 0
   bird_v = 0
   score = 0
   high_score = 0
   pipes = []  # List to store pipe dicts: {'x': x_pos, 'gap_y': y_pos, 'passed': bool}

   # --- Initialize Bird ---
   bird = turtle.Turtle()
   bird.shape("square")
   bird.color("yellow")
   bird.shapesize(stretch_wid=1.2, stretch_len=1.2)  # ~24x24 pixels
   bird.penup()
   bird.goto(-100, 0)

   # --- Initialize Drawers (Optimized to avoid recreating turtles) ---
   pipe_drawer = turtle.Turtle()
   pipe_drawer.hideturtle()
   pipe_drawer.penup()
   pipe_drawer.color("forestgreen")
   pipe_drawer.shape("square")

   hud_drawer = turtle.Turtle()
   hud_drawer.hideturtle()
   hud_drawer.penup()
   hud_drawer.color("white")


   # --- Input Handling ---
   def jump(x=0, y=0):
       global bird_v, running, game_started
       if not game_started:
           game_started = True
       if running:
           bird_v = JUMP_STRENGTH
       else:
           reset_game()


   screen.listen()
   screen.onkeypress(jump, "space")
   screen.onclick(jump)  # Allows mouse clicks too


   # --- Game State Functions ---
   def spawn_pipe():
       gap_y = random.randint(-120, 120)
       pipes.append({"x": 220, "gap_y": gap_y, "passed": False})


   def reset_game():
       global bird_y, bird_v, score, pipes, running, game_started, frame_count
       bird_y = 0
       bird_v = 0
       score = 0
       pipes.clear()
       frame_count = 0
       running = True
       spawn_pipe()


   def check_collision(bx, by, pipes):
       # Floor and ceiling collision (Screen height is 600, bounds are -300 to 300)
       if by < -285 or by > 285:
           return True

       # Pipe collision (Bird radius approximation ~12px, pipe width ~50px -> half_width = 25)
       for p in pipes:
           px = p["x"]
           py = p["gap_y"]
           # Check horizontal bounds
           if px - 28 < bx < px + 28:
               # Check vertical bounds (outside the gap)
               if by < py - PIPE_GAP / 2 + 10 or by > py + PIPE_GAP / 2 - 10:
                   return True
       return False


   # --- Main Game Loop ---
   frame_count = 0
   running = True
   game_started = False

   spawn_pipe()


   def game_loop():
       global bird_y, bird_v, frame_count, running, score, high_score, game_started

       if running and game_started:
           # 1. Physics Update
           bird_v += GRAVITY
           bird_y += bird_v
           bird.sety(bird_y)

           # 2. Pipe Management
           frame_count += 1
           if frame_count >= SPAWN_INTERVAL:
               spawn_pipe()
               frame_count = 0

           # Move pipes and check score
           for p in pipes:
               p["x"] += PIPE_SPEED
               # Score check: if pipe passes the bird's x position (-100)
               if not p["passed"] and p["x"] < -100:
                   p["passed"] = True
                   score += 1
                   if score > high_score:
                       high_score = score

           # Remove off-screen pipes
           if pipes and pipes[0]["x"] < -230:
               pipes.pop(0)

           # 3. Collision Detection
           if check_collision(-100, bird_y, pipes):
               running = False

       # 4. Rendering Phase (Clear stamps instead of clearing screen to preserve performance)
       pipe_drawer.clear()

       # Draw Pipes
       for p in pipes:
           px = p["x"]
           py = p["gap_y"]

           # Top pipe (Screen top is +300)
           top_height = 300 - (py + PIPE_GAP / 2)
           pipe_drawer.goto(px, py + PIPE_GAP / 2 + top_height / 2)
           pipe_drawer.shapesize(
               stretch_wid=top_height / 20, stretch_len=2.5
           )  # turtle square base is 20x20
           pipe_drawer.stamp()

           # Bottom pipe (Screen bottom is -300)
           bottom_height = (py - PIPE_GAP / 2) - (-300)
           pipe_drawer.goto(px, py - PIPE_GAP / 2 - bottom_height / 2)
           pipe_drawer.shapesize(stretch_wid=bottom_height / 20, stretch_len=2.5)
           pipe_drawer.stamp()

       # Draw Bird
       bird.goto(-100, bird_y)

       # Draw HUD / Text UI
       hud_drawer.clear()
       if not game_started:
           hud_drawer.goto(0, 50)
           hud_drawer.write(
               "FLAPPY BIRD", align="center", font=("Arial", 28, "bold")
           )
           hud_drawer.goto(0, 0)
           hud_drawer.write(
               "Press SPACE or Click to Start",
               align="center",
               font=("Arial", 14, "normal"),
           )
       elif running:
           hud_drawer.goto(0, 250)
           hud_drawer.write(str(score), align="center", font=("Arial", 30, "bold"))
       else:
           hud_drawer.goto(0, 80)
           hud_drawer.write(
               "GAME OVER", align="center", font=("Arial", 28, "bold")
           )
           hud_drawer.goto(0, 30)
           hud_drawer.write(
               f"Score: {score}  |  High Score: {high_score}",
               align="center",
               font=("Arial", 14, "normal"),
           )
           hud_drawer.goto(0, -20)
           hud_drawer.write(
               "Press SPACE or Click to Restart",
               align="center",
               font=("Arial", 12, "normal"),
           )

       screen.update()  # Refresh frame manually

       # Loop next frame (~60 FPS = ~16ms)
       screen.ontimer(game_loop, 16)


   # Start the game tick sequence
   game_loop()
   screen.mainloop()
   ```

3. **Run the Game:**
   Open your terminal or command prompt, navigate to the directory where you saved `flappy_bird.py`, and execute the following command:
   ```bash
   python flappy_bird.py
   ```
   *(Note: On some operating systems, you may need to use `python3 flappy_bird.py` instead).*

---

## 3. Game Controls

* **Jump / Start / Restart:** Press the **Spacebar** on your keyboard or **Left-Click** anywhere on the game window with your mouse.

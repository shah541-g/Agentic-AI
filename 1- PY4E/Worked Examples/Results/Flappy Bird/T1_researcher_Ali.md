<!-- Task T1: Research the core mechanics of Flappy Bird (gravity, jump velocity, pipe generation, collision detection) and how to implement them efficiently using Python's turtle graphics module. -->

### 1. Core Mechanics Analysis

#### **Gravity & Physics**
*   **Mechanics:** The bird is constantly acted upon by a downward acceleration (gravity). When the player inputs a command, an instantaneous upward velocity (jump velocity) is applied, overriding the current vertical speed.
*   **Mathematical Model:** 
    *   $y_{new} = y_{old} + v_y$
    *   $v_{y,new} = v_{y,old} + g$ (where $g$ is negative acceleration).
    *   $v_{y,jump} = +J$ (where $J$ is the positive initial jump velocity).
*   **Terminal Velocity:** To prevent the bird from accelerating infinitely and breaking the physics bounds, a maximum downward velocity ($v_{max\_down}$) should be enforced.

#### **Pipe Generation & Movement**
*   **Mechanics:** Pipes spawn off-screen to the right at fixed horizontal intervals and move leftward at a constant speed to simulate forward motion.
*   **Structure:** Each pipe obstacle consists of a top pipe and a bottom pipe with a fixed vertical "gap" between them for the bird to pass through.
*   **Randomization:** The vertical position of the gap should be randomized within predefined safe boundaries to ensure all generated pipes are passable.
*   **Recycling/Pooling:** For efficiency, instead of destroying off-screen pipes and creating new ones, pipe pairs should be recycled: once a pipe pair moves past the left boundary of the screen, it is repositioned to the far right with a new random gap height.

#### **Collision Detection**
*   **Mechanics:** The game must continuously check if the bird intersects with any solid surface (ground, ceiling, or any part of the top and bottom pipes).
*   **Bounding Box (AABB) Approach:** Treat the bird and the pipes as rectangular bounding boxes. A collision occurs if the horizontal and vertical intervals of the bird overlap with the intervals of a pipe.
    *   *Bird Box:* $[x_{bird} - w/2, x_{bird} + w/2]$ and $[y_{bird} - h/2, y_{bird} + h/2]$
    *   *Pipe Box:* $[x_{pipe}, x_{pipe} + w_{pipe}]$ and $[y_{pipe\_bottom}, y_{pipe\_top}]$
*   **Circle Approximation (Alternative):** Treat the bird as a circle with radius $r$ and center $(x, y)$, which often feels more forgiving and natural to players than a square bounding box.

---

### 2. Efficient Implementation Using Python's `turtle` Module

Python's `turtle` module is traditionally slow because every movement triggers a window refresh and vector drawing calculation. To implement Flappy Bird efficiently, specific optimizations are required.

#### **Performance Optimizations**
1.  **Screen Updates (`tracer(0, 0)` & `update()`):** 
    Disable automatic screen updates entirely. Use `turtle.tracer(0, 0)` at initialization and manually call `turtle.update()` at the end of every single game loop frame. This shifts rendering from real-time drawing to frame-based batch rendering.
2.  **Shape Caching (`register_shape` / `ht()`):** 
    Do not draw complex shapes dynamically using turtle pen strokes. Use simple built-in shapes (`"square"`, `"circle"`) scaled via `shapesize()`, or register custom bitmaps/polygons once. Hide unnecessary turtle pointers using `hideturtle()`.
3.  **Stamp vs. Turtle Instances:** 
    *   For the bird, a single turtle instance is acceptable since its state changes frequently.
    *   For pipes, creating multiple turtle objects introduces severe overhead. Instead, use **turtle stamping** (`clone()` or a single turtle using `stamp()` and `clearstamps()`), or draw simple geometric blocks using filled polygons with minimal state changes.

#### **Architecture & Game Loop Structure**
Because `turtle` lacks a native high-performance delta-time game loop, use `screen.ontimer()` to create a fixed-framerate loop (e.g., ~30 to 60 FPS, roughly 16ms to 33ms per tick).

#### **Draft Code Blueprint**

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
GRAVITY = -0.6
JUMP_STRENGTH = 10
PIPE_SPEED = -4
PIPE_GAP = 150
SPAWN_INTERVAL = 90  # frames

bird_y = 0
bird_v = 0

pipes = []  # List to store pipe dicts: {'x': x_pos, 'gap_y': y_pos}


# --- Initialize Bird ---
bird = turtle.Turtle()
bird.shape("square")
bird.color("yellow")
bird.shapesize(stretch_wid=1.5, stretch_len=1.5)  # 30x30 pixels roughly
bird.penup()
bird.goto(-100, 0)


# --- Input Handling ---
def jump(x=0, y=0):  # Accepts arguments to work with screen.onclick/listen
    global bird_v
    bird_v = JUMP_STRENGTH


screen.listen()
screen.onkeypress(jump, "space")
screen.onclick(jump)  # Allows mouse clicks too


# --- Helper Functions ---
def spawn_pipe():
    gap_y = random.randint(-150, 150)
    pipes.append({"x": 220, "gap_y": gap_y})


def check_collision(bx, by, pipes):
    # Floor and ceiling collision
    if by < -280 or by > 280:
        return True

    # Pipe collision (assuming bird radius ~15px)
    for p in pipes:
        px = p["x"]
        py = p["gap_y"]
        # Check if bird is horizontally aligned with the pipe width (approx 60px wide)
        if px - 30 < bx < px + 30:
            # Check if bird is outside the vertical gap
            if by < py - PIPE_GAP / 2 or by > py + PIPE_GAP / 2:
                return True
    return False


# --- Main Game Loop ---
frame_count = 0
running = True


def game_loop():
    global bird_y, bird_v, frame_count, running

    if not running:
        return

    # 1. Physics Update
    bird_v += GRAVITY
    bird_y += bird_v
    bird.sety(bird_y)

    # 2. Pipe Management
    frame_count += 1
    if frame_count >= SPAWN_INTERVAL:
        spawn_pipe()
        frame_count = 0

    # Move pipes
    for p in pipes:
        p["x"] += PIPE_SPEED

    # Remove off-screen pipes
    if pipes and pipes[0]["x"] < -220:
        pipes.pop(0)

    # 3. Collision Detection
    if check_collision(-100, bird_y, pipes):
        running = False
        # Handle game over state here (omitted for brevity)
        return

    # 4. Rendering (Using Turtle Stamps or Clearing/Redrawing)
    screen.clear()  # Note: screen.clear wipes everything including event bindings in some versions.
    # Alternatively, use dedicated drawing turtles to clear stamps instead of screen.clear().
    # For a basic prototype, we redraw the screen state:
    screen.bgcolor("skyblue")

    # Draw Bird
    bird.goto(-100, bird_y)
    bird.stamp()

    # Draw Pipes
    pipe_drawer = turtle.Turtle()
    pipe_drawer.hideturtle()
    pipe_drawer.penup()
    pipe_drawer.color("green")

    for p in pipes:
        px = p["x"]
        py = p["gap_y"]

        # Top pipe
        pipe_drawer.goto(px, py + PIPE_GAP / 2)
        pipe_drawer.shape("square")
        pipe_drawer.shapesize(
            stretch_wid=25, stretch_len=3
        )  # Adjust dimensions as needed
        pipe_drawer.stamp()

        # Bottom pipe
        pipe_drawer.goto(px, py - PIPE_GAP / 2)
        pipe_drawer.shape("square")
        pipe_drawer.shapesize(stretch_wid=25, stretch_len=3)
        pipe_drawer.stamp()

    screen.update()  # Refresh frame

    # Loop next frame (~30 FPS = ~33ms)
    screen.ontimer(game_loop, 33)


# Start the game
spawn_pipe()
game_loop()
screen.mainloop()
```

---

### 3. Uncertainties & Limitations

*   **Turtle Rendering Limitations:** While `screen.update()` and `ontimer()` allow for pseudo-real-time loops, Python's `turtle` is fundamentally unoptimized for real-time arcade games. At higher speeds or with many rendered objects, frame stuttering (*lag*) may occur because `turtle` recalculates window geometry on redraws.
*   **`screen.clear()` Side Effects:** Using `screen.clear()` inside the loop to clear old frames wipes out registered click/keypress bindings in certain Python environments. **Correction/Alternative:** It is computationally more efficient and safer to manage a persistent set of "stamp turtles" or clear specific stamps (`clearstamps()`) rather than clearing the entire screen canvas every frame.

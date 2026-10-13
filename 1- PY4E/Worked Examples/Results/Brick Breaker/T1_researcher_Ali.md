<!-- Task T1: Research the basic game mechanics, required classes, and Pygame/Turtle architecture needed for a Brick Breaker game in Python using the turtle module. -->

### 1. Basic Game Mechanics
Brick Breaker (derived from arcade games like *Breakout* and *Arkanoid*) relies on a continuous 2D collision-detection and physics loop.

*   **The Paddle:** Controlled horizontally by the player (using keyboard arrows or mouse movement). It is restricted to the bottom of the screen.
*   **The Ball:** Moves continuously at a set velocity vector $(v_x, v_y)$. It bounces off walls, the paddle, and bricks. If it falls below the bottom boundary, the player loses a life.
*   **The Bricks:** Arranged in a grid at the top of the screen. When the ball intersects a brick's bounding box, the brick is destroyed, and the ball's vertical velocity is inverted ($v_y = -v_y$).
*   **Scoring & Win/Loss Conditions:** 
    *   Score increases per brick destroyed.
    *   Loss condition: Player runs out of lives (ball hits the bottom floor).
    *   Win condition: All bricks are cleared from the grid.

### 2. Required Classes
To maintain clean architecture in a procedural environment like Python's `turtle` module, object-oriented programming (OOP) is strongly recommended. The game requires four core classes:

*   **`Paddle` Class:**
    *   *Attributes:* `turtle.Turtle` instance, width, height, screen boundaries.
    *   *Methods:* `move_left()`, `move_right()`, `update_position()`.
*   **`Ball` Class:**
    *   *Attributes:* `turtle.Turtle` instance, $x$ velocity (`dx`), $y$ velocity (`dy`), speed multiplier.
    *   *Methods:* `move()`, `bounce_x()`, `bounce_y()`, `reset_position()`.
*   **`Brick` (or `BrickManager`) Class:**
    *   *Attributes:* List/matrix of brick objects, color, dimensions, status (active/destroyed).
    *   *Methods:* `create_grid()`, `check_collision(ball)`.
*   **`GameManager` (or `Scoreboard`) Class:**
    *   *Attributes:* Lives remaining, current score, game state (running, paused, game over).
    *   *Methods:* `update_score()`, `lose_life()`, `display_message()`.

### 3. Pygame vs. Turtle Architecture
*Note: The prompt mentions both Pygame and Turtle. Below is the architectural breakdown specifically for implementing this game using the **Python `turtle` module** (as requested by the primary constraint), contrasted briefly with Pygame for structural context.*

#### Turtle Architecture (`turtle` module):
*   **Screen Setup:** Uses `turtle.Screen()` configured with fixed dimensions (e.g., 600x800 pixels) and `tracer(0)` to disable auto-updates for manual frame-rate control (double buffering).
*   **Main Game Loop:** Instead of Pygame's `while True` loop with `pygame.event.get()`, Turtle relies on a custom `update()` function called recursively via `screen.ontimer()` or driven by a `while` loop combined with `screen.update()`.
*   **Input Handling:** Uses event listeners (`screen.listen()`, `screen.onkeypress(paddle.move_left, "Left")`) rather than polling `pygame.key.get_pressed()`.
*   **Rendering:** Every entity is a `turtle.Turtle()` instance shaped as a square or rectangle (`shapesize`), stamped or moved across the canvas. `screen.update()` must be called explicitly at the end of every frame.

#### Pygame Architecture (Contextual Contrast - *Unsure if needed, but included for completeness*):
*   Pygame uses a `pygame.Surface` display, a strict `pygame.time.Clock().tick(FPS)` loop, surface blitting for rendering, and pixel-or-rect-based `pygame.Rect.colliderect()` for physics. 

### 4. Areas of Uncertainty & Limitations in Turtle
*   **Performance (FPS):** The `turtle` module is built on top of Tkinter and is notoriously slow. Rendering a high number of individual brick turtles simultaneously will cause significant input lag and low frame rates. *Mitigation:* Using `turtle.stamp()` instead of multiple distinct turtle objects for the bricks can improve performance, though collision detection becomes more mathematically manual.
*   **Collision Precision:** Turtle's native distance-based collision (`distance()`) is radial (circular), whereas a Brick Breaker game requires axis-aligned bounding box (AABB) collision to accurately determine whether the ball hit the top/bottom vs. the side of a brick or paddle. Implementing accurate AABB physics manually in Turtle requires writing custom bounding-box math.

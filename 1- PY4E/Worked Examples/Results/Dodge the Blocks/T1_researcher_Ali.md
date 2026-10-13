<!-- Task T1: Research the core game mechanics, control setup, and architecture for a Python Turtle 'Dodge the Blocks' game. -->

### 1. Core Game Mechanics

*   **Player Character (The Dodger):** 
    *   Represented by a custom turtle shape, polygon, or basic geometry.
    *   Moves horizontally (or freely, depending on design) along the lower bound of the screen to avoid falling obstacles.
    *   Maintains a constant $Y$ coordinate while its $X$ coordinate responds to user input.
*   **Obstacles (The Blocks):** 
    *   Spawn continuously or in waves at the top of the screen ($Y = \text{max\_height}$).
    *   Fall vertically down the screen by decreasing their $Y$ coordinate at a fixed or progressively increasing speed per frame.
    *   Reset to the top at randomized $X$ coordinates once they pass the bottom boundary of the screen, or are deleted and re-instantiated to manage memory.
*   **Collision Detection:** 
    *   Calculated continuously in the main game loop.
    *   Typically implemented using bounding-box collision (comparing the distance between the player and each block using `turtle.distance()`) or coordinate boundary checks (checking if the player's $[x, y]$ falls within the width/height of a block).
    *   Triggers a "Game Over" state upon intersection.
*   **Scoring System:** 
    *   Increments based on survival time (frames survived) or successful dodges (blocks cleared past the player's $Y$ threshold).
    *   Rendered dynamically on screen using Python Turtle's `turtle.write()` method.
*   **Game Loop & State Management:** 
    *   Driven by a continuous loop governed by `turtle.ontimer()` or manual frame updates via `screen.update()`.
    *   States include: `START`, `PLAYING`, and `GAME_OVER`.

### 2. Control Setup

*   **Event Handling:** 
    *   Utilizes Turtle's `screen.listen()` combined with `screen.onkey()` or `screen.onkeypress()` to capture keyboard input asynchronously.
*   **Default Key Bindings:**
    *   Left Arrow / `A` key: Moves the player left (decrements $X$).
    *   Right Arrow / `D` key: Moves the player right (increments $X$).
    *   Spacebar: Restarts the game upon reaching the "Game Over" state.
*   **Movement Implementation:**
    *   *Direct Coordinate Update:* Setting `player.setx(player.xcor() - step_size)` inside event-bound functions for snappy response.
    *   *Flag-based Movement (Smooth Handling):* Setting a movement direction flag (`is_moving_left = True`) on keypress and clearing it on key-release (`onkeyrelease`) to prevent OS key-repeat stutter in the main loop. *(Note: Turtle's `onkeyrelease` support can be inconsistent across operating systems; developers are often unsure of its cross-platform reliability).*

### 3. Architecture

*   **Architectural Pattern:** Procedural-to-Object-Oriented hybrid. Organizing code into classes (e.g., `Player`, `BlockManager`, `Scoreboard`, `Game`) is heavily recommended to manage state cleanly in Python Turtle.
*   **Component Breakdown:**
    *   **Screen/Window Setup (`turtle.Screen`):** Initializes the canvas, dimensions, background color, and disables automatic screen updates (`screen.tracer(0)`) to implement manual double-buffering for smooth, flicker-free rendering.
    *   **Player Class:** Encapsulates player attributes (shape, color, speed, boundaries) and movement methods.
    *   **Block Class / Manager:** Handles block generation, randomized positioning, movement updates, and recycling/deletion logic.
    *   **Scoreboard Class:** Manages current score, high score tracking, and text rendering on the canvas.
*   **Execution Flow (The Main Loop):**
    1. Initialize window, register shapes, and instantiate game objects.
    2. Bind keyboard listeners.
    3. Enter the `game_loop()` function:
        *   Update player position.
        *   Move all active blocks downward.
        *   Check for collisions between player and blocks.
        *   Check for scoring conditions.
        *   Refresh the screen (`screen.update()`).
        *   Call `screen.ontimer(game_loop, delay_ms)` to schedule the next frame (typically targeting ~30 to 60 FPS, e.g., 16ms to 33ms delay).
    4. Upon collision, break the loop, display "Game Over", and prompt for a restart.

### Areas of Uncertainty

*   **Performance Bottlenecks:** It is unclear how Turtle handles more than 15–20 active shapes simultaneously without noticeable frame drops, as Turtle is a lightweight wrapper around Tkinter canvas and is not optimized for high-sprite-count real-time action games.
*   **Key-Release Reliability:** The cross-platform reliability of `screen.onkeyrelease()` in standard Python installations can be erratic, sometimes requiring workarounds to prevent player movement from sticking.

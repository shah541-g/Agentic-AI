<!-- Task T1: Research and outline the game mechanics, controls, and visual layout for a Python Turtle 'Target Shooter' game. -->

**Research Findings: Python Turtle 'Target Shooter' Game**

### 1. Visual Layout
*   **Window Dimensions:** Standard configuration typically uses a square or rectangular window (e.g., $600 \times 600$ pixels) set up via `turtle.Screen()`.
*   **Background:** Solid color (e.g., black or sky blue) to ensure high contrast for game elements. A `turtle.Turtle` instance is used as a static background stamper or `screen.bgcolor()` is called.
*   **The Player (Cannon/Turret):** Positioned at the bottom center of the screen $(0, -250)$. Represented by a simple geometric shape (rectangle or triangle) pointing upwards.
*   **The Projectile (Bullet/Cannonball):** Starts at the player's position and travels upward toward the targets upon firing.
*   **The Targets:** Spawn randomly along the upper half of the screen ($y$-coordinates between $100$ and $250$). Represented by colored circles or custom shapes.
*   **Heads-Up Display (HUD):** Text rendered via the `turtle.write()` method positioned at the top corners of the screen to track:
    *   Score (incremented on target hits).
    *   Lives or Ammo remaining (decremented on misses or shots fired).

### 2. Controls
*   **Aiming (Rotation):** 
    *   *Left/Right Arrow Keys:* Rotate the player turtle by a fixed angle (e.g., $\pm 5$ degrees) per keystroke to adjust the firing trajectory.
    *   *Alternative (Mouse-following):* Track mouse coordinates via `screen.onclick()` or `screen.listen()` combined with `turtle.atan2()` to aim the cannon toward the cursor *(Uncertainty: Mouse tracking introduces higher complexity in standard Turtle compared to discrete keyboard event listeners).*
*   **Firing:**
    *   *Spacebar:* Triggers the projectile to launch from the current turret angle.
*   **Game Management:**
    *   *R Key:* Restart the game loop upon a Game Over state.

### 3. Game Mechanics
*   **Initialization:** Set up screen, register key bindings, initialize global variables (`score = 0`, `lives = 3`, `game_active = True`), and spawn the initial set of targets.
*   **Target Spawns and Movement:**
    *   Targets spawn at random $x$-coordinates ($-\text{width}/2 + 50$ to $\text{width}/2 - 50$) and fixed or random upper $y$-coordinates.
    *   Targets may remain stationary (static target shooter) or oscillate horizontally along the $x$-axis using a continuous `screen.ontimer()` loop.
*   **Projectile Physics:**
    *   When fired, the projectile calculates its $x$ and $y$ velocity components based on the firing angle using basic trigonometry ($\cos$ and $\sin$).
    *   The projectile updates its position incrementally inside a game loop or via a recursive `ontimer` function.
*   **Collision Detection:**
    *   Calculated using Euclidean distance (`turtle.distance()`) between the projectile and each active target.
    *   *Hit Condition:* If $\text{distance} < \text{collision threshold}$ (e.g., $< 20$ pixels), the target is hidden/respawned, the score increases, and the projectile resets.
    *   *Miss Condition:* If the projectile exceeds the upper screen boundary ($y > 300$), it resets to the player's position, and a life may be deducted.
*   **Game Loop & Timing:**
    *   Python Turtle relies on event-driven programming (`screen.listen()`) and non-blocking timers (`screen.ontimer(update_function, milliseconds)`) rather than a traditional `while True` game loop to maintain responsiveness and prevent window freezing.

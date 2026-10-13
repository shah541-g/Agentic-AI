<!-- Task T1: Research the requirements, game mechanics, and standard implementation of a Pong game using Python's turtle graphics module. -->

### 1. Requirements

To implement a classic Pong game using Python's built-in `turtle` module, the following functional and technical components are required:

*   **Python Environment:** Standard Python 3.x installation (the `turtle` module comes pre-installed with standard Python distributions on Windows, macOS, and Linux).
*   **Game Window (Screen):** A fixed-dimension window (commonly 800x600 pixels) with a black background, a designated window title, and animation tracing turned off (`screen.tracer(0)`) to allow manual frame updating for smooth rendering.
*   **Game Entities:**
    *   **Two Paddles:** Rectangular sprites controlled by the user(s) (Left player: W/S or standard keys; Right player: Up/Down arrow keys).
    *   **One Ball:** A square or circular sprite that moves continuously across the screen at a constant velocity vector.
    *   **Scoreboard:** Text display tracking the score of both Player A (Left) and Player B (Right).
    *   **Center Divider:** A dashed vertical line drawn down the middle of the screen for aesthetic accuracy.

---

### 2. Core Game Mechanics

*   **Paddle Movement:**
    *   Paddles are restricted to vertical movement (Y-axis) only.
    *   Movement must be bounded by the top and bottom borders of the game window to prevent paddles from disappearing off-screen.
*   **Ball Movement & Physics:**
    *   The ball moves by adding a constant delta value to its X and Y coordinates each frame (`dx` and `dy`).
    *   **Wall Collisions (Top/Bottom):** When the ball hits the top or bottom screen boundary, its vertical velocity (`dy`) is inverted (multiplied by `-1`), and it bounces away.
    *   **Goal Collisions (Left/Right):** If the ball passes the left or right boundary without hitting a paddle:
        *   The opposing player scores a point.
        *   The ball resets to the center (`0, 0`).
        *   The ball's horizontal direction (`dx`) reverses, serving toward the player who just conceded.
    *   **Paddle Collisions:**
        *   Standard implementation uses bounding-box collision detection (comparing the ball's X and Y coordinates against the paddle's current width/height boundaries).
        *   Upon collision, the ball's horizontal velocity (`dx`) is inverted, and its position is adjusted slightly to prevent "glitching" or getting stuck inside the paddle.
*   **Game Loop:**
    *   Because `turtle` lacks a native real-time game loop function, standard implementation utilizes `screen.ontimer()` or a `while True` loop paired with `screen.update()` and `time.sleep()` to control frame rates (typically ~60 FPS / `time.sleep(1/60)`).

---

### 3. Standard Implementation Architecture

A robust `turtle` Pong implementation is structured around an Object-Oriented Programming (OOP) approach or a clean procedural script separated into distinct modules/sections:

1.  **Initialization:** Set up the screen, register keyboard event listeners (`screen.listen()`, `screen.onkeypress()`), and instantiate the graphics objects.
2.  **Class/Object Breakdown (Typical):**
    *   *Paddle Class (inheriting from `turtle.Turtle`):* Handles shape (`stretch_wid`, `stretch_len`), color, starting position, and up/down movement methods.
    *   *Ball Class (inheriting from `turtle.Turtle`):* Handles shape, movement vector (`dx`, `dy`), wall bouncing logic, and reset mechanics.
    *   *Scoreboard Class (inheriting from `turtle.Turtle`):* Handles writing, clearing, and updating scores on the screen.
3.  **Main Game Loop Execution:**
    ```python
    # Conceptual standard loop structure
    while game_is_on:
        screen.update()
        time.sleep(0.016)  # ~60 FPS cap
        ball.move()

        # Detect wall collision
        if ball.ycor() > 290 or ball.ycor() < -290:
            ball.bounce_y()

        # Detect paddle collision
        if (
            ball.distance(right_paddle) < 50
            and ball.xcor() > 340
            or ball.distance(left_paddle) < 50
            and ball.xcor() < -340
        ):
            ball.bounce_x()

        # Detect right wall miss (Left scores)
        if ball.xcor() > 390:
            ball.reset_position()
            scoreboard.point_left()

        # Detect left wall miss (Right scores)
        if ball.xcor() < -390:
            ball.reset_position()
            scoreboard.point_right()
```

---

### 4. Areas of Uncertainty & Limitations

*   **Collision Accuracy:** The standard bounding-box or distance-based collision (`ball.distance()`) in `turtle` uses radial distance calculations or basic coordinate thresholds. This can occasionally cause edge-case bugs where the ball clips through the top/bottom corners of a paddle rather than bouncing cleanly. Advanced implementations require precise axis-aligned bounding box (AABB) intersection checks.
*   **Key Responsiveness (Input Lag):** Python's `turtle` event handling via `onkeypress` can suffer from operating system key-repeat delays (a slight pause before continuous movement kicks in). Developers often implement a custom boolean flag system tracking `press` and `release` events to ensure fluid, lag-free paddle movement, though this requires overriding default key bindings or using external tracking logic.

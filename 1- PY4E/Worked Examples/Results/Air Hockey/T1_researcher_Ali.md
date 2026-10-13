<!-- Task T1: Research the requirements and structure for building a basic 2-player Air Hockey game in Python using the turtle graphics module, including game loop, paddle movement, puck physics, and scorekeeping. -->

**Research Findings: Building a 2-Player Air Hockey Game in Python (Turtle Module)**

### 1. Overview and Requirements
To build a basic 2-player Air Hockey game in Python, the standard library `turtle` module is well-suited due to its built-in event handling, simple coordinate system, and graphical rendering capabilities. 

**Core Components Needed:**
*   **Game Window (Screen):** Sets up the playing field, background color, and animation updates (`tracer(0)`).
*   **The Puck:** A circular shape that moves across the screen, bounces off walls, and reacts to paddle collisions.
*   **Two Paddles:** Controlled by separate players via keyboard inputs, constrained to their respective halves of the table.
*   **Goals/Boundaries:** Lines or regions at opposite ends of the screen to detect scoring events.
*   **Scoreboard:** Text display tracking the score of Player 1 and Player 2.
*   **Game Loop:** A continuous `while` or `ontimer` loop that updates positions, checks collisions, and refreshes the screen.

---

### 2. Structure and Implementation Details

#### A. Initialization and Game Window
*   Create a screen instance using `turtle.Screen()`.
*   Set dimensions (e.g., width=800, height=600).
*   Turn off automatic screen updates using `screen.tracer(0)` to ensure smooth animation via manual `screen.update()` calls in the game loop.

#### B. Game Objects (Turtle Setup)
*   **Puck:** A turtle configured as a circle (`shape("circle")`), typically smaller than paddles, with initial `dx` and `dy` velocity variables.
*   **Paddles:** Two turtles configured as squares or circles, scaled up. 
    *   *Player 1 (Left):* Confined to the left half of the screen ($x < 0$).
    *   *Player 2 (Right):* Confined to the right half of the screen ($x > 0$).
*   **Centerline and Goals:** Drawn using a static turtle with `penup()`, `pendown()`, and `goto()` commands.

#### C. Paddle Movement & Controls
*   Use `screen.listen()` and `screen.onkeypress()` (or `onkeyrelease` for smoother movement) to bind keys.
    *   *Player 1 Controls:* `W` (Up), `S` (Down), `A` (Left), `D` (Right).
    *   *Player 2 Controls:* Arrow Keys (`Up`, `Down`, `Left`, `Right`).
*   **Boundary Constraints:** In the movement functions, check the paddle's coordinates (`xcor()`, `ycor()`) and prevent them from leaving the table or crossing the center line into the opponent's territory.

#### D. Puck Physics and Collision Detection
*   **Wall Collisions:** 
    *   If the puck hits the top or bottom wall ($y \ge \text{top\_limit}$ or $y \le \text{bottom\_limit}$), reverse its vertical velocity (`dy *= -1`).
    *   If the puck hits the left or right boundaries:
        *   Check if it enters the goal area. If yes, update the score.
        *   If not a goal (hitting the side boards), reverse its horizontal velocity (`dx *= -1`).
*   **Paddle Collisions:**
    *   Calculate the distance between the puck and each paddle using the Pythagorean theorem or `puck.distance(paddle)`.
    *   If the distance is less than the collision threshold (e.g., sum of their radii), reverse the puck's horizontal direction (`dx *= -1`) and optionally add a slight velocity boost based on paddle movement to simulate striking.

#### E. Scorekeeping
*   Maintain integer variables `score_a = 0` and `score_b = 0`.
*   Use a separate turtle instance to write the score to the screen using `write()`.
*   When a goal is detected:
    *   Increment the appropriate score.
    *   Reset the puck to the center of the screen (`goto(0, 0)`).
    *   Reverse or randomize the puck's initial heading for the next round.
    *   Clear and rewrite the scoreboard.

#### F. The Game Loop
*   Implemented typically via a `while True:` loop or a recursive `screen.ontimer()` function.
*   **Loop sequence:**
    1. Update puck position (`puck.setx(puck.xcor() + dx)`, `puck.sety(...)`).
    2. Check wall collisions.
    3. Check paddle collisions.
    4. Check goal/scoring conditions.
    5. Call `screen.update()`.
    6. Introduce a small delay (e.g., `time.sleep(0.01)` or managed via `ontimer`) to control game speed.

---

### 3. Areas of Uncertainty / Limitations
*   **Physics Realism:** Standard `turtle` lacks advanced rigid-body physics. Realistic angle deflection based on where the puck strikes the curved surface of a moving paddle requires vector math and trigonometry, which can be complex to implement cleanly in basic Python without external libraries.
*   **Key Lag:** Python's `turtle` event handling for continuous movement (`onkeypress`) can suffer from operating system key-repeat delays, resulting in stuttering paddle movement unless managed with a custom boolean state-tracking system (tracking key down/up events).

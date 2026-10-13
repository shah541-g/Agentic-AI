<!-- Task T1: Research the requirements and structure for building a Whack-a-Mole game using Python's turtle module, including target positioning, timer mechanisms, and click event handling. -->

### 1. Core Architecture and Module Selection
Building a Whack-a-Mole game in Python using the built-in `turtle` module requires a structured approach centered around event-driven programming. Because `turtle` is inherently single-threaded and event-driven, the application relies on a main game loop managed by `turtle.ontimer()` or recursive function calls, coupled with screen listeners for mouse input.

### 2. Target Positioning (Grid Setup)
To manage moles effectively, the game space must be mapped using coordinates. A standard grid (e.g., a $3 \times 3$ matrix) is established by defining fixed $(x, y)$ coordinate tuples.

*   **Mole Representation:** Moles can be represented either by individual Turtle objects assigned to each grid slot or by a single "active" Turtle that relocates to specific coordinates. Using a fixed list of coordinate tuples is the standard approach.
*   **Implementation Steps:**
    1. Define a list of coordinate pairs: `GRID_COORDS = [(-100, 100), (0, 100), (100, 100), ...]`
    2. Draw static "holes" on the screen at these coordinates using a base turtle.
    3. Instantiate a "mole" turtle that changes its visibility (`turtle.showturtle()` / `turtle.hideturtle()`) and teleports (`turtle.goto(x, y)`) to active grid slots.

### 3. Timer Mechanisms
Game duration, mole pop-up intervals, and mole disappearance rates require precise timing. Python's standard `time.sleep()` is **not** recommended inside the main thread because it freezes the turtle graphics window and blocks event handling (clicks).

*   **Non-Blocking Timers:** The `turtle` screen object provides the `ontimer(fun, t)` method, which executes a function `fun` after `t` milliseconds without freezing the event loop.
*   **Game Loop Implementation:**
    *   **Total Game Timer:** A countdown variable (e.g., `time_left = 30`) decremented every 1,000 milliseconds using a recursive `countdown()` function managed by `screen.ontimer()`.
    *   **Mole Pop-up Timer:** A separate recurring function (`pop_mole()`) selects a random coordinate from the grid, moves the mole there, makes it visible, and sets an `ontimer` to hide it after a set duration (e.g., 800 milliseconds).

### 4. Click Event Handling
Player interaction relies on detecting mouse clicks within the bounding box of the active mole.

*   **Screen-Level Click Registration:** `turtle.onscreenclick(fun)` captures the $(x, y)$ coordinates of any mouse click on the canvas.
*   **Hit Detection Logic:**
    1. The click handler function receives the arguments `(x, y)` representing the click location.
    2. The system checks if the mole is currently active (visible).
    3. It calculates the Euclidean distance or uses a bounding-box check between the click coordinates $(x, y)$ and the current mole coordinate.
    4. **Distance Formula:** $\sqrt{(x_{\text{click}} - x_{\text{mole}})^2 + (y_{\text{click}} - y_{\text{mole}})^2} < \text{hit\_radius}$
    5. If the distance is within the threshold, the score increments, and the mole immediately hides to prevent multi-scoring on a single appearance.

### 5. State Management and Scoring
A robust Whack-a-Mole implementation requires a global or class-based state tracker to manage:
*   `score`: Integer tracking successful hits.
*   `game_active`: Boolean flag to stop accepting clicks and spawning moles when time expires.
*   A dedicated scoreboard turtle (`turtle.Turtle()`) that updates text dynamically using `write()` whenever the score changes.

### Uncertainties and Limitations
*   **Concurrency Limits:** Because `turtle` is single-threaded, if multiple moles need to be active simultaneously, managing individual hide/show timers via `ontimer` can become complex and prone to race conditions without an object-oriented approach (e.g., creating a dedicated `Mole` class that manages its own state and timer).
*   **Performance Bottlenecks:** Rapidly drawing and clearing shapes can cause visual stuttering (lag) in `turtle`. Using pre-loaded custom shapes (`screen.register_shape()`) instead of standard vector drawings can improve performance, though rendering speed ultimately depends on the underlying Tcl/Tk framework.

<!-- Task T1: Research the requirements, libraries, and architecture needed to build a console-based Snake game in C++. -->

### 1. Requirements

Building a console-based Snake game in C++ requires handling real-time input, managing game state logic, rendering a grid within a terminal window, and controlling game speed.

*   **Platform Compatibility:** Terminal APIs differ significantly between operating systems (Windows vs. Unix-like systems such as Linux and macOS). The architecture must either abstract these differences or target a specific OS.
*   **Game Loop:** A continuous execution cycle consisting of three phases:
    1.  *Input:* Check for player keystrokes (WASD or Arrow keys) without pausing execution (non-blocking).
    2.  *Update:* Move the snake, check for collisions (walls, self, fruit), and update scores/fruit positions.
    3.  *Render:* Redraw the game board in the console.
*   **Timing/Frame Rate:** A mechanism to control the speed of the game loop (typically 100ms to 150ms per frame) so the snake does not move too fast.
*   **Rendering Performance:** Minimizing screen flicker by updating only changed characters or efficiently redrawing the buffer, rather than repeatedly calling system clear commands.

---

### 2. Libraries

Depending on whether you choose a standard library-only approach or external wrappers, several options exist:

#### Standard C++ Libraries (`<iostream>`, `<vector>`, `<chrono>`, `<random>`)
*   **`<vector>` / `<deque>`:** Essential for storing the coordinates of the snake's body segments. A `std::deque` is often preferred for efficient insertions at the front (head) and deletions at the back (tail).
*   **`<chrono>` and `<thread>`:** Used for cross-platform frame pacing (e.g., `std::this_thread::sleep_for`).
*   **`<random>`:** Standard C++ pseudo-random number generation for spawning food at random grid coordinates.

#### Input and Console Manipulation Libraries
*   **Platform-Specific (Standard for pure console apps):**
    *   **Windows (`<conio.h>`):** Provides `_kbhit()` (checks if a key was pressed) and `_getch()` (retrieves the pressed key without waiting for Enter).
    *   **Unix/Linux/macOS (`<termios.h>`, `<unistd.h>`, `<fcntl.h>`):** Requires modifying terminal settings to raw mode (disabling canonical mode and echo) to read non-blocking input via standard `read()`.
*   **External Wrapper Libraries (Recommended for Cross-Platform):**
    *   **PDCurses / NCurses:** A terminal-handling library that abstracts cursor movement, screen buffers, and non-blocking input across Windows and Unix. It drastically simplifies rendering and input handling without needing full graphical windows.

---

### 3. Architecture

A clean, modular object-oriented architecture keeps concerns separated (Game Engine, Input, Renderer, Entity Model).

```
[Main Function] 
       │
       ▼
[Game Engine / Controller] ◄─── [Input Handler]
       │
       ├──────────────► [Board / Grid Model]
       │                       │
       ├──────────────► [Snake Model (Deque)]
       │                       │
       └──────────────► [Renderer / View]
```

#### Component Breakdown:

1.  **`Point` / `Vector2` Struct:**
    *   Holds `int x` and `int y` coordinates.
    *   Overloads comparison operators (`==`) for collision detection.

2.  **`Snake` Class (Model):**
    *   Maintains a `std::deque<Point>` representing body segments.
    *   Maintains a current movement direction enum (`UP`, `DOWN`, `LEFT`, `RIGHT`).
    *   Contains methods: `Move()`, `Grow()`, and `CheckSelfCollision()`.

3.  **`Food` Class (Model):**
    *   Holds a `Point` coordinate.
    *   Contains a `Respawn(maxWidth, maxHeight, snakeBody)` method to generate new food locations that do not overlap with the snake.

4.  **`Game` Class (Controller / Engine):**
    *   Manages game state (`Running`, `GameOver`, `Paused`).
    *   Tracks the score and high score.
    *   Runs the core **Game Loop**:
        ```cpp
        while (is_running) {
            ProcessInput();
            Update();
            Render();
            Sleep(frame_duration);
        }
        ```

5.  **`Renderer` Class (View):**
    *   Handles drawing the boundaries, snake, and food to the console.
    *   *Optimization:* Instead of clearing the entire screen (`system("cls")` or `system("clear")`), which causes severe flickering, use ANSI escape codes (e.g., `\033[H` to move the cursor to the top-left) or `NCurses` buffer refreshes to overwrite the frame in place.

---

### 4. Uncertainties & Limitations

*   **Terminal Font Aspect Ratio:** Console characters are typically taller than they are wide (often a 2:1 height-to-width ratio). Without scaling factor adjustments (e.g., using two characters like `[]` or spaces for a "square" pixel), the game board will look vertically stretched.
*   **OS-Specific Input Nuances:** Writing native non-blocking input for Linux/macOS via `termios` requires restoring the terminal state upon exit. If the program crashes abruptly, the user's terminal may remain in "raw mode," requiring a manual `reset` command in the shell. Using a library like NCurses mitigates this risk by handling terminal state cleanup automatically.

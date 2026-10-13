<!-- Task T1: Research the requirements and structure for building a Tic-Tac-Toe game using Python's turtle graphics library, including game state logic and UI layout. -->

### 1. Introduction and Prerequisites
Python’s `turtle` module is a standard library tool well-suited for introducing graphical user interface (GUI) programming and event-driven game logic. Building Tic-Tac-Toe requires combining state management (tracking the board, turns, and win conditions) with spatial mathematics (mapping mouse clicks to grid coordinates and drawing shapes).

---

### 2. UI Layout and Spatial Design
The game board consists of a $3 \times 3$ grid, typically rendered within a square window (e.g., $600 \times 600$ pixels). 

*   **Window and Screen Setup:**
    *   Initialize the screen using `turtle.Screen()`. Set a fixed dimension (e.g., $600 \times 600$ pixels) and a background color.
    *   Hide the default turtle cursor using `hideturtle()` and speed up rendering using `tracer(0)` for manual screen updates via `update()`.
*   **Grid Coordinates:**
    *   If the window is $600 \times 600$, the coordinate system ranges from $-300$ to $300$ on both the X and Y axes.
    *   Divide the board into three columns and three rows. Each cell is $200 \times 200$ pixels.
    *   **Grid Lines:** Draw two vertical lines (at $x = -100$ and $x = 100$) and two horizontal lines (at $y = -100$ and $y = 100$).
*   **Cell Mapping (Click Detection):**
    *   Mouse clicks return screen coordinates $(x, y)$ via `screen.onclick(click_handler)`.
    *   Map these continuous $(x, y)$ coordinates to discrete grid indices `(row, col)` ranging from $0$ to $2$:
        *   **Columns:** 
            *   Col 0: $x < -100$
            *   Col 1: $-100 \le x \le 100$
            *   Col 2: $x > 100$
        *   **Rows:** 
            *   Row 0 (Top): $y > 100$
            *   Row 1 (Middle): $-100 \le y \le 100$
            *   Row 2 (Bottom): $y < -100$
    *   Calculate the exact center coordinates of each cell for drawing 'X' or 'O':
        *   `center_x = (col - 1) * 200` (assuming standard alignment, or adjusted based on offsets like $-200, 0, 200$).
        *   `center_y = (1 - row) * 200`.

---

### 3. Game State Logic
The game state must track board occupancy, current player turn, and game termination status.

*   **Data Structures:**
    *   **Board Representation:** A 1D list of 9 elements or a 2D list ($3 \times 3$) initialized to empty values (e.g., `""`, `None`, or integers `0`). Example: `board = [["" for _ in range(3)] for _ in range(3)]`.
    *   **Turn Tracker:** A variable tracking the active player, typically `"X"` and `"O"`. Player "X" traditionally goes first.
    *   **Game Over Flag:** A boolean variable (e.g., `game_over = False`) to prevent further moves after a win or tie.
*   **Move Validation:**
    *   When a click occurs and is mapped to `(row, col)`, verify if `board[row][col] == ""` (the cell is unoccupied) and `not game_over`.
    *   If valid, update `board[row][col] = current_player`.
*   **Win and Tie Conditions:**
    *   Check these conditions after every successful move.
    *   **Rows:** Check if any row has three identical, non-empty values (`board[r][0] == board[r][1] == board[r][2] != ""`).
    *   **Columns:** Check if any column has three identical, non-empty values (`board[0][c] == board[1][c] == board[2][c] != ""`).
    *   **Diagonals:** Check both diagonals:
        *   Top-left to bottom-right: `board[0][0] == board[1][1] == board[2][2] != ""`
        *   Top-right to bottom-left: `board[0][2] == board[1][1] == board[2][0] != ""`
    *   **Tie (Draw):** If no winning condition is met and all cells are occupied (no `""` remains in the board structure).
*   **State Transitions:**
    *   If a win or tie is detected, set `game_over = True` and display a message (using `turtle.write()` or a pop-up via `turtle.textinput` / `turtle.messagebox`).
    *   If the game continues, toggle the player: `current_player = "O" if current_player == "X" else "X"`.

---

### 4. Rendering Elements (`turtle` Specifics)
*   **Drawing the Board:** Use a dedicated turtle instance to lift the pen (`penup()`), move to start coordinates, put the pen down (`pendown()`), and draw the grid lines.
*   **Drawing 'X' and 'O':**
    *   To prevent the grid-drawing turtle from interfering, use a separate turtle instance or manage pen states carefully.
    *   **Drawing 'X':** Move to the cell center, offset diagonally, and draw two intersecting lines forming an 'X'.
    *   **Drawing 'O':** Move to the cell center, offset vertically, and use `circle(radius)` to draw a complete circle.
*   **Text Output:** Use `turtle.write(arg, move=False, align="center", font=(name, size, type))` to display turn indicators or game-over banners at the top or bottom of the screen.

---

### 5. Uncertainties and Limitations
*   **Event Handling Concurrency:** Python's `turtle` event loop (`screen.listen()` and `screen.onclick()`) runs asynchronously. Rapid clicking can cause race conditions or overlapping move processing if state flags (`game_over` or processing locks) are not checked atomically at the start of the click handler.
*   **Window Scaling/Resizing:** Resizing the turtle graphics window manually via the OS can break hardcoded pixel-to-grid coordinate mappings unless bound to window resize events (which `turtle` handles inconsistently across platforms). It is generally recommended to disable window resizing (`screen.setup(width, height)` without explicit resize bindings).

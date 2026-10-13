<!-- Task T1: Research and outline the game logic, grid dimensions, and card state management for a Python Turtle Memory Match game. -->

### 1. Grid Dimensions and Layout Logic

The Memory Match game board is typically structured as a 2D grid of cards. To calculate positions and ensure responsiveness, specific geometric parameters must be defined.

*   **Standard Grid Size:** A 4x4 grid (16 cards total) is standard for a balanced difficulty and performance level in Python Turtle. Alternative configurations include 4x3 (12 cards) or 6x6 (36 cards), requiring even totals for complete pairs.
*   **Window and Board Proportions:** 
    *   Assume a standard window size of $800 \times 800$ pixels.
    *   Board padding (margins) should occupy roughly 10–20% of the screen dimension to prevent cards from touching the window borders.
*   **Card Dimensions (in pixels):**
    *   Width ($W_c$): Typically $80$ to $100$ pixels.
    *   Height ($H_c$): Typically $100$ to $120$ pixels (maintaining a standard playing card aspect ratio of roughly $1:1.2$ or $1:1.4$).
*   **Spacing and Gaps:**
    *   Horizontal gap ($G_x$) and vertical gap ($G_y$) between cards: $15$ to $20$ pixels.
*   **Coordinate Calculation Formula:**
    *   To center the grid on the Turtle canvas (where $(0,0)$ is the center of the screen):
    *   Total Grid Width = $(Cols \times W_c) + ((Cols - 1) \times G_x)$
    *   Total Grid Height = $(Rows \times H_c) + ((Rows - 1) \times G_y)$
    *   Starting Top-Left X coordinate: $Start_X = -(\text{Total Grid Width} / 2) + (W_c / 2)$
    *   Starting Top-Left Y coordinate: $Start_Y = (\text{Total Grid Height} / 2) - (H_c / 2)$
    *   The center position of a card at grid index `(r, c)` (where `r` is row, `c` is column) is:
        *   $X_{rc} = Start_X + c \times (W_c + G_x)$
        *   $Y_{rc} = Start_Y - r \times (H_c + G_y)$

---

### 2. Card State Management

Each card in the game maintains a distinct state that dictates its visual representation and how it reacts to user input (mouse clicks).

*   **Possible States per Card:**
    1.  **Face-Down (Hidden):** The default state. The card displays its back design. It is interactive (can be clicked).
    2.  **Face-Up (Revealed):** The card displays its assigned front symbol/image. It is temporarily non-interactive to prevent double-clicking the same card.
    3.  **Matched (Solved):** The card has been successfully paired. It remains permanently face-up and is rendered inactive (clicks are ignored).

*   **Data Structure Design:**
    *   A centralized state tracker (e.g., a list of dictionaries, a 2D array, or a custom `Card` class) is required to manage all cards simultaneously.
    *   *Unsure:* While a 2D array (`list of lists`) maps directly to the visual grid, a 1D flat list (`list of objects/dicts`) mapped with an index simplifies click-detection coordinate math. A flat list paired with row/col attributes is recommended.

*   **Global Game State Variables:**
    *   `first_selection`: Tracks the index/reference of the first card clicked in a turn (`None` if no card is currently exposed).
    *   `second_selection`: Tracks the index/reference of the second card clicked.
    *   `lock_board`: A boolean flag (`True`/`False`) set to `True` while the game evaluates a pair, temporarily locking out all mouse inputs to prevent rapid-fire clicking bugs.
    *   `matches_found`: An integer counter tracking successful pairs (Win condition triggers when `matches_found == Total_Cards / 2`).

---

### 3. Core Game Logic and Turn Flow

The lifecycle of a player's turn follows a strict sequential state machine managed via event-driven programming (Turtle's `onscreenclick`).

1.  **Initialization:**
    *   Generate a list of symbol pairs (e.g., letters, numbers, or shapes). For a 16-card grid, use 8 unique symbols, each duplicated twice.
    *   Shuffle the list randomly using Python's `random.shuffle()`.
    *   Assign shuffled symbols to the card data structures and draw the grid in the face-down state.

2.  **Click Event Handling:**
    *   When the user clicks the screen, capture the $(x, y)$ coordinates.
    *   Iterate through the card bounding boxes to determine which card (if any) was clicked:
        $$\text{Inside Card if: } (X_{rc} - W_c/2 \le x \le X_{rc} + W_c/2) \text{ and } (Y_{rc} - H_c/2 \le y \le Y_{rc} + H_c/2)$$
    *   **Guard Clauses:** Ignore the click if:
        *   `lock_board` is `True`.
        *   The clicked card is already in the **Face-Up** or **Matched** state.
        *   The user clicks the exact same card twice as their first selection.

3.  **Turn Evaluation Logic:**
    *   **Step 1 (First Card):** Flip the card to **Face-Up**. Set `first_selection = clicked_card`.
    *   **Step 2 (Second Card):** Flip the card to **Face-Up**. Set `second_selection = clicked_card`. Set `lock_board = True`.
    *   **Step 3 (Comparison):** 
        *   Compare `first_selection.symbol` with `second_selection.symbol`.
        *   **If Match:** Update both cards' states to **Matched**. Reset `first_selection`, `second_selection`, and set `lock_board = False`. Increment `matches_found`. Check for Win Condition.
        *   **If No Match:** Keep cards visible briefly, then trigger a delayed callback (using `turtle.ontimer`) to flip both cards back to **Face-Down**. Once flipped back, reset selections and set `lock_board = False`.

4.  **Win Condition:**
    *   Triggered when `matches_found` equals total pairs. Display a victory message on the Turtle canvas.

---

### 4. Turtle-Specific Implementation Considerations

*   **Rendering Performance:** Drawing complex vector shapes via Turtle for every card frame drop can cause severe lag. *Best Practice:* Draw static rectangles/card backs once, or use stamp shapes (`turtle.shape()`) mapped to pre-loaded images/shapes to optimize redraw speeds during flips.
*   **Asynchronous Delays:** Python Turtle is single-threaded. Standard `time.sleep()` will freeze the entire window, preventing screen refreshes. **Must use `turtle.ontimer(function, milliseconds)`** to handle the delay before non-matching cards flip back face-down.
*   **Click Binding:** Instead of binding individual cards (which is tedious in Turtle), bind a single click listener to the main screen (`turtle.onscreenclick()`) and route the resulting $(x, y)$ coordinates through a collision-detection function against the grid objects.

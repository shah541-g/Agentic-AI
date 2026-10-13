<!-- Task T2: Write the Python code using the turtle module to implement the Memory Match game, including drawing the grid, handling mouse clicks, and checking for matching pairs. -->

```python
import random
import turtle

# ==========================================
# CONSTANTS & CONFIGURATION
# ==========================================
WINDOW_WIDTH = 800
WINDOW_HEIGHT = 800

GRID_ROWS = 4
GRID_COLS = 4
TOTAL_CARDS = GRID_ROWS * GRID_COLS
TOTAL_PAIRS = TOTAL_CARDS // 2

CARD_WIDTH = 100
CARD_HEIGHT = 130
GAP_X = 20
GAP_Y = 20

# Colors
BG_COLOR = "#1e1e2e"
CARD_BACK_COLOR = "#89b4fa"
CARD_BACK_BORDER = "#45475a"
CARD_FRONT_COLOR = "#f5e0dc"
CARD_MATCHED_COLOR = "#a6e3a1"
TEXT_COLOR = "#11111b"

# Symbols for the cards (8 unique pairs for a 4x4 grid)
SYMBOLS = ["🍎", "🍌", "🍇", "🍉", "🍒", "🍓", "🍍", "🥝"]

# ==========================================
# GLOBAL GAME STATE
# ==========================================
cards = []            # List of card dictionaries
first_selection = None  # Index of the first flipped card
second_selection = None # Index of the second flipped card
lock_board = False      # Flag to lock input during evaluation/animations
matches_found = 0     # Counter for successful pairs

# ==========================================
# TURTLE SETUP
# ==========================================
screen = turtle.Screen()
screen.setup(width=WINDOW_WIDTH, height=WINDOW_HEIGHT)
screen.bgcolor(BG_COLOR)
screen.title("Memory Match Game - Python Turtle")
screen.tracer(0)  # Disable automatic updates for manual performance rendering

drawer = turtle.Turtle()
drawer.hideturtle()
drawer.penup()

writer = turtle.Turtle()
writer.hideturtle()
writer.penup()

# ==========================================
# CARD DATA STRUCTURE & INITIALIZATION
# ==========================================
def setup_cards():
    """Initializes the deck with shuffled symbol pairs and calculates coordinates."""
    global cards
    cards = []
    
    # Duplicate and shuffle symbols
    deck_symbols = SYMBOLS * 2
    random.shuffle(deck_symbols)
    
    # Calculate grid layout dimensions
    total_grid_width = (GRID_COLS * CARD_WIDTH) + ((GRID_COLS - 1) * GAP_X)
    total_grid_height = (GRID_ROWS * CARD_HEIGHT) + ((GRID_ROWS - 1) * GAP_Y)
    
    start_x = -(total_grid_width / 2) + (CARD_WIDTH / 2)
    start_y = (total_grid_height / 2) - (CARD_HEIGHT / 2)
    
    index = 0
    for r in range(GRID_ROWS):
        for c in range(GRID_COLS):
            x = start_x + c * (CARD_WIDTH + GAP_X)
            y = start_y - r * (CARD_HEIGHT + GAP_Y)
            
            card = {
                "id": index,
                "row": r,
                "col": c,
                "x": x,
                "y": y,
                "symbol": deck_symbols[index],
                "state": "hidden"  # "hidden", "revealed", or "matched"
            }
            cards.append(card)
            index += 1

# ==========================================
# RENDERING FUNCTIONS
# ==========================================
def draw_card(card):
    """Draws a single card based on its current state."""
    drawer.goto(card["x"], card["y"])
    
    # Determine colors based on card state
    if card["state"] == "hidden":
        fill_color = CARD_BACK_COLOR
        border_color = CARD_BACK_BORDER
    elif card["state"] == "revealed":
        fill_color = CARD_FRONT_COLOR
        border_color = CARD_BACK_BORDER
    elif card["state"] == "matched":
        fill_color = CARD_MATCHED_COLOR
        border_color = CARD_BACK_BORDER

    # Draw card body (Rectangle with rounded corners simulated via square/shapes)
    drawer.setheading(0)
    drawer.goto(card["x"] - CARD_WIDTH / 2, card["y"] - CARD_HEIGHT / 2)
    drawer.pendown()
    drawer.color(border_color, fill_color)
    drawer.begin_fill()
    for _ in range(2):
        drawer.forward(CARD_WIDTH)
        drawer.left(90)
        drawer.forward(CARD_HEIGHT)
        drawer.left(90)
    drawer.end_fill()
    drawer.penup()
    
    # Draw content if revealed or matched
    if card["state"] in ["revealed", "matched"]:
        drawer.goto(card["x"], card["y"] - 22)  # Adjust vertical alignment for text emojis
        drawer.color(TEXT_COLOR)
        drawer.write(card["symbol"], align="center", font=("Arial", 32, "normal"))

def draw_board():
    """Redraws the entire game board."""
    drawer.clear()
    for card in cards:
        draw_card(card)
    
    # Draw UI status text
    writer.clear()
    writer.goto(0, (WINDOW_HEIGHT / 2) - 50)
    writer.color("white")
    if matches_found == TOTAL_PAIRS:
        writer.write("🎉 YOU WIN! GREAT JOB! 🎉", align="center", font=("Arial", 24, "bold"))
    else:
        writer.write(f"Matches Found: {matches_found} / {TOTAL_PAIRS}", align="center", font=("Arial", 18, "bold"))
        
    screen.update()

# ==========================================
# GAME LOGIC & EVENT HANDLERS
# ==========================================
def handle_click(x, y):
    """Handles mouse click events on the canvas."""
    global first_selection, second_selection, lock_board, matches_found
    
    if lock_board:
        return  # Ignore clicks while board is locked during evaluation
    
    # Check which card was clicked
    clicked_card = None
    for card in cards:
        half_w = CARD_WIDTH / 2
        half_h = CARD_HEIGHT / 2
        if (card["x"] - half_w <= x <= card["x"] + half_w) and \
           (card["y"] - half_h <= y <= card["y"] + half_h):
            clicked_card = card
            break
            
    # Guard clauses: Ensure a valid interactive card was clicked
    if not clicked_card:
        return
    if clicked_card["state"] != "hidden":
        return  # Can't click already revealed or matched cards
        
    # --- Turn Flow State Machine ---
    if first_selection is None:
        # First card choice
        first_selection = clicked_card["id"]
        cards[first_selection]["state"] = "revealed"
        draw_board()
        
    elif second_selection is None and clicked_card["id"] != first_selection:
        # Second card choice
        second_selection = clicked_card["id"]
        cards[second_selection]["state"] = "revealed"
        draw_board()
        
        # Lock board and evaluate match
        lock_board = True
        evaluate_turn()

def evaluate_turn():
    """Compares the two selected cards after a short visual delay."""
    global first_selection, second_selection, lock_board, matches_found
    
    card1 = cards[first_selection]
    card2 = cards[second_selection]
    
    if card1["symbol"] == card2["symbol"]:
        # MATCH FOUND
        card1["state"] = "matched"
        card2["state"] = "matched"
        matches_found += 1
        reset_turn_variables()
        draw_board()
    else:
        # NO MATCH: Wait 1 second before hiding cards again using ontimer
        screen.ontimer(hide_mismatched_cards, 1000)

def hide_mismatched_cards():
    """Flips non-matching cards back to hidden state."""
    global first_selection, second_selection
    if first_selection is not None and second_selection is not None:
        cards[first_selection]["state"] = "hidden"
        cards[second_selection]["state"] = "hidden"
    reset_turn_variables()
    draw_board()

def reset_turn_variables():
    """Resets selection trackers and unlocks the board."""
    global first_selection, second_selection, lock_board
    first_selection = None
    second_selection = None
    lock_board = False

# ==========================================
# MAIN EXECUTION
# ==========================================
def main():
    setup_cards()
    draw_board()
    
    # Bind mouse click event to screen
    screen.onscreenclick(handle_click)
    
    # Start the turtle event loop
    screen.mainloop()

if __name__ == "__main__":
    main()
```

### Usage Note
1. Ensure you have Python installed with the standard `turtle` library included.
2. Run the script using any standard Python environment: `python memory_match.py`.
3. A graphical window will open displaying a 4x4 grid of face-down blue cards. Click on any card to reveal its symbol, then click a second card to find a match. Matching pairs turn green, while incorrect pairs automatically flip back over after 1 second. Clear the entire board to win!

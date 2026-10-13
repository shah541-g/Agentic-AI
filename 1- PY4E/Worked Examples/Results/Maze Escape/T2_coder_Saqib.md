<!-- Task T2: Write the complete Python code using the turtle module to render the large maze, handle player movement controls, and implement win-condition collision detection. -->

```python
import turtle

# Maze data extracted from the prerequisite output
MAZE_DATA = {
  "maze_metadata": {
    "dimensions": {"width": 25, "height": 25},
    "legend": {"W": "Wall", "P": "Path", "S": "Start Position", "E": "Exit Position"},
    "start_position": {"x": 1, "y": 1},
    "exit_position": {"x": 23, "y": 23}
  },
  "grid": [
    ["W", "W", "W", "W", "W", "W", "W", "W", "W", "W", "W", "W", "W", "W", "W", "W", "W", "W", "W", "W", "W", "W", "W", "W", "W"],
    ["W", "S", "P", "P", "W", "P", "P", "P", "P", "P", "W", "P", "P", "P", "W", "P", "P", "P", "P", "P", "P", "P", "P", "P", "W"],
    ["W", "W", "W", "P", "W", "P", "W", "W", "W", "P", "W", "P", "W", "P", "W", "P", "W", "W", "W", "W", "W", "W", "W", "P", "W"],
    ["W", "P", "P", "P", "W", "P", "P", "P", "W", "P", "W", "P", "W", "P", "W", "P", "P", "P", "P", "P", "P", "P", "W", "P", "W"],
    ["W", "P", "W", "W", "W", "W", "W", "P", "W", "P", "W", "W", "W", "P", "W", "W", "W", "W", "W", "P", "W", "P", "W", "P", "W"],
    ["W", "P", "P", "P", "P", "P", "W", "P", "W", "P", "P", "P", "W", "P", "P", "P", "P", "P", "W", "P", "W", "P", "W", "P", "W"],
    ["W", "W", "W", "W", "W", "P", "W", "P", "W", "W", "W", "P", "W", "W", "W", "W", "W", "P", "W", "P", "W", "P", "W", "P", "W"],
    ["W", "P", "P", "P", "W", "P", "W", "P", "P", "P", "W", "P", "P", "P", "P", "P", "W", "P", "W", "P", "W", "P", "W", "P", "W"],
    ["W", "P", "W", "P", "W", "P", "W", "W", "W", "P", "W", "W", "W", "W", "W", "P", "W", "P", "W", "P", "W", "P", "W", "P", "W"],
    ["W", "P", "W", "P", "W", "P", "P", "P", "W", "P", "P", "P", "P", "P", "W", "P", "W", "P", "W", "P", "W", "P", "W", "P", "W"],
    ["W", "P", "W", "P", "W", "W", "W", "P", "W", "W", "W", "W", "W", "P", "W", "P", "W", "P", "W", "P", "W", "P", "W", "P", "W"],
    ["W", "P", "W", "P", "P", "P", "W", "P", "P", "P", "P", "P", "W", "P", "W", "P", "W", "P", "P", "P", "W", "P", "W", "P", "W"],
    ["W", "P", "W", "W", "W", "P", "W", "W", "W", "W", "W", "P", "W", "P", "W", "P", "W", "W", "W", "W", "W", "P", "W", "P", "W"],
    ["W", "P", "P", "P", "W", "P", "P", "P", "P", "P", "W", "P", "W", "P", "W", "P", "P", "P", "P", "P", "W", "P", "W", "P", "W"],
    ["W", "W", "W", "P", "W", "W", "W", "W", "W", "P", "W", "P", "W", "P", "W", "W", "W", "W", "W", "P", "W", "P", "W", "P", "W"],
    ["W", "P", "P", "P", "P", "P", "P", "P", "W", "P", "W", "P", "W", "P", "P", "P", "P", "P", "W", "P", "W", "P", "W", "P", "W"],
    ["W", "P", "W", "W", "W", "W", "W", "P", "W", "P", "W", "P", "W", "W", "W", "W", "W", "P", "W", "P", "W", "P", "W", "P", "W"],
    ["W", "P", "W", "P", "P", "P", "W", "P", "W", "P", "W", "P", "P", "P", "P", "P", "W", "P", "W", "P", "W", "P", "W", "P", "W"],
    ["W", "P", "W", "P", "W", "P", "W", "P", "W", "P", "W", "W", "W", "W", "W", "P", "W", "P", "W", "P", "W", "P", "W", "P", "W"],
    ["W", "P", "W", "P", "W", "P", "W", "P", "W", "P", "P", "P", "P", "P", "W", "P", "W", "P", "W", "P", "W", "P", "W", "P", "W"],
    ["W", "P", "W", "P", "W", "P", "W", "P", "W", "W", "W", "W", "W", "P", "W", "P", "W", "P", "W", "P", "W", "P", "W", "P", "W"],
    ["W", "P", "W", "P", "W", "P", "W", "P", "P", "P", "P", "P", "W", "P", "W", "P", "W", "P", "P", "P", "W", "P", "W", "P", "W"],
    ["W", "P", "W", "W", "W", "P", "W", "W", "W", "W", "W", "P", "W", "W", "W", "P", "W", "W", "W", "W", "W", "P", "W", "P", "W"],
    ["W", "P", "P", "P", "P", "P", "P", "P", "P", "P", "P", "P", "P", "P", "P", "P", "P", "P", "P", "P", "P", "P", "W", "E", "W"],
    ["W", "W", "W", "W", "W", "W", "W", "W", "W", "W", "W", "W", "W", "W", "W", "W", "W", "W", "W", "W", "W", "W", "W", "W", "W"]
  ]
}

# Configuration constants
CELL_SIZE = 20  # Size of each grid cell in pixels
GRID = MAZE_DATA["grid"]
WIDTH = MAZE_DATA["maze_metadata"]["dimensions"]["width"]
HEIGHT = MAZE_DATA["maze_metadata"]["dimensions"]["height"]

# Calculate screen offsets to center the maze
SCREEN_WIDTH = WIDTH * CELL_SIZE
SCREEN_HEIGHT = HEIGHT * CELL_SIZE
OFFSET_X = -SCREEN_WIDTH / 2
OFFSET_Y = SCREEN_HEIGHT / 2

# Set up screen
screen = turtle.Screen()
screen.title("Python Turtle Maze Game")
screen.setup(width=SCREEN_WIDTH + 60, height=SCREEN_HEIGHT + 60)
screen.tracer(0)  # Disable automatic screen updates for fast rendering

# Drawer turtle for rendering the maze statically
drawer = turtle.Turtle()
drawer.hideturtle()
drawer.penup()
drawer.speed(0)

def draw_maze():
    """Renders the maze walls, start, and exit zones onto the screen."""
    for y, row in enumerate(GRID):
        for x, cell in enumerate(row):
            # Calculate screen coordinates (Turtle 0,0 is at center)
            screen_x = OFFSET_X + (x * CELL_SIZE)
            screen_y = OFFSET_Y - (y * CELL_SIZE)
            
            if cell == "W":
                drawer.color("black", "black")
            elif cell == "S":
                drawer.color("black", "lightblue")
            elif cell == "E":
                drawer.color("black", "gold")
            else:
                continue  # Skip normal paths for background efficiency
                
            drawer.goto(screen_x, screen_y)
            drawer.begin_fill()
            for _ in range(4):
                drawer.forward(CELL_SIZE)
                drawer.right(90)
            drawer.end_fill()

# Draw the maze once before starting the game loop
draw_maze()
screen.update()

# Player setup
player = turtle.Turtle()
player.shape("circle")
player.color("crimson")
player.penup()
player.speed(0)

# Initialize player position coordinates (grid indices)
start_pos = MAZE_DATA["maze_metadata"]["start_position"]
player_x = start_pos["x"]
player_y = start_pos["y"]

def update_player_position():
    """Updates the graphical position of the player turtle based on grid indices."""
    screen_x = OFFSET_X + (player_x * CELL_SIZE) + (CELL_SIZE / 2)
    screen_y = OFFSET_Y - (player_y * CELL_SIZE) - (CELL_SIZE / 2)
    player.goto(screen_x, screen_y)

# Set initial player view position
update_player_position()
screen.update()

# Game state flag to stop movement once won
game_won = False

def move(dx, dy):
    """Handles movement logic, collision detection, and win conditions."""
    global player_x, player_y, game_won
    if game_won:
        return

    new_x = player_x + dx
    new_y = player_y + dy

    # Check boundaries
    if 0 <= new_x < WIDTH and 0 <= new_y < HEIGHT:
        target_cell = GRID[new_y][new_x]
        
        # Check collision with walls ('W')
        if target_cell != "W":
            player_x = new_x
            player_y = new_y
            update_player_position()
            screen.update()

            # Check win condition ('E')
            if target_cell == "E":
                game_won = True
                display_win_message()

def display_win_message():
    """Displays a congratulatory message on screen when the player reaches the exit."""
    writer = turtle.Turtle()
    writer.hideturtle()
    writer.penup()
    writer.color("green")
    writer.goto(0, 0)
    writer.write("YOU WIN! 🎉", align="center", font=("Arial", 28, "bold"))
    screen.update()

# Keyboard event bindings
screen.listen()
screen.onkey(lambda: move(0, -1), "Up")
screen.onkey(lambda: move(0, 1), "Down")
screen.onkey(lambda: move(-1, 0), "Left")
screen.onkey(lambda: move(1, 0), "Right")

# Also support WASD controls
screen.onkey(lambda: move(0, -1), "w")
screen.onkey(lambda: move(0, -1), "W")
screen.onkey(lambda: move(0, 1), "s")
screen.onkey(lambda: move(0, 1), "S")
screen.onkey(lambda: move(-1, 0), "a")
screen.onkey(lambda: move(-1, 0), "A")
screen.onkey(lambda: move(1, 0), "d")
screen.onkey(lambda: move(1, 0), "D")

# Keep window open
screen.mainloop()
```

### Usage Note
1. Ensure Python is installed along with the built-in `turtle` module.
2. Save the script to a file (e.g., `maze_game.py`) and run it using `python maze_game.py`.
3. Use the **Arrow keys** or **W/A/S/D keys** to navigate the crimson circle (player) from the light-blue start zone to the golden exit zone (`E`) marked at the end of the maze.

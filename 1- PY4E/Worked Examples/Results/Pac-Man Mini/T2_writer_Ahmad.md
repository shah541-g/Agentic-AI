<!-- Task T2: Design the game map layout, pellet placement data structures, and the main game window initialization using Python's turtle module. -->

```python
import turtle

# ==========================================
# CONSTANTS & CONFIGURATION
# ==========================================
WINDOW_WIDTH = 672
WINDOW_HEIGHT = 768
FPS_DELAY = 20  # milliseconds

# Tile scaling based on a 28x36 grid layout
# 28 columns * 24 pixels = 672 width
# 32 rows playable + top/bottom UI space = 36 rows * 21.33 pixels (~24 pixels for clean scaling)
TILE_SIZE = 24

# ==========================================
# MAP LAYOUT DATA STRUCTURE
# ==========================================
# Legend:
# '#' = Wall
# '.' = Standard Pellet (10 pts)
# 'O' = Energizer / Power Pellet (50 pts)
# ' ' = Empty Space / Traversable Corridor
# 'G' = Ghost House
# 'T' = Tunnel
MAP_LAYOUT = [
    "############################",
    "#............##............#",
    "#.####.#####.##.#####.####.#",
    "#O####.#####.##.#####.####O#",
    "#.####.#####.##.#####.####.#",
    "#..........................#",
    "#.####.##.########.##.####.#",
    "#.####.##.########.##.####.#",
    "#......##....##....##......#",
    "######.##### ## #####.######",
    "     #.##### ## #####.#     ",
    "     #.##          ##.#     ",
    "     #.## ###--### ##.#     ",
    "######.## # GGG # ##.######",
    "TTTTT.#   # GGG #   #.TTTTT",
    "######.## # ##### ##.######",
    "     #.##          ##.#     ",
    "     #.## ######## ##.#     ",
    "######.## ######## ##.######",
    "#............##............#",
    "#.####.#####.##.#####.####.#",
    "#.####.#####.##.#####.####.#",
    "#O..##.......  .......##..O#",
    "###.##.##.########.##.##.###",
    "###.##.##.########.##.##.###",
    "#......##....##....##......#",
    "#.##########.##.##########.#",
    "#.##########.##.##########.#",
    "#..........................#",
    "############################",
    "                            ",
    "                            "
]


class PacManGame:
    def __init__(self):
        # 1. Initialize the main game window
        self.screen = turtle.Screen()
        self.screen.title("Pac-Man Architecture - Map & Pellets")
        self.screen.setup(width=WINDOW_WIDTH, height=WINDOW_HEIGHT)
        self.screen.bgcolor("black")
        self.screen.tracer(0)  # Disable automatic screen updates for manual rendering performance

        # 2. Setup rendering turtle
        self.drawer = turtle.Turtle()
        self.drawer.hideturtle()
        self.drawer.speed(0)
        self.drawer.penup()

        # Data structures for game state entities
        self.walls = []
        self.pellets = []
        self.energizers = []

        # Build map structures from the ASCII layout
        self.parse_map_layout()

        # Draw the static environment
        self.render_map()

        # Finalize display update
        self.screen.update()

    def parse_map_layout(self):
        """Scans the MAP_LAYOUT matrix and populates coordinate collections for walls, pellets, and energizers."""
        rows = len(MAP_LAYOUT)
        cols = len(MAP_LAYOUT[0])

        # Calculate offset to center the 28x36 grid on the screen
        start_x = - (cols * TILE_SIZE) / 2 + TILE_SIZE / 2
        start_y = (rows * TILE_SIZE) / 2 - TILE_SIZE / 2

        for r_idx, row in enumerate(MAP_LAYOUT):
            for c_idx, char in enumerate(row):
                # Calculate cartesian screen coordinates for the current tile
                x = start_x + (c_idx * TILE_SIZE)
                y = start_y - (r_idx * TILE_SIZE)

                if char == '#':
                    self.walls.append((x, y))
                elif char == '.':
                    self.pellets.append((x, y))
                elif char == 'O':
                    self.energizers.append((x, y))

    def render_map(self):
        """Renders walls, standard pellets, and energizers using turtle graphics primitives."""
        # Render Walls
        self.drawer.color("blue")
        self.drawer.shape("square")
        for wx, wy in self.walls:
            self.drawer.goto(wx, wy)
            self.drawer.stamp()

        # Render Standard Pellets
        self.drawer.color("pink")
        for px, py in self.pellets:
            self.drawer.goto(px, py)
            # Draw a small dot for a standard pellet
            self.drawer.dot(4)

        # Render Energizers (Power Pellets)
        for ex, ey in self.energizers:
            self.drawer.goto(ex, ey)
            # Draw a larger dot for an energizer
            self.drawer.dot(12)

    def run(self):
        """Starts the main event listener loop."""
        self.screen.mainloop()


if __name__ == "__main__":
    game = PacManGame()
    game.run()
```

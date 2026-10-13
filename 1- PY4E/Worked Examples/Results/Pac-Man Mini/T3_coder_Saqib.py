import math
import random
import turtle

# ==========================================
# CONSTANTS & CONFIGURATION
# ==========================================
WINDOW_WIDTH = 672
WINDOW_HEIGHT = 768
FPS_DELAY = 30  # milliseconds per frame

# Tile scaling based on a 28x32 grid layout
TILE_SIZE = 24

# Map dimensions
COLS = 28
ROWS = 32

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
    "                            ",
]


class PacManGame:

    def __init__(self):
        # 1. Initialize the main game window
        self.screen = turtle.Screen()
        self.screen.title(
            "Pac-Man: Movement, Ghost AI, Collisions & Score Tracking"
        )
        self.screen.setup(width=WINDOW_WIDTH, height=WINDOW_HEIGHT)
        self.screen.bgcolor("black")
        self.screen.tracer(0)  # Disable auto-refresh for manual game loop

        # 2. Setup rendering & HUD turtles
        self.drawer = turtle.Turtle()
        self.drawer.hideturtle()
        self.drawer.speed(0)
        self.drawer.penup()

        self.hud = turtle.Turtle()
        self.hud.hideturtle()
        self.hud.speed(0)
        self.hud.color("white")
        self.hud.penup()

        # Game State Variables
        self.score = 0
        self.lives = 3
        self.game_over = False
        self.win = False

        # Frightened mode state timer
        self.frightened_timer = 0
        self.ghost_eat_score = 200

        # Data structures for map entities
        self.walls = set()
        self.pellets = set()
        self.energizers = set()
        self.tunnel_rows = set()

        # Parse map layout
        self.parse_map_layout()
        self.total_pellets_count = len(self.pellets) + len(self.energizers)

        # Initialize Entities
        self.setup_pacman()
        self.setup_ghosts()

        # Setup Keyboard Controls
        self.screen.listen()
        self.screen.onkey(lambda: self.set_pacman_intent("Up"), "Up")
        self.screen.onkey(lambda: self.set_pacman_intent("Down"), "Down")
        self.screen.onkey(lambda: self.set_pacman_intent("Left"), "Left")
        self.screen.onkey(lambda: self.set_pacman_intent("Right"), "Right")

        # Start game loop
        self.screen.ontimer(self.game_loop, FPS_DELAY)

    def parse_map_layout(self):
        """Scans MAP_LAYOUT and populates coordinate collections."""
        rows = len(MAP_LAYOUT)
        cols = len(MAP_LAYOUT[0])

        self.start_x = -(cols * TILE_SIZE) / 2 + TILE_SIZE / 2
        self.start_y = (rows * TILE_SIZE) / 2 - TILE_SIZE / 2

        for r_idx, row in enumerate(MAP_LAYOUT):
            for c_idx, char in enumerate(row):
                x = self.start_x + (c_idx * TILE_SIZE)
                y = self.start_y - (r_idx * TILE_SIZE)

                if char == "#":
                    self.walls.add((int(x), int(y)))
                elif char == ".":
                    self.pellets.add((int(x), int(y)))
                elif char == "O":
                    self.energizers.add((int(x), int(y)))
                elif char == "T":
                    self.tunnel_rows.add(int(y))

    def world_to_grid(self, x, y):
        """Converts world pixel coordinates to grid (col, row) indexes."""
        c = round((x - self.start_x) / TILE_SIZE)
        r = round((self.start_y - y) / TILE_SIZE)
        return int(c), int(r)

    def grid_to_world(self, c, r):
        """Converts grid (col, row) indexes to world pixel coordinates."""
        x = self.start_x + (c * TILE_SIZE)
        y = self.start_y - (r * TILE_SIZE)
        return int(x), int(y)

    def setup_pacman(self):
        """Initializes Pac-Man turtle and positioning state."""
        self.pacman = turtle.Turtle()
        self.pacman.shape("circle")
        self.pacman.color("yellow")
        self.pacman.penup()
        self.pacman.speed(0)

        # Pac-man starts around row 23, col 13.5
        wx, wy = self.grid_to_world(13.5, 23)
        self.pacman.goto(wx, wy)

        self.pac_speed = 3.0
        self.pac_dir = "Stop"
        self.pac_intent = "Stop"

    def setup_ghosts(self):
        """Initializes the 4 ghosts with distinct colors and home targets."""
        # Ghost definitions: (Name, Color, Scatter Target (col, row))
        ghost_configs = [
            ("Blinky", "red", (26, 0)),  # Top-Right corner
            ("Pinky", "pink", (1, 0)),  # Top-Left corner
            ("Inky", "cyan", (27, 31)),  # Bottom-Right corner
            ("Clyde", "orange", (0, 31)),  # Bottom-Left corner
        ]

        self.ghosts = []
        for name, color, scatter_target in ghost_configs:
            g = turtle.Turtle()
            g.shape("turtle")
            g.color(color)
            g.penup()
            g.speed(0)

            # Spawn inside ghost house (Row 14, Cols 12-15)
            wx, wy = self.grid_to_world(13.5, 14)
            g.goto(wx, wy)

            ghost_data = {
                "turtle": g,
                "name": name,
                "color": color,
                "speed": 2.5,
                "dir": "Up",
                "scatter_target": scatter_target,
                "state": "chase",  # chase, scatter, frightened, eaten
            }
            self.ghosts.append(ghost_data)

    def set_pacman_intent(self, direction):
        """Buffers keyboard input for Pac-Man turning."""
        self.pac_intent = direction

    def is_wall(self, x, y):
        """Checks if a given world coordinate collides with a wall."""
        gx, gy = self.world_to_grid(x, y)
        wx, wy = self.grid_to_world(gx, gy)
        return (wx, wy) in self.walls

    def get_valid_directions(self, x, y, current_dir):
        """Returns list of traversable directions excluding immediate reverse."""
        valid = []
        dirs = {
            "Up": (0, self.pac_speed),
            "Down": (0, -self.pac_speed),
            "Left": (-self.pac_speed, 0),
            "Right": (self.pac_speed, 0),
        }
        opposites = {
            "Up": "Down",
            "Down": "Up",
            "Left": "Right",
            "Right": "Left",
        }

        for d, (dx, dy) in dirs.items():
            # Prevent instant reversal unless trapped
            if d == opposites.get(current_dir):
                continue
            test_x = x + dx * 2
            test_y = y + dy * 2
            if not self.is_wall(test_x, test_y):
                valid.append(d)
        return valid

    def update_pacman(self):
        """Handles Pac-Man movement, grid snap-turns, and tunnel wrapping."""
        x, y = self.pacman.pos()

        # Handle Tunnel wrap-around on Row 14
        if int(y) in self.tunnel_rows:
            cols_max = COLS * TILE_SIZE
            if x < self.start_x - TILE_SIZE / 2:
                self.pacman.setx(-self.start_x)
                return
            elif x > -self.start_x + TILE_SIZE / 2:
                self.pacman.setx(self.start_x)
                return

        # Check intent buffering at tile intersections
        dx, dy = 0, 0
        if self.pac_intent == "Up":
            dy = self.pac_speed
        elif self.pac_intent == "Down":
            dy = -self.pac_speed
        elif self.pac_intent == "Left":
            dx = -self.pac_speed
        elif self.pac_intent == "Right":
            dx = self.pac_speed

        # Try to execute intended turn if corridor is open
        if self.pac_intent != self.pac_dir and self.pac_intent != "Stop":
            test_x = x + dx * 2
            test_y = y + dy * 2
            if not self.is_wall(test_x, test_y):
                self.pac_dir = self.pac_intent

        # Move along current active direction
        curr_dx, curr_dy = 0, 0
        if self.pac_dir == "Up":
            curr_dy = self.pac_speed
        elif self.pac_dir == "Down":
            curr_dy = -self.pac_speed
        elif self.pac_dir == "Left":
            curr_dx = -self.pac_speed
        elif self.pac_dir == "Right":
            curr_dx = self.pac_speed

        next_x = x + curr_dx
        next_y = y + curr_dy

        if not self.is_wall(next_x, next_y):
            self.pacman.goto(next_x, next_y)
        else:
            self.pac_dir = "Stop"

    def update_ghosts(self):
        """AI routing and movement for all ghosts based on state."""
        if self.frightened_timer > 0:
            self.frightened_timer -= 1
            if self.frightened_timer == 0:
                for g in self.ghosts:
                    if g["state"] == "frightened":
                        g["state"] = "chase"
                        g["turtle"].color(g["color"])

        pac_x, pac_y = self.pacman.pos()
        pac_c, pac_r = self.world_to_grid(pac_x, pac_y)

        for g in self.ghosts:
            gt = g["turtle"]
            gx, gy = gt.pos()
            gc, gr = self.world_to_grid(gx, gy)

            # Check if ghost is exactly aligned with a tile center for decision making
            target_wx, target_wy = self.grid_to_world(gc, gr)
            if abs(gx - target_wx) < 1.5 and abs(gy - target_wy) < 1.5:
                gt.goto(target_wx, target_wy)

                # Determine available directions (disallowing instant reversals)
                opposites = {
                    "Up": "Down",
                    "Down": "Up",
                    "Left": "Right",
                    "Right": "Left",
                }
                valid_dirs = []
                dir_vectors = {
                    "Up": (0, 1),
                    "Down": (0, -1),
                    "Left": (-1, 0),
                    "Right": (1, 0),
                }

                for d, (dc, dr) in dir_vectors.items():
                    if d == opposites.get(g["dir"]):
                        continue
                    test_c, test_r = gc + dc, gr + dr
                    twx, twy = self.grid_to_world(test_c, test_r)
                    if not self.is_wall(twx, twy):
                        valid_dirs.append((d, test_c, test_r))

                # Fallback if trapped
                if not valid_dirs:
                    valid_dirs = [(opposites[g["dir"]], gc, gr)]

                # Pick best direction based on Ghost AI State
                if g["state"] == "frightened":
                    # Choose pseudo-random valid direction
                    chosen = random.choice(valid_dirs)
                    g["dir"] = chosen[0]
                elif g["state"] == "eaten":
                    # Route back to Ghost house center (13.5, 14)
                    house_c, house_r = 13, 14
                    best_dir = valid_dirs[0]
                    min_dist = float("inf")
                    for d, tc, tr in valid_dirs:
                        dist = math.hypot(tc - house_c, tr - house_r)
                        if dist < min_dist:
                            min_dist = dist
                            best_dir = (d, tc, tr)
                    g["dir"] = best_dir[0]
                    if gc == house_c and gr == house_r:
                        g["state"] = "chase"
                        gt.color(g["color"])
                else:
                    # Chase / Scatter Targeting Priority (shortest Euclidean distance)
                    target_c, target_r = g["scatter_target"]
                    if g["state"] == "chase":
                        if g["name"] == "Blinky":
                            target_c, target_r = pac_c, pac_r
                        elif g["name"] == "Pinky":
                            # Target 4 tiles ahead of Pac-Man
                            pdir_map = {
                                "Up": (0, -4),
                                "Down": (0, 4),
                                "Left": (-4, 0),
                                "Right": (4, 0),
                            }
                            dc, dr = pdir_map.get(self.pac_dir, (0, 0))
                            target_c, target_r = pac_c + dc, pac_r + dr
                        elif g["name"] == "Clyde":
                            # Chase if > 8 tiles away, else scatter
                            dist_to_pac = math.hypot(gc - pac_c, gr - pac_r)
                            if dist_to_pac <= 8:
                                target_c, target_r = g["scatter_target"]
                            else:
                                target_c, target_r = pac_c, pac_r
                        elif g["name"] == "Inky":
                            target_c, target_r = pac_c, pac_r

                    # Evaluate intersection choices minimizing Euclidean distance to target
                    best_dir = valid_dirs[0]
                    min_dist = float("inf")
                    for d, tc, tr in valid_dirs:
                        dist = math.hypot(tc - target_c, tr - target_r)
                        if dist < min_dist:
                            min_dist = dist
                            best_dir = (d, tc, tr)
                    g["dir"] = best_dir[0]

            # Step ghost forward
            gs = (
                1.5
                if g["state"] == "frightened"
                else (3.5 if g["state"] == "eaten" else g["speed"])
            )
            gdx, gdy = 0, 0
            if g["dir"] == "Up":
                gdy = gs
            elif g["dir"] == "Down":
                gdy = -gs
            elif g["dir"] == "Left":
                gdx = -gs
            elif g["dir"] == "Right":
                gdx = gs

            gt.goto(gt.xcor() + gdx, gt.ycor() + gdy)

    def check_collisions(self):
        """Handles collisions with pellets, energizers, and ghosts."""
        px, py = self.pacman.pos()
        pc, pr = self.world_to_grid(px, py)
        p_coord = (int(self.grid_to_world(pc, pr)[0]), int(self.grid_to_world(pc, pr)[1]))

        # Pellet Consumption
        if p_coord in self.pellets:
            self.pellets.remove(p_coord)
            self.score += 10
            # Redraw map tile space clean (or rely on dot clearing)
            self.drawer.goto(p_coord[0], p_coord[1])
            self.drawer.color("black")
            self.drawer.dot(6)

        # Energizer Consumption
        elif p_coord in self.energizers:
            self.energizers.remove(p_coord)
            self.score += 50
            self.frightened_timer = 200  # ~6 seconds at 30 FPS
            self.ghost_eat_score = 200
            for g in self.ghosts:
                if g["state"] != "eaten":
                    g["state"] = "frightened"
                    g["turtle"].color("blue")
            self.drawer.goto(p_coord[0], p_coord[1])
            self.drawer.color("black")
            self.drawer.dot(16)

        # Win Condition Check
        if len(self.pellets) == 0 and len(self.energizers) == 0:
            self.win = True
            self.game_over = True

        # Ghost Collisions
        for g in self.ghosts:
            gt = g["turtle"]
            if gt.distance(self.pacman) < 20:
                if g["state"] == "frightened":
                    g["state"] = "eaten"
                    gt.color("white")
                    self.score += self.ghost_eat_score
                    self.ghost_eat_score *= 2
                elif g["state"] == "chase" or g["state"] == "scatter":
                    self.lives -= 1
                    if self.lives <= 0:
                        self.game_over = True
                    else:
                        self.reset_positions()
                    break

    def reset_positions(self):
        """Resets Pac-Man and ghosts to starting positions after losing a life."""
        wx, wy = self.grid_to_world(13.5, 23)
        self.pacman.goto(wx, wy)
        self.pac_dir = "Stop"
        self.pac_intent = "Stop"

        for g in self.ghosts:
            wx, wy = self.grid_to_world(13.5, 14)
            g["turtle"].goto(wx, wy)
            g["state"] = "chase"
            g["turtle"].color(g["color"])

    def render_map(self):
        """Draws static walls and remaining pellets."""
        self.drawer.color("blue")
        self.drawer.shape("square")
        for wx, wy in self.walls:
            self.drawer.goto(wx, wy)
            self.drawer.stamp()

        self.drawer.color("pink")
        for px, py in self.pellets:
            self.drawer.goto(px, py)
            self.drawer.dot(4)

        for ex, ey in self.energizers:
            self.drawer.goto(ex, ey)
            self.drawer.dot(12)

    def update_hud(self):
        """Updates onscreen score and lives display."""
        self.hud.clear()
        self.hud.goto(-WINDOW_WIDTH / 2 + 20, WINDOW_HEIGHT / 2 - 40)
        self.hud.write(
            f"SCORE: {self.score}   LIVES: {self.lives}",
            font=("Courier", 16, "bold"),
        )

    def game_loop(self):
        """Main game heartbeat loop."""
        if not self.game_over:
            self.update_pacman()
            self.update_ghosts()
            self.check_collisions()

            self.screen.update()
            self.update_hud()
            self.screen.ontimer(self.game_loop, FPS_DELAY)
        else:
            self.hud.goto(0, 0)
            msg = "YOU WIN!" if self.win else "GAME OVER"
            self.hud.write(
                f"{msg}\nFinal Score: {self.score}",
                align="center",
                font=("Courier", 24, "bold"),
            )
            self.screen.update()

    def run(self):
        """Renders static level geometry and starts main loop."""
        self.render_map()
        self.screen.update()
        self.screen.mainloop()


if __name__ == "__main__":
    game = PacManGame()
    game.run()

<!-- Task T2: Design the class architecture and game state logic for the Frogger game using Python and the turtle module. -->

```python
import turtle
import random

# ==========================================
# CONSTANTS & CONFIGURATION
# ==========================================
SCREEN_WIDTH = 480
SCREEN_HEIGHT = 600
TILE_SIZE = 40

# Grid Dimensions: 12 columns, 15 rows
COLS = 12
ROWS = 15

# Coordinate mapping helpers
# Screen center is (0,0). Top-left is (-240, 300), Bottom-right is (240, -300)
GRID_ORIGIN_X = -240 + (TILE_SIZE / 2)  # -220
GRID_ORIGIN_Y = 300 - (TILE_SIZE / 2)   #  280

def grid_to_pixel(col, row):
    """Converts grid column and row indices to Turtle screen coordinates (center of tile)."""
    x = GRID_ORIGIN_X + (col * TILE_SIZE)
    y = GRID_ORIGIN_Y - (row * TILE_SIZE)
    return x, y

def pixel_to_grid(x, y):
    """Converts screen coordinates to approximate grid column and row indices."""
    col = round((x - GRID_ORIGIN_X) / TILE_SIZE)
    row = round((GRID_ORIGIN_Y - y) / TILE_SIZE)
    return col, row


# ==========================================
# GAME STATE MANAGER
# ==========================================
class GameState:
    """Manages global game metrics, score, lives, timer, and difficulty scaling."""
    def __init__(self):
        self.score = 0
        self.high_score = 0
        self.lives = 3
        self.level = 1
        self.time_left = 60
        self.game_over = False
        self.won_slots = [False] * 5  # Tracks which of the 5 home slots are filled
        self.highest_row_reached = 13  # Used for awarding forward-progress points

    def reset_life(self):
        """Resets dynamic stats for a single life loss."""
        self.time_left = 60
        self.highest_row_reached = 13

    def reset_game(self):
        """Resets the entire game state back to initial conditions."""
        self.score = 0
        self.lives = 3
        self.level = 1
        self.won_slots = [False] * 5
        self.game_over = False
        self.reset_life()

    def check_level_clear(self):
        """Checks if all 5 home slots are filled. If so, triggers next level."""
        if all(self.won_slots):
            self.level += 1
            self.won_slots = [False] * 5
            self.score += 1000
            return True
        return False


# ==========================================
# BASE ENTITY CLASS
# ==========================================
class GameObject(turtle.Turtle):
    """Abstract base class for all rendered entities using the Turtle module."""
    def __init__(self, shape="square", color="white", size_mult_x=1, size_mult_y=1):
        super().__init__()
        self.shape(shape)
        self.color(color)
        self.penup()
        self.speed(0)
        if shape == "square":
            self.shapesize(stretch_wid=size_mult_y, stretch_len=size_mult_x)

    def get_bounds(self):
        """Returns bounding box coordinates (left, right, top, bottom) for AABB collision detection."""
        x, y = self.pos()
        # Default turtle shape dimensions are 20x20 pixels base, scaled by shapesize
        w_half = (self.shapesize()[1] * 20) / 2
        h_half = (self.shapesize()[0] * 20) / 2
        return {
            "left": x - w_half,
            "right": x + w_half,
            "top": y + h_half,
            "bottom": y - h_half
        }

    def collides_with(self, other):
        """AABB Collision Detection against another GameObject."""
        b1 = self.get_bounds()
        b2 = other.get_bounds()
        return not (
            b1["right"] < b2["left"] or
            b1["left"] > b2["right"] or
            b1["top"] < b2["bottom"] or
            b1["bottom"] > b2["top"]
        )


# ==========================================
# PLAYER (FROG) CLASS
# ==========================================
class Frog(GameObject):
    """Player-controlled Frog entity handling grid movement and platform riding."""
    def __init__(self):
        super().__init__(shape="triangle", color="#00FF00")
        self.left(90)  # Face upward initially
        self.reset_position()
        self.current_platform = None

    def reset_position(self):
        """Resets frog to the starting safety median (Row 13, Col 5/6 center)."""
        self.col = 6
        self.row = 13
        x, y = grid_to_pixel(self.col, self.row)
        self.goto(x, y)
        self.current_platform = None

    def move(self, dx, dy, game_state):
        """
        Executes discrete grid-locked movement.
        dx: delta columns (-1, 1, or 0)
        dy: delta rows (-1 for forward/up, 1 for backward/down)
        """
        if game_state.game_over:
            return

        target_col = self.col + dx
        target_row = self.row + dy

        # Boundary checks
        if 0 <= target_col < COLS and 0 <= target_row < ROWS:
            # Prevent entering row 0 (top banner) or out of bounds
            if target_row == 0:
                return

            self.col = target_col
            self.row = target_row
            x, y = grid_to_pixel(self.col, self.row)
            self.goto(x, y)
            self.current_platform = None  # Detach from platform upon manual jump

            # Award points for forward progress (lower row number means higher up the board)
            if self.row < game_state.highest_row_reached:
                game_state.highest_row_reached = self.row
                game_state.score += 10

    def update_position_with_platform(self):
        """If riding a platform, moves the frog along with the platform's velocity."""
        if self.current_platform:
            vx = self.current_platform.velocity
            x, y = self.pos()
            new_x = x + vx
            self.setx(new_x)
            
            # Update internal column tracker based on new coordinate
            self.col, _ = pixel_to_grid(new_x, y)

            # Check if platform carried the frog off-screen
            if new_x < -SCREEN_WIDTH/2 or new_x > SCREEN_WIDTH/2:
                return False  # Triggers death (drowned/off-screen)
        return True


# ==========================================
# OBSTACLE CLASSES (VEHICLES & PLATFORMS)
# ==========================================
class Obstacle(GameObject):
    """Base class for moving road vehicles and river platforms."""
    def __init__(self, x, y, width_multiplier, velocity, color, shape="square"):
        super().__init__(shape=shape, color=color, size_mult_x=width_multiplier, size_mult_y=1)
        self.goto(x, y)
        self.velocity = velocity
        self.width_multiplier = width_multiplier

    def update(self):
        """Moves obstacle horizontally and wraps around screen bounds."""
        x, y = self.pos()
        new_x = x + self.velocity
        
        # Screen wrapping logic with padding based on size
        total_width = self.width_multiplier * TILE_SIZE
        half_width = total_width / 2

        limit_right = (SCREEN_WIDTH / 2) + half_width
        limit_left = (-SCREEN_WIDTH / 2) - half_width

        if self.velocity > 0 and new_x > limit_right:
            new_x = limit_left
        elif self.velocity < 0 and new_x < limit_left:
            new_x = limit_right

        self.setx(new_x)


class Vehicle(Obstacle):
    """Road obstacles (cars, trucks, bulldozers) located in rows 8-12."""
    def __init__(self, x, y, width_multiplier, velocity, color):
        super().__init__(x, y, width_multiplier, velocity, color)


class Platform(Obstacle):
    """River obstacles (logs and turtles) located in rows 2-6."""
    def __init__(self, x, y, width_multiplier, velocity, color, is_turtle=False):
        super().__init__(x, y, width_multiplier, velocity, color, shape="square" if not is_turtle else "circle")
        self.is_turtle = is_turtle


# ==========================================
# MANAGER / CONTROLLER CLASS
# ==========================================
class FroggerGame:
    """Main game orchestration class managing loops, object instantiation, and event handling."""
    def __init__(self):
        # 1. Setup Screen
        self.screen = turtle.Screen()
        self.screen.setup(width=SCREEN_WIDTH, height=SCREEN_HEIGHT)
        self.screen.title("Frogger - Python Turtle Edition")
        self.screen.bgcolor("#111111")
        self.screen.tracer(0)  # Manual rendering control for smooth frame rates

        # 2. Core Systems
        self.state = GameState()
        self.frog = Frog()

        # 3. UI Display Turtle
        self.ui_turtle = turtle.Turtle()
        self.ui_turtle.hideturtle()
        self.ui_turtle.penup()
        self.ui_turtle.color("white")

        # 4. Entities Collections
        self.vehicles = []
        self.platforms = []
        self.home_slots_coords = []

        self.setup_level()
        self.bind_keys()

    def setup_level(self):
        """Initializes game rows, populates obstacles based on current level speed scaling."""
        self.vehicles.clear()
        self.platforms.clear()
        self.home_slots_coords.clear()

        speed_multiplier = 1.0 + ((self.state.level - 1) * 0.2)

        # --- ROAD ROWS (8 to 12) ---
        # Row 12: Slow Cars (Moving Right)
        self.spawn_row_obstacles(12, Vehicle, width=1.5, velocity=1.5 * speed_multiplier, color="#FF0000", count=3, spacing=180)
        # Row 11: Bulldozers (Moving Left)
        self.spawn_row_obstacles(11, Vehicle, width=2.0, velocity=-2.0 * speed_multiplier, color="#FFFF00", count=2, spacing=240)
        # Row 10: Race Cars (Moving Right)
        self.spawn_row_obstacles(10, Vehicle, width=1.0, velocity=3.0 * speed_multiplier, color="#FF00FF", count=3, spacing=160)
        # Row 9: Trucks (Moving Left)
        self.spawn_row_obstacles(9, Vehicle, width=3.0, velocity=-1.0 * speed_multiplier, color="#00FFFF", count=2, spacing=300)
        # Row 8: Fast Cars (Moving Right)
        self.spawn_row_obstacles(8, Vehicle, width=1.2, velocity=3.5 * speed_multiplier, color="#FFA500", count=3, spacing=150)

        # --- RIVER ROWS (2 to 6) ---
        # Row 6: Slow Turtles (Moving Right)
        self.spawn_row_obstacles(6, Platform, width=1.5, velocity=1.0 * speed_multiplier, color="#008080", count=3, spacing=180, is_turtle=True)
        # Row 5: Long Logs (Moving Left)
        self.spawn_row_obstacles(5, Platform, width=4.0, velocity=-1.5 * speed_multiplier, color="#8B4513", count=2, spacing=280)
        # Row 4: Logs (Moving Right)
        self.spawn_row_obstacles(4, Platform, width=2.5, velocity=2.0 * speed_multiplier, color="#A0522D", count=3, spacing=200)
        # Row 3: Turtles (Moving Left)
        self.spawn_row_obstacles(3, Platform, width=2.0, velocity=-2.5 * speed_multiplier, color="#008080", count=3, spacing=170, is_turtle=True)
        # Row 2: Fast Logs (Moving Right)
        self.spawn_row_obstacles(2, Platform, width=2.0, velocity=3.0 * speed_multiplier, color="#CD853F", count=3, spacing=190)

        # --- HOME SLOTS (Row 1) ---
        # 5 designated slots across width. Precompute slot target coordinates.
        slot_columns = [1, 3.5, 6, 8.5, 11]  # Adjusted mapping for 12 columns width
        for col_idx in slot_columns:
            x, y = grid_to_pixel(col_idx, 1)
            self.home_slots_coords.append({"x": x, "y": y, "col": col_idx})

    def spawn_row_obstacles(self, row, cls, width, velocity, color, count, spacing, is_turtle=False):
        """Helper to cleanly instantiate rows of vehicles or river platforms."""
        _, y = grid_to_pixel(0, row)
        for i in range(count):
            x = -SCREEN_WIDTH / 2 + (i * spacing) + random.randint(-20, 20)
            if cls == Vehicle:
                obs = Vehicle(x, y, width, velocity, color)
                self.vehicles.append(obs)
            elif cls == Platform:
                obs = Platform(x, y, width, velocity, color, is_turtle=is_turtle)
                self.platforms.append(obs)

    def bind_keys(self):
        """Maps user inputs to directional methods."""
        self.screen.listen()
        self.screen.onkey(lambda: self.frog.move(0, -1, self.state), "Up")
        self.screen.onkey(lambda: self.frog.move(0, -1, self.state), "w")
        self.screen.onkey(lambda: self.frog.move(0, 1, self.state), "Down")
        self.screen.onkey(lambda: self.frog.move(0, 1, self.state), "s")
        self.screen.onkey(lambda: self.frog.move(-1, 0, self.state), "Left")
        self.screen.onkey(lambda: self.frog.move(-1, 0, self.state), "a")
        self.screen.onkey(lambda: self.frog.move(1, 0, self.state), "Right")
        self.screen.onkey(lambda: self.frog.move(1, 0, self.state), "d")
        self.screen.onkey(self.reset_game_external, "r")

    def reset_game_external(self):
        """External hook to restart the game state via keyboard command."""
        if self.state.game_over:
            self.state.reset_game()
            self.setup_level()

    def handle_collisions(self):
        """Evaluates intersections between the frog, hazards, and river platforms."""
        frog_row = self.frog.row

        # 1. Road Hazards (Rows 8 to 12)
        if 8 <= frog_row <= 12:
            for vehicle in self.vehicles:
                if self.frog.collides_with(vehicle):
                    self.trigger_death()
                    return

        # 2. River Mechanics (Rows 2 to 6)
        elif 2 <= frog_row <= 6:
            on_platform = False
            for platform in self.platforms:
                if self.frog.collides_with(platform):
                    on_platform = True
                    self.frog.current_platform = platform
                    break
            
            if not on_platform:
                # Fell directly into water without landing on a platform
                self.trigger_death()
                return
            else:
                # Update position based on platform velocity and verify boundary limits
                if not self.frog.update_position_with_platform():
                    self.trigger_death()
                    return

        # 3. Home Slots / Win Condition (Row 1)
        elif frog_row == 1:
            reached_slot = False
            fx, fy = self.frog.pos()
            
            for idx, slot in enumerate(self.home_slots_coords):
                # Check proximity to slot target coordinates
                if abs(fx - slot["x"]) < 20:
                    if not self.state.won_slots[idx]:
                        self.state.won_slots[idx] = True
                        self.state.score += 200
                        reached_slot = True
                        
                        # Check if level cleared
                        if self.state.check_level_clear():
                            self.setup_level()
                        
                        self.frog.reset_position()
                        self.state.reset_life()
                        break
                    else:
                        # Slot already occupied
                        reached_slot = True
                        break

            if not reached_slot:
                # Hit the safety wall between slots
                self.trigger_death()

    def trigger_death(self):
        """Handles player life deduction and resets frog positioning."""
        self.state.lives -= 1
        if self.state.lives < 0:
            self.state.game_over = True
        else:
            self.frog.reset_position()
            self.state.reset_life()

    def update_ui(self):
        """Renders heads-up display (Score, Lives, Level, Timer) via Turtle drawing commands."""
        self.ui_turtle.clear()
        
        # Draw top banner stats
        self.ui_turtle.goto(-230, 265)
        self.ui_turtle.write(
            f"SCORE: {self.state.score}   LIVES: {'🐸 ' * max(0, self.state.lives)}   LEVEL: {self.state.level}   TIME: {int(self.state.time_left)}",
            font=("Courier", 12, "bold")
        )

        # Draw home slot achievement indicators
        for idx, slot in enumerate(self.home_slots_coords):
            if self.state.won_slots[idx]:
                self.ui_turtle.goto(slot["x"] - 10, slot["y"] - 10)
                self.ui_turtle.write("🐸", font=("Courier", 12, "normal"))

        # Draw Game Over Overlay Screen if applicable
        if self.state.game_over:
            self.ui_turtle.goto(0, 0)
            self.ui_turtle.color("red")
            self.ui_turtle.write("GAME OVER\nPress 'R' to Restart", align="center", font=("Courier", 20, "bold"))
            self.ui_turtle.color("white")

    def run(self):
        """Main Game Loop executing at ~30 FPS using custom delta-time calculations."""
        fps = 30
        frame_delay = int(1000 / fps)

        def game_loop():
            if not self.state.game_over:
                # Update Timer
                self.state.time_left -= (frame_delay / 1000.0)
                if self.state.time_left <= 0:
                    self.trigger_death()

                # Update Obstacles
                for v in self.vehicles:
                    v.update()
                for p in self.platforms:
                    p.update()

                # Handle Collisions and Game Logic
                self.handle_collisions()

            # Render UI and update screen buffer
            self.update_ui()
            self.screen.update()

            # Schedule next frame iteration
            self.screen.ontimer(game_loop, frame_delay)

        # Kick off loop
        game_loop()
        self.screen.mainloop()


# ==========================================
# EXECUTION ENTRY POINT
# ==========================================
if __name__ == "__main__":
    game = FroggerGame()
    game.run()
```

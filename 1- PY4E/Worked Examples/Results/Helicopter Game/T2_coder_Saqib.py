import random
import tkinter as tk

# Window dimensions
WIDTH = 800
HEIGHT = 600

# Game constants
GRAVITY = 0.5
LIFT = -8.0
MAX_VELOCITY = 10.0
SCROLL_SPEED = 4
TUNNEL_HEIGHT = 200
SEGMENT_WIDTH = 20


class HelicopterGame:

    def __init__(self, root):
        self.root = root
        self.root.title("Classic Helicopter Game")
        self.root.geometry(f"{WIDTH}x{HEIGHT}")
        self.root.resizable(False, False)

        # Canvas for rendering
        self.canvas = tk.Canvas(
            root, width=WIDTH, height=HEIGHT, bg="black", highlightthickness=0
        )
        self.canvas.pack()

        # Bind controls (Spacebar or Mouse click to fly)
        self.root.bind("<space>", self.on_thrust_press)
        self.root.bind("<KeyRelease-space>", self.on_thrust_release)
        self.canvas.bind("<Button-1>", self.on_click_press)
        self.canvas.bind("<ButtonRelease-1>", self.on_click_release)

        # Game variables
        self.is_thrusting = False
        self.game_started = False
        self.game_over = False
        self.score = 0
        self.high_score = 0

        # Helicopter properties
        self.heli_x = 150
        self.heli_y = HEIGHT // 2
        self.heli_vy = 0
        self.heli_radius = 15

        # Cave properties (list of [x, top_height, bottom_y])
        self.cave = []

        self.init_cave()
        self.create_start_screen()

        # Start game loop
        self.update_game()

    def init_cave(self):
        """Initializes the cave segments across the screen width."""
        self.cave = []
        top = 50
        bottom = HEIGHT - 50

        for x in range(0, WIDTH + SEGMENT_WIDTH * 2, SEGMENT_WIDTH):
            self.cave.append([x, top, bottom])

    def create_start_screen(self):
        """Draws the start screen elements."""
        self.canvas.delete("all")
        self.draw_cave()
        self.canvas.create_text(
            WIDTH // 2,
            HEIGHT // 2 - 40,
            text="HELICOPTER CAVE GAME",
            fill="cyan",
            font=("Courier", 28, "bold"),
        )
        self.canvas.create_text(
            WIDTH // 2,
            HEIGHT // 2 + 10,
            text="Press SPACEBAR or Click & Hold to Fly",
            fill="white",
            font=("Courier", 14),
        )
        self.canvas.create_text(
            WIDTH // 2,
            HEIGHT // 2 + 50,
            text="Avoid the ceiling, floor, and obstacles!",
            fill="yellow",
            font=("Courier", 12),
        )

    def on_thrust_press(self, event):
        if not self.game_started and not self.game_over:
            self.game_started = True
        elif self.game_over:
            self.reset_game()
        self.is_thrusting = True

    def on_thrust_release(self, event):
        self.is_thrusting = False

    def on_click_press(self, event):
        if not self.game_started and not self.game_over:
            self.game_started = True
        elif self.game_over:
            self.reset_game()
        self.is_thrusting = True

    def on_click_release(self, event):
        self.is_thrusting = False

    def reset_game(self):
        """Resets the game state for a new round."""
        self.game_over = False
        self.game_started = True
        self.score = 0
        self.heli_y = HEIGHT // 2
        self.heli_vy = 0
        self.init_cave()

    def update_cave(self):
        """Scrolls the cave and procedurally generates new segments."""
        # Move existing segments left
        for segment in self.cave:
            segment[0] -= SCROLL_SPEED

        # Remove segments off screen and add new ones on the right
        if self.cave[0][0] + SEGMENT_WIDTH < 0:
            self.cave.pop(0)

            last_x, last_top, last_bottom = self.cave[-1]
            new_x = last_x + SEGMENT_WIDTH

            # Random walk for cave height, constrained by boundaries
            height_change = random.randint(-25, 25)
            new_top = max(
                20, min(HEIGHT - TUNNEL_HEIGHT - 100, last_top + height_change)
            )
            new_bottom = new_top + TUNNEL_HEIGHT

            self.cave.append([new_x, new_top, new_bottom])

    def check_collision(self):
        """Checks if the helicopter hits the ceiling or floor."""
        # Top/Bottom screen boundaries
        if (
            self.heli_y - self.heli_radius <= 0
            or self.heli_y + self.heli_radius >= HEIGHT
        ):
            return True

        # Cave wall boundaries
        for segment in self.cave:
            seg_x, seg_top, seg_bottom = segment
            # Check if helicopter is within this segment's x range
            if seg_x <= self.heli_x + self.heli_radius <= seg_x + SEGMENT_WIDTH:
                if (
                    self.heli_y - self.heli_radius <= seg_top
                    or self.heli_y + self.heli_radius >= seg_bottom
                ):
                    return True

        return False

    def update_game(self):
        """Main game loop update function."""
        if self.game_started and not self.game_over:
            # Physics calculations
            if self.is_thrusting:
                self.heli_vy += LIFT
            else:
                self.heli_vy += GRAVITY

            # Terminal velocity clamping
            if self.heli_vy > MAX_VELOCITY:
                self.heli_vy = MAX_VELOCITY
            elif self.heli_vy < -MAX_VELOCITY:
                self.heli_vy = -MAX_VELOCITY

            self.heli_y += self.heli_vy

            # Update Cave
            self.update_cave()

            # Score tracking
            self.score += 1

            # Collision Detection
            if self.check_collision():
                self.game_over = True
                if self.score > self.high_score:
                    self.high_score = self.score

            # Redraw Frame
            self.draw_game()

        elif self.game_over:
            self.draw_game_over()

        # Loop at ~60 FPS (16ms)
        self.root.after(16, self.update_game)

    def draw_cave(self):
        """Renders the cave walls onto the canvas."""
        for segment in self.cave:
            x, top, bottom = segment
            # Top ceiling polygon/rectangle
            self.canvas.create_rectangle(
                x,
                0,
                x + SEGMENT_WIDTH + 1,
                top,
                fill="#00aa00",
                outline="#00aa00",
            )
            # Bottom floor polygon/rectangle
            self.canvas.create_rectangle(
                x,
                bottom,
                x + SEGMENT_WIDTH + 1,
                HEIGHT,
                fill="#00aa00",
                outline="#00aa00",
            )

    def draw_game(self):
        """Renders active gameplay elements."""
        self.canvas.delete("all")

        # Draw Cave
        self.draw_cave()

        # Draw Helicopter (Body + Tail + Rotor)
        hx, hy = self.heli_x, self.heli_y
        # Main body
        self.canvas.create_oval(
            hx - 15,
            hy - 10,
            hx + 15,
            hy + 10,
            fill="red",
            outline="white",
            width=2,
        )
        # Tail boom
        self.canvas.create_line(
            hx - 15, hy, hx - 28, hy - 5, fill="white", width=3
        )
        # Rotor blade (tilts slightly based on vertical velocity)
        tilt = self.heli_vy * 1.5
        self.canvas.create_line(
            hx - 20,
            hy - 14,
            hx + 20,
            hy - 14 + tilt,
            fill="cyan",
            width=3,
        )
        # Skids
        self.canvas.create_line(
            hx - 8, hy + 10, hx + 8, hy + 10, fill="white", width=2
        )

        # Draw Score
        self.canvas.create_text(
            50,
            25,
            text=f"SCORE: {self.score}",
            fill="white",
            font=("Courier", 14, "bold"),
            anchor="w",
        )
        self.canvas.create_text(
            WIDTH - 50,
            25,
            text=f"HIGH SCORE: {self.high_score}",
            fill="yellow",
            font=("Courier", 14, "bold"),
            anchor="e",
        )

    def draw_game_over(self):
        """Renders the game over screen overlay."""
        # Keep background drawn underneath
        self.canvas.delete("all")
        self.draw_cave()

        self.canvas.create_rectangle(
            WIDTH // 2 - 200,
            HEIGHT // 2 - 100,
            WIDTH // 2 + 200,
            HEIGHT // 2 + 100,
            fill="#111111",
            outline="cyan",
            width=3,
        )
        self.canvas.create_text(
            WIDTH // 2,
            HEIGHT // 2 - 50,
            text="CRASH!",
            fill="red",
            font=("Courier", 24, "bold"),
        )
        self.canvas.create_text(
            WIDTH // 2,
            HEIGHT // 2 - 10,
            text=f"Final Score: {self.score}",
            fill="white",
            font=("Courier", 16),
        )
        self.canvas.create_text(
            WIDTH // 2,
            HEIGHT // 2 + 20,
            text=f"High Score: {self.high_score}",
            fill="yellow",
            font=("Courier", 14),
        )
        self.canvas.create_text(
            WIDTH // 2,
            HEIGHT // 2 + 60,
            text="Click or Press SPACE to Restart",
            fill="cyan",
            font=("Courier", 11, "bold"),
        )


if __name__ == "__main__":
    root = tk.Tk()
    app = HelicopterGame(root)
    root.mainloop()

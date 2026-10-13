import random
import turtle

# --- Configuration Constants ---
SCREEN_WIDTH = 600
SCREEN_HEIGHT = 600
GRID_COORDS = [
    (-120, 120),
    (0, 120),
    (120, 120),
    (-120, 0),
    (0, 0),
    (120, 0),
    (-120, -120),
    (0, -120),
    (120, -120),
]
HOLE_RADIUS = 40
MOLE_SHOW_TIME = 800  # Duration the mole stays visible in milliseconds
SPAWN_INTERVAL = 1100  # How often a new mole tries to appear in milliseconds
GAME_DURATION = 30  # Total game time in seconds


class WhackAMoleGame:

    def __init__(self):
        # 1. Initialize Screen
        self.screen = turtle.Screen()
        self.screen.setup(width=SCREEN_WIDTH, height=SCREEN_HEIGHT)
        self.screen.title("Whack-a-Mole!")
        self.screen.bgcolor("forest green")
        self.screen.tracer(
            0
        )  # Turn off automatic updates for smoother drawing

        # 2. Game State Variables
        self.score = 0
        self.time_left = GAME_DURATION
        self.game_active = True
        self.current_mole_index = None
        self.mole_is_visible = False

        # 3. Setup Game Elements
        self.setup_holes()
        self.setup_mole()
        self.setup_scoreboard()

        # 4. Bind Click Events
        self.screen.onscreenclick(self.handle_click)

        # Update screen to render static elements
        self.screen.update()

        # 5. Start Timers
        self.screen.ontimer(self.pop_mole, SPAWN_INTERVAL)
        self.screen.ontimer(self.countdown, 1000)

    def setup_holes(self):
        """Draws the static holes on the board."""
        hole_drawer = turtle.Turtle()
        hole_drawer.hideturtle()
        hole_drawer.speed(0)
        hole_drawer.penup()

        for x, y in GRID_COORDS:
            hole_drawer.goto(x, y - HOLE_RADIUS)
            hole_drawer.pendown()
            hole_drawer.color("saddle brown", "sienna")
            hole_drawer.begin_fill()
            hole_drawer.circle(HOLE_RADIUS)
            hole_drawer.end_fill()
            hole_drawer.penup()

    def setup_mole(self):
        """Creates the mole turtle."""
        self.mole = turtle.Turtle()
        self.mole.hideturtle()
        self.mole.speed(0)
        self.mole.penup()
        # Create a simple representation for a mole (brown circle with eyes)
        self.mole.shape("circle")
        self.mole.color("peru")
        self.mole.shapesize(stretch_wid=2.2, stretch_len=2.2)

    def setup_scoreboard(self):
        """Creates the scoreboard turtle to display score and time."""
        self.scoreboard = turtle.Turtle()
        self.scoreboard.hideturtle()
        self.scoreboard.speed(0)
        self.scoreboard.penup()
        self.scoreboard.color("white")
        self.update_scoreboard_display()

    def update_scoreboard_display(self):
        """Refreshes the text shown on the scoreboard."""
        self.scoreboard.clear()
        self.scoreboard.goto(0, SCREEN_HEIGHT / 2 - 50)
        self.scoreboard.write(
            f"Score: {self.score}   Time Left: {self.time_left}s",
            align="center",
            font=("Arial", 20, "bold"),
        )

    def pop_mole(self):
        """Pops a mole up at a random grid location if the game is active."""
        if not self.game_active:
            return

        # Hide current mole if still visible
        self.mole.hideturtle()
        self.mole_is_visible = False

        # Pick a random hole
        self.current_mole_index = random.randint(0, len(GRID_COORDS) - 1)
        x, y = GRID_COORDS[self.current_mole_index]

        # Move and show mole
        self.mole.goto(x, y)
        self.mole.showturtle()
        self.mole_is_visible = True
        self.screen.update()

        # Schedule hiding the mole after MOLE_SHOW_TIME
        self.screen.ontimer(self.hide_mole, MOLE_SHOW_TIME)

        # Schedule the next mole appearance
        self.screen.ontimer(self.pop_mole, SPAWN_INTERVAL)

    def hide_mole(self):
        """Hides the mole if it's currently showing."""
        if self.mole_is_visible:
            self.mole.hideturtle()
            self.mole_is_visible = False
            self.screen.update()

    def handle_click(self, x, y):
        """Handles mouse clicks to check for 'whacking' the mole."""
        if not self.game_active or not self.mole_is_visible:
            return

        # Get current mole coordinates
        mole_x, mole_y = GRID_COORDS[self.current_mole_index]

        # Calculate Euclidean distance between click and mole
        distance = ((x - mole_x) ** 2 + (y - mole_y) ** 2) ** 0.5

        # If clicked within the radius of the active mole, score a point
        if distance < HOLE_RADIUS:
            self.score += 1
            self.mole_is_visible = False
            self.mole.hideturtle()
            self.update_scoreboard_display()
            self.screen.update()

    def countdown(self):
        """Manages the overall game timer."""
        if self.time_left > 0:
            self.time_left -= 1
            self.update_scoreboard_display()
            self.screen.update()
            self.screen.ontimer(self.countdown, 1000)
        else:
            self.end_game()

    def end_game(self):
        """Ends the game, hides the mole, and displays the final score."""
        self.game_active = False
        self.mole.hideturtle()
        self.screen.update()

        # Display Game Over message
        game_over_turtle = turtle.Turtle()
        game_over_turtle.hideturtle()
        game_over_turtle.color("yellow")
        game_over_turtle.goto(0, 0)
        game_over_turtle.write(
            f"GAME OVER!\nFinal Score: {self.score}",
            align="center",
            font=("Arial", 28, "bold"),
        )
        self.screen.update()


def main():
    game = WhackAMoleGame()
    turtle.mainloop()


if __name__ == "__main__":
    main()

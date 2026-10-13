<!-- Task T2: Write the complete Python code for the 'Dodge the Blocks' game using the turtle module based on the researched mechanics. -->

```python
import turtle
import random

# --- Constants ---
SCREEN_WIDTH = 600
SCREEN_HEIGHT = 700
FPS_DELAY = 16  # ~60 FPS (16ms)

# --- Classes ---

class Player:
    """Encapsulates the player character (the dodger)."""
    def __init__(self):
        self.turtle = turtle.Turtle()
        self.turtle.shape("square")
        self.turtle.color("#00ffff")
        self.turtle.shapesize(stretch_wid=1, stretch_len=3)  # Width: 60, Height: 20
        self.turtle.penup()
        self.turtle.goto(0, -250)
        self.step_size = 35
        self.min_x = -SCREEN_WIDTH // 2 + 40
        self.max_x = SCREEN_WIDTH // 2 - 40

    def move_left(self):
        new_x = self.turtle.xcor() - self.step_size
        if new_x >= self.min_x:
            self.turtle.setx(new_x)

    def move_right(self):
        new_x = self.turtle.xcor() + self.step_size
        if new_x <= self.max_x:
            self.turtle.setx(new_x)

    def reset(self):
        self.turtle.goto(0, -250)
        self.turtle.showturtle()

    def hide(self):
        self.turtle.hideturtle()


class BlockManager:
    """Manages spawning, moving, and recycling of falling obstacle blocks."""
    def __init__(self, num_blocks=6):
        self.num_blocks = num_blocks
        self.blocks = []
        self.base_speed = 4
        self.current_speed = self.base_speed
        self._init_blocks()

    def _init_blocks(self):
        for _ in range(self.num_blocks):
            b = turtle.Turtle()
            b.shape("square")
            b.color("#ff3366")
            b.shapesize(stretch_wid=1.2, stretch_len=2)  # Width: 40, Height: 24
            b.penup()
            self.respawn_block(b, initial=True)
            self.blocks.append(b)

    def respawn_block(self, block, initial=False):
        x = random.randint(-SCREEN_WIDTH // 2 + 30, SCREEN_WIDTH // 2 - 30)
        if initial:
            # Stagger initial heights so they don't all clump together
            y = random.randint(SCREEN_HEIGHT // 2, SCREEN_HEIGHT // 2 + 400)
        else:
            y = SCREEN_HEIGHT // 2 + random.randint(20, 100)
        block.goto(x, y)

    def update(self, score):
        # Scale speed slightly as score increases
        self.current_speed = self.base_speed + (score // 10) * 0.5
        
        for block in self.blocks:
            y = block.ycor() - self.current_speed
            block.sety(y)
            # If block goes past bottom, recycle to top
            if y < -SCREEN_HEIGHT // 2 - 30:
                self.respawn_block(block)

    def check_collision(self, player_turtle):
        for block in self.blocks:
            # Using turtle's built-in bounding distance check
            if block.distance(player_turtle) < 30:
                return True
        return False

    def reset_all(self):
        self.current_speed = self.base_speed
        for block in self.blocks:
            self.respawn_block(block, initial=True)

    def hide_all(self):
        for block in self.blocks:
            block.hideturtle()

    def show_all(self):
        for block in self.blocks:
            block.showturtle()


class Scoreboard:
    """Manages score tracking, high score, and on-screen text rendering."""
    def __init__(self):
        self.score = 0
        self.high_score = 0
        
        self.writer = turtle.Turtle()
        self.writer.hideturtle()
        self.writer.penup()
        self.writer.color("white")

    def update_score(self):
        self.score += 1
        if self.score > self.high_score:
            self.high_score = self.score

    def display(self, game_state):
        self.writer.clear()
        if game_state == "PLAYING":
            self.writer.goto(0, SCREEN_HEIGHT // 2 - 50)
            self.writer.write(
                f"Score: {self.score}   High Score: {self.high_score}",
                align="center",
                font=("Courier", 18, "bold")
            )
        elif game_state == "GAME_OVER":
            self.writer.goto(0, 40)
            self.writer.write(
                "GAME OVER",
                align="center",
                font=("Courier", 32, "bold")
            )
            self.writer.goto(0, -10)
            self.writer.write(
                f"Final Score: {self.score}",
                align="center",
                font=("Courier", 18, "normal")
            )
            self.writer.goto(0, -60)
            self.writer.write(
                "Press SPACE to Restart or ESC to Quit",
                align="center",
                font=("Courier", 14, "normal")
            )

    def reset(self):
        self.score = 0


class Game:
    """Main game controller handling loop, state transitions, and inputs."""
    def __init__(self):
        # Screen Setup
        self.screen = turtle.Screen()
        self.screen.setup(width=SCREEN_WIDTH, height=SCREEN_HEIGHT)
        self.screen.title("Dodge the Blocks")
        self.screen.bgcolor("#1a1a1a")
        self.screen.tracer(0)  # Disable auto-updates for manual frame management

        # Game States: START, PLAYING, GAME_OVER
        self.state = "START"

        # Initialize Components
        self.player = Player()
        self.block_manager = BlockManager(num_blocks=7)
        self.scoreboard = Scoreboard()

        # Frame counter for score progression based on survival time
        self.frame_counter = 0

        # Bind Controls
        self.bind_keys()
        
        # Show initial start message
        self.show_start_screen()

    def bind_keys(self):
        self.screen.listen()
        self.screen.onkey(self.player.move_left, "Left")
        self.screen.onkey(self.player.move_left, "a")
        self.screen.onkey(self.player.move_right, "Right")
        self.screen.onkey(self.player.move_right, "d")
        self.screen.onkey(self.handle_space, "space")
        self.screen.onkey(self.screen.bye, "Escape")

    def show_start_screen(self):
        self.player.hide()
        self.block_manager.hide_all()
        self.scoreboard.writer.goto(0, 20)
        self.scoreboard.writer.write(
            "DODGE THE BLOCKS",
            align="center",
            font=("Courier", 28, "bold")
        )
        self.scoreboard.writer.goto(0, -20)
        self.scoreboard.writer.write(
            "Use Left/Right Arrows or A/D to move",
            align="center",
            font=("Courier", 12, "normal")
        )
        self.scoreboard.writer.goto(0, -60)
        self.scoreboard.writer.write(
            "Press SPACE to Start",
            align="center",
            font=("Courier", 16, "bold")
        )
        self.screen.update()

    def start_game(self):
        self.state = "PLAYING"
        self.scoreboard.reset()
        self.player.reset()
        self.block_manager.reset_all()
        self.block_manager.show_all()
        self.frame_counter = 0
        self.game_loop()

    def handle_space(self):
        if self.state == "START" or self.state == "GAME_OVER":
            self.start_game()

    def game_loop(self):
        if self.state != "PLAYING":
            return

        # Increment score every ~30 frames (approx. twice a second)
        self.frame_counter += 1
        if self.frame_counter >= 30:
            self.scoreboard.update_score()
            self.frame_counter = 0

        # Update game objects
        self.block_manager.update(self.scoreboard.score)

        # Check for collisions
        if self.block_manager.check_collision(self.player.turtle):
            self.state = "GAME_OVER"
            self.player.hide()
            self.block_manager.hide_all()
            self.scoreboard.display("GAME_OVER")
            self.screen.update()
            return

        # Render frame
        self.scoreboard.display("PLAYING")
        self.screen.update()

        # Schedule next frame
        self.screen.ontimer(self.game_loop, FPS_DELAY)

    def run(self):
        self.screen.mainloop()


# --- Execution ---
if __name__ == "__main__":
    game = Game()
    game.run()
```

### Usage Note
1. Ensure Python is installed along with the built-in `turtle` module (standard on most Python installations).
2. Save the code into a file named `dodge_blocks.py`.
3. Run the script using your terminal: `python dodge_blocks.py`.
4. **Controls:**
   - **Left Arrow** or **A**: Move left.
   - **Right Arrow** or **D**: Move right.
   - **Spacebar**: Start / Restart the game.
   - **Escape**: Quit the application.

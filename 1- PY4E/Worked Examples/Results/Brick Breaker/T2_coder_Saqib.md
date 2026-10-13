<!-- Task T2: Write the complete Python code for a Brick Breaker game using the turtle module based on the research. -->

```python
import turtle
import time

# Constants
SCREEN_WIDTH = 600
SCREEN_HEIGHT = 700
FPS = 60
FRAME_DELAY = int(1000 / FPS)

class Paddle:
    """Represents the player's paddle at the bottom of the screen."""
    def __init__(self, screen):
        self.screen = screen
        self.width = 100
        self.height = 20
        
        self.turtle = turtle.Turtle()
        self.turtle.shape("square")
        self.turtle.color("blue")
        # turtle square is default 20x20. scale it to width x height
        self.turtle.shapesize(stretch_wid=self.height / 20, stretch_len=self.width / 20)
        self.turtle.penup()
        self.turtle.goto(0, -250)
        
        # Movement flags
        self.moving_left = False
        self.moving_right = False
        self.speed = 10

    def start_left(self):
        self.moving_left = True

    def stop_left(self):
        self.moving_left = False

    def start_right(self):
        self.moving_right = True

    def stop_right(self):
        self.moving_right = False

    def update(self):
        x = self.turtle.xcor()
        if self.moving_left and not self.moving_right:
            x -= self.speed
        if self.moving_right and not self.moving_left:
            x += self.speed
            
        # Constrain within screen bounds
        half_width = self.width / 2
        min_x = -SCREEN_WIDTH / 2 + half_width
        max_x = SCREEN_WIDTH / 2 - half_width
        
        if x < min_x:
            x = min_x
        elif x > max_x:
            x = max_x
            
        self.turtle.setx(x)

    def get_bbox(self):
        """Returns Axis-Aligned Bounding Box (AABB): (left, top, right, bottom)"""
        x = self.turtle.xcor()
        y = self.turtle.ycor()
        half_w = self.width / 2
        half_h = self.height / 2
        return (x - half_w, y + half_h, x + half_w, y - half_h)


class Ball:
    """Represents the ball that bounces around and breaks bricks."""
    def __init__(self):
        self.radius = 10
        self.turtle = turtle.Turtle()
        self.turtle.shape("circle")
        self.turtle.color("white")
        # circle default is 20x20 diameter
        self.turtle.shapesize(stretch_wid=self.radius / 10, stretch_len=self.radius / 10)
        self.turtle.penup()
        self.reset_position()

    def reset_position(self):
        self.turtle.goto(0, -200)
        self.dx = 4
        self.dy = -4

    def move(self):
        self.turtle.setx(self.turtle.xcor() + self.dx)
        self.turtle.sety(self.turtle.ycor() + self.dy)

    def bounce_x(self):
        self.dx = -self.dx

    def bounce_y(self):
        self.dy = -self.dy

    def get_bbox(self):
        """Returns AABB: (left, top, right, bottom)"""
        x = self.turtle.xcor()
        y = self.turtle.ycor()
        return (x - self.radius, y + self.radius, x + self.radius, y - self.radius)


class BrickManager:
    """Manages the grid of bricks at the top of the screen."""
    def __init__(self):
        self.bricks = []
        self.brick_width = 60
        self.brick_height = 20
        self.create_grid()

    def create_grid(self):
        rows = 5
        cols = 8
        colors = ["red", "orange", "yellow", "green", "cyan"]
        
        start_x = - (cols * self.brick_width) / 2 + self.brick_width / 2
        start_y = 250

        for row in range(rows):
            color = colors[row % len(colors)]
            for col in range(cols):
                x = start_x + col * self.brick_width
                y = start_y - row * self.brick_height
                
                t = turtle.Turtle()
                t.shape("square")
                t.color(color)
                t.shapesize(stretch_wid=self.brick_height / 20, stretch_len=self.brick_width / 20)
                t.penup()
                t.goto(x, y)
                
                self.bricks.append({
                    "turtle": t,
                    "x": x,
                    "y": y,
                    "width": self.brick_width,
                    "height": self.brick_height,
                    "active": True
                })

    def check_collision(self, ball):
        """Checks for AABB collision between ball and active bricks."""
        bx1, by1, bx2, by2 = ball.get_bbox()
        
        for brick in self.bricks:
            if not brick["active"]:
                continue
                
            bx = brick["x"]
            by = brick["y"]
            bw = brick["width"]
            bh = brick["height"]
            
            # Brick AABB
            rx1 = bx - bw / 2
            ry1 = by + bh / 2
            rx2 = bx + bw / 2
            ry2 = by - bh / 2
            
            # Check intersection
            if bx2 >= rx1 and bx1 <= rx2 and by1 >= ry2 and by2 <= ry1:
                brick["active"] = False
                brick["turtle"].hideturtle()
                return True
        return False

    def all_cleared(self):
        for brick in self.bricks:
            if brick["active"]:
                return False
        return True


class GameManager:
    """Manages game state, score, lives, and text displays."""
    def __init__(self):
        self.score = 0
        self.lives = 3
        self.state = "RUNNING" # RUNNING, WON, GAMEOVER
        
        self.writer = turtle.Turtle()
        self.writer.hideturtle()
        self.writer.color("white")
        self.writer.penup()
        self.update_hud()

    def update_hud(self):
        self.writer.clear()
        self.writer.goto(-SCREEN_WIDTH / 2 + 20, SCREEN_HEIGHT / 2 - 40)
        self.writer.write(f"Score: {self.score}  Lives: {self.lives}", font=("Arial", 14, "normal"))

    def display_message(self, message):
        self.writer.goto(0, 0)
        self.writer.write(message, align="center", font=("Arial", 24, "bold"))


class Game:
    """Main game engine handling loops, inputs, and updates."""
    def __init__(self):
        self.screen = turtle.Screen()
        self.screen.setup(width=SCREEN_WIDTH, height=SCREEN_HEIGHT)
        self.screen.bgcolor("black")
        self.screen.title("Brick Breaker - Turtle")
        self.screen.tracer(0)

        self.paddle = Paddle(self.screen)
        self.ball = Ball()
        self.brick_manager = BrickManager()
        self.manager = GameManager()

        # Keyboard bindings (using onkey / onkeyrelease for smooth continuous movement)
        self.screen.listen()
        self.screen.onkey(self.paddle.start_left, "Left")
        self.screen.onkeyrelease(self.paddle.stop_left, "Left")
        self.screen.onkey(self.paddle.start_right, "Right")
        self.screen.onkeyrelease(self.paddle.stop_right, "Right")

        self.running = True

    def run(self):
        """Main game loop driven by screen.ontimer for smooth timing."""
        if not self.running:
            return

        if self.manager.state == "RUNNING":
            # Update positions
            self.paddle.update()
            self.ball.move()

            # Wall Collisions (Left / Right)
            bx1, by1, bx2, by2 = self.ball.get_bbox()
            if bx1 <= -SCREEN_WIDTH / 2 or bx2 >= SCREEN_WIDTH / 2:
                self.ball.bounce_x()

            # Wall Collision (Top)
            if by1 >= SCREEN_HEIGHT / 2:
                self.ball.bounce_y()

            # Bottom Collision (Lose Life)
            if by2 <= -SCREEN_HEIGHT / 2:
                self.manager.lives -= 1
                self.manager.update_hud()
                if self.manager.lives <= 0:
                    self.manager.state = "GAMEOVER"
                    self.manager.display_message("GAME OVER\nPress 'R' to Restart")
                    self.screen.onkey(self.restart, "r")
                    self.screen.onkey(self.restart, "R")
                else:
                    self.ball.reset_position()

            # Paddle Collision
            px1, py1, px2, py2 = self.paddle.get_bbox()
            if bx2 >= px1 and bx1 <= px2 and by2 <= py1 and by1 >= py2:
                if self.ball.dy < 0: # Ensure it only bounces upward if falling
                    self.ball.bounce_y()
                    # Add English/spin based on where it hit the paddle
                    offset = self.ball.turtle.xcor() - self.paddle.turtle.xcor()
                    self.ball.dx += offset * 0.05

            # Brick Collision
            if self.brick_manager.check_collision(self.ball):
                self.ball.bounce_y()
                self.manager.score += 10
                self.manager.update_hud()
                
                if self.brick_manager.all_cleared():
                    self.manager.state = "WON"
                    self.manager.display_message("YOU WIN!\nPress 'R' to Restart")
                    self.screen.onkey(self.restart, "r")
                    self.screen.onkey(self.restart, "R")

        self.screen.update()
        self.screen.ontimer(self.run, FRAME_DELAY)

    def restart(self):
        """Resets the game state completely."""
        # Clear existing bricks
        for brick in self.brick_manager.bricks:
            brick["turtle"].hideturtle()
        
        self.brick_manager = BrickManager()
        self.ball.reset_position()
        self.manager.score = 0
        self.manager.lives = 3
        self.manager.state = "RUNNING"
        self.manager.update_hud()
        
        # Re-bind controls just in case
        self.screen.onkey(None, "r")
        self.screen.onkey(None, "R")
        
        # Kick start loop again if stopped
        self.run()


if __name__ == "__main__":
    game = Game()
    game.run()
    turtle.mainloop()
```

### Usage Note
1. Run the script using Python: `python <script_name>.py`
2. **Controls:** Use the **Left** and **Right Arrow keys** to move the paddle and bounce the ball to clear all colored bricks.
3. If you lose all 3 lives or clear all bricks, you can press **'R'** to restart the game.

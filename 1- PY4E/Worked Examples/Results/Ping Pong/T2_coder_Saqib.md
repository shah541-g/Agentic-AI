<!-- Task T2: Write the complete Python code for the Pong game using the turtle module based on the research. -->

```python
import time
import turtle

# --- Screen Setup ---
screen = turtle.Screen()
screen.title("Pong Game - Turtle Graphics")
screen.bgcolor("black")
screen.setup(width=800, height=600)
screen.tracer(0)  # Turns off automatic screen updates for manual frame control

# --- Center Divider ---
divider = turtle.Turtle()
divider.color("white")
divider.penup()
divider.goto(0, 300)
divider.setheading(270)
divider.pensize(2)
for _ in range(15):
    divider.pendown()
    divider.forward(20)
    divider.penup()
    divider.forward(20)
divider.hideturtle()

# --- Left Paddle ---
left_paddle = turtle.Turtle()
left_paddle.speed(0)
left_paddle.shape("square")
left_paddle.color("white")
left_paddle.shapesize(stretch_wid=5, stretch_len=1)  # 100px high, 20px wide
left_paddle.penup()
left_paddle.goto(-350, 0)

# --- Right Paddle ---
right_paddle = turtle.Turtle()
right_paddle.speed(0)
right_paddle.shape("square")
right_paddle.color("white")
right_paddle.shapesize(stretch_wid=5, stretch_len=1)
right_paddle.penup()
right_paddle.goto(350, 0)

# --- Ball ---
ball = turtle.Turtle()
ball.speed(0)
ball.shape("square")
ball.color("white")
ball.penup()
ball.goto(0, 0)
# Ball velocity vector (speed multiplier)
ball.dx = 4
ball.dy = 4

# --- Scoreboard ---
score_display = turtle.Turtle()
score_display.speed(0)
score_display.color("white")
score_display.penup()
score_display.hideturtle()
score_display.goto(0, 240)
score_display.write(
    "0 : 0", align="center", font=("Courier", 36, "normal")
)

score_left = 0
score_right = 0


# --- Paddle Movement Functions ---
def left_paddle_up():
    y = left_paddle.ycor()
    if y < 240:
        left_paddle.sety(y + 20)


def left_paddle_down():
    y = left_paddle.ycor()
    if y > -240:
        left_paddle.sety(y - 20)


def right_paddle_up():
    y = right_paddle.ycor()
    if y < 240:
        right_paddle.sety(y + 20)


def right_paddle_down():
    y = right_paddle.ycor()
    if y > -240:
        right_paddle.sety(y - 20)


# --- Keyboard Bindings ---
screen.listen()
# Left player controls: W and S
screen.onkeypress(left_paddle_up, "w")
screen.onkeypress(left_paddle_down, "s")
# Right player controls: Up and Down arrow keys
screen.onkeypress(right_paddle_up, "Up")
screen.onkeypress(right_paddle_down, "Down")


# --- Helper Function to Update Scores ---
def update_scoreboard():
    score_display.clear()
    score_display.write(
        f"{score_left} : {score_right}",
        align="center",
        font=("Courier", 36, "normal"),
    )


# --- Main Game Loop ---
game_is_on = True

while game_is_on:
    screen.update()
    time.sleep(1 / 60)  # Cap frame rate at ~60 FPS

    # Move the ball
    ball.setx(ball.xcor() + ball.dx)
    ball.sety(ball.ycor() + ball.dy)

    # --- Border Collision (Top & Bottom) ---
    if ball.ycor() > 290:
        ball.sety(290)
        ball.dy *= -1

    if ball.ycor() < -290:
        ball.sety(-290)
        ball.dy *= -1

    # --- Scoring (Left & Right Walls) ---
    if ball.xcor() > 390:
        ball.goto(0, 0)
        ball.dx *= -1  # Serve toward the player who conceded
        score_left += 1
        update_scoreboard()

    if ball.xcor() < -390:
        ball.goto(0, 0)
        ball.dx *= -1
        score_right += 1
        update_scoreboard()

    # --- Paddle Collisions ---
    # Right Paddle Collision
    if (
        340 < ball.xcor() < 350
        and (right_paddle.ycor() - 50 < ball.ycor() < right_paddle.ycor() + 50)
    ):
        ball.setx(340)
        ball.dx *= -1

    # Left Paddle Collision
    if (
        -350 < ball.xcor() < -340
        and (left_paddle.ycor() - 50 < ball.ycor() < left_paddle.ycor() + 50)
    ):
        ball.setx(-340)
        ball.dx *= -1
```

### Usage Note

1. Ensure you have Python installed with the built-in `turtle` module.
2. Save the code into a file named `pong.py`.
3. Run the script using the command: `python pong.py`
4. **Controls:**
   * **Player 1 (Left Paddle):** Press **W** to move up, **S** to move down.
   * **Player 2 (Right Paddle):** Press the **Up Arrow** to move up, **Down Arrow** to move down.
5. Close the game window to exit.

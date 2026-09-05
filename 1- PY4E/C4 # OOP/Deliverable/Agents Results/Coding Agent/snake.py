import turtle
import time
import random

# System Design & Constants
WINDOW_WIDTH = 600
WINDOW_HEIGHT = 600
DELAY = 0.1
GRID_SIZE = 20

class GameModel:
    def __init__(self):
        self.snake = [[0, 0], [20, 0], [40, 0]]
        self.direction = "stop"
        self.food = [0, 0]
        self.score = 0
        self.high_score = 0
        self.spawn_food()

    def spawn_food(self):
        x = random.randint(int(-WINDOW_WIDTH/2 + GRID_SIZE), int(WINDOW_WIDTH/2 - GRID_SIZE))
        y = random.randint(int(-WINDOW_HEIGHT/2 + GRID_SIZE), int(WINDOW_HEIGHT/2 - GRID_SIZE))
        # Align to grid
        self.food = [x - (x % GRID_SIZE), y - (y % GRID_SIZE)]

    def move_snake(self):
        head = list(self.snake[-1])
        if self.direction == 'up':
            head[1] += GRID_SIZE
        elif self.direction == 'down':
            head[1] -= GRID_SIZE
        elif self.direction == 'left':
            head[0] -= GRID_SIZE
        elif self.direction == 'right':
            head[0] += GRID_SIZE

        if self.direction != 'stop':
            self.snake.append(head)
            if not self.check_food_collision():
                self.snake.pop(0)

    def check_food_collision(self):
        if self.snake[-1] == self.food:
            self.score += 10
            if self.score > self.high_score:
                self.high_score = self.score
            self.spawn_food()
            return True
        return False

    def check_wall_collision(self):
        head = self.snake[-1]
        return (head[0] > WINDOW_WIDTH/2 - GRID_SIZE or 
                head[0] < -WINDOW_WIDTH/2 or 
                head[1] > WINDOW_HEIGHT/2 or 
                head[1] < -WINDOW_HEIGHT/2 + GRID_SIZE)

    def check_self_collision(self):
        head = self.snake[-1]
        for segment in self.snake[:-1]:
            if segment == head:
                return True
        return False

    def reset(self):
        time.sleep(1)
        self.snake = [[0, 0], [20, 0], [40, 0]]
        self.direction = 'stop'
        self.score = 0
        self.spawn_food()


class GameView:
    def __init__(self):
        self.screen = turtle.Screen()
        self.screen.title("Ahmad's Python Snake Game")
        self.screen.setup(width=WINDOW_WIDTH, height=WINDOW_HEIGHT)
        self.screen.bgcolor('black')
        self.screen.tracer(0)

        # Snake head/body turtle renderer pool
        self.segments = []
        
        # Food turtle
        self.food_turtle = turtle.Turtle()
        self.food_turtle.speed(0)
        self.food_turtle.shape('square')
        self.food_turtle.color('red')
        self.food_turtle.penup()

        # Scoreboard turtle
        self.score_turtle = turtle.Turtle()
        self.score_turtle.speed(0)
        self.score_turtle.color('white')
        self.score_turtle.penup()
        self.score_turtle.hideturtle()
        self.score_turtle.goto(0, WINDOW_HEIGHT / 2 - 40)

    def update_score(self, score, high_score):
        self.score_turtle.clear()
        self.score_turtle.write(f'Score: {score}  High Score: {high_score}', 
                                align='center', font=('Courier', 24, 'normal'))

    def render(self, model):
        # Adjust segment count
        while len(self.segments) < len(model.snake):
            seg = turtle.Turtle()
            seg.speed(0)
            seg.shape('square')
            seg.color('green')
            seg.penup()
            self.segments.append(seg)

        for seg in self.segments[len(model.snake):]:
            seg.goto(1000, 1000) # Hide extra segments offscreen

        # Draw snake
        for index, segment in enumerate(model.snake):
            self.segments[index].goto(segment[0], segment[1])

        # Draw food
        self.food_turtle.goto(model.food[0], model.food[1])
        
        self.update_score(model.score, model.high_score)
        self.screen.update()

    def bind_keys(self, controller):
        self.screen.listen()
        self.screen.onkey(controller.go_up, 'Up')
        self.screen.onkey(controller.go_down, 'Down')
        self.screen.onkey(controller.go_left, 'Left')
        self.screen.onkey(controller.go_right, 'Right')


class GameController:
    def __init__(self, model, view):
        self.model = model
        self.view = view
        self.view.bind_keys(self)

    def go_up(self):
        if self.model.direction != 'down':
            self.model.direction = 'up'

    def go_down(self):
        if self.model.direction != 'up':
            self.model.direction = 'down'

    def go_left(self):
        if self.model.direction != 'right':
            self.model.direction = 'left'

    def go_right(self):
        if self.model.direction != 'left':
            self.model.direction = 'right'

    def run(self):
        while True:
            self.view.screen.update()
            
            if self.model.check_wall_collision() or self.model.check_self_collision():
                self.model.reset()

            self.model.move_snake()
            self.view.render(self.model)
            
            time.sleep(DELAY)

if __name__ == '__main__':
    game_model = GameModel()
    game_view = GameView()
    game_controller = GameController(game_model, game_view)
    game_controller.run()
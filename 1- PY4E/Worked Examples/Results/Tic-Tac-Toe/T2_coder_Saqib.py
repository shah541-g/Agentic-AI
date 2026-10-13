import turtle

class TicTacToe:
    def __init__(self):
        # Setup screen
        self.screen = turtle.Screen()
        self.screen.title("Tic-Tac-Toe")
        self.screen.setup(width=600, height=600)
        self.screen.bgcolor("#f0f0f0")
        self.screen.tracer(0)  # Manual screen updates for instant rendering

        # Game state
        self.board = [["" for _ in range(3)] for _ in range(3)]
        self.current_player = "X"
        self.game_over = False

        # Drawing turtle
        self.t = turtle.Turtle()
        self.t.hideturtle()
        self.t.speed(0)

        # Status display turtle
        self.status_t = turtle.Turtle()
        self.status_t.hideturtle()
        self.status_t.speed(0)

        # Draw the initial board
        self.draw_grid()
        self.update_status(f"Player {self.current_player}'s turn")

        # Bind mouse click event
        self.screen.onclick(self.handle_click)
        self.screen.listen()

    def draw_grid(self):
        """Draws the 3x3 Tic-Tac-Toe grid lines."""
        self.t.clear()
        self.t.pensize(4)
        self.t.pencolor("#333333")

        # Vertical lines
        for x in (-100, 100):
            self.t.penup()
            self.t.goto(x, -300)
            self.t.pendown()
            self.t.goto(x, 300)

        # Horizontal lines
        for y in (-100, 100):
            self.t.penup()
            self.t.goto(-300, y)
            self.t.pendown()
            self.t.goto(300, y)
            
        self.screen.update()

    def update_status(self, message):
        """Displays status messages at the top of the window."""
        self.status_t.clear()
        self.status_t.penup()
        self.status_t.goto(0, 250)
        self.status_t.pencolor("#111111")
        self.status_t.write(message, align="center", font=("Arial", 18, "bold"))
        self.screen.update()

    def draw_x(self, row, col):
        """Draws an 'X' in the specified cell."""
        center_x = (col - 1) * 200
        center_y = (1 - row) * 200
        offset = 60

        self.t.pensize(5)
        self.t.pencolor("#e74c3c")  # Red for X

        # First diagonal line
        self.t.penup()
        self.t.goto(center_x - offset, center_y - offset)
        self.t.pendown()
        self.t.goto(center_x + offset, center_y + offset)

        # Second diagonal line
        self.t.penup()
        self.t.goto(center_x - offset, center_y + offset)
        self.t.pendown()
        self.t.goto(center_x + offset, center_y - offset)
        
        self.screen.update()

    def draw_o(self, row, col):
        """Draws an 'O' in the specified cell."""
        center_x = (col - 1) * 200
        center_y = (1 - row) * 200
        radius = 60

        self.t.pensize(5)
        self.t.pencolor("#3498db")  # Blue for O

        self.t.penup()
        # turtle circle starts drawing from bottom of the circle
        self.t.goto(center_x, center_y - radius)
        self.t.pendown()
        self.t.circle(radius)
        
        self.screen.update()

    def handle_click(self, x, y):
        """Handles mouse click events, validating and mapping them to board coordinates."""
        if self.game_over:
            return

        # Map continuous (x, y) coordinates to discrete grid indices (row, col)
        if x < -100:
            col = 0
        elif x <= 100:
            col = 1
        else:
            col = 2

        if y > 100:
            row = 0
        elif y >= -100:
            row = 1
        else:
            row = 2

        # Check if the clicked cell is within bounds and empty
        if 0 <= row < 3 and 0 <= col < 3:
            if self.board[row][col] == "":
                self.board[row][col] = self.current_player

                # Draw move
                if self.current_player == "X":
                    self.draw_x(row, col)
                else:
                    self.draw_o(row, col)

                # Check for win or tie
                if self.check_win(self.current_player):
                    self.update_status(f"Player {self.current_player} Wins!")
                    self.game_over = True
                elif self.check_tie():
                    self.update_status("It's a Tie!")
                    self.game_over = True
                else:
                    # Switch turn
                    self.current_player = "O" if self.current_player == "X" else "X"
                    self.update_status(f"Player {self.current_player}'s turn")

    def check_win(self, player):
        """Checks if the specified player has won the game."""
        b = self.board
        # Check rows
        for r in range(3):
            if b[r][0] == b[r][1] == b[r][2] == player:
                return True
        # Check columns
        for c in range(3):
            if b[0][c] == b[1][c] == b[2][c] == player:
                return True
        # Check diagonals
        if b[0][0] == b[1][1] == b[2][2] == player:
            return True
        if b[0][2] == b[1][1] == b[2][0] == player:
            return True
        return False

    def check_tie(self):
        """Checks if the board is completely full resulting in a tie."""
        for row in self.board:
            if "" in row:
                return False
        return True

    def run(self):
        """Starts the turtle main event loop."""
        turtle.mainloop()

if __name__ == "__main__":
    game = TicTacToe()
    game.run()

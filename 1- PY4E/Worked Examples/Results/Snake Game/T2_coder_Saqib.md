<!-- Task T2: Write the C++ source code for the console-based Snake game, implementing the game loop, snake movement, collision detection, food generation, and score tracking based on the research. -->

```cpp
#include <iostream>
#include <vector>
#include <deque>
#include <cstdlib>
#include <ctime>
#include <chrono>
#include <thread>

// Platform-specific headers and input handling
#if defined(_WIN32) || defined(_WIN64)
    #include <conio.h>
    #include <windows.h>
    
    // Clear screen for Windows without flashing using ANSI escape sequences
    void clearScreen() {
        std::cout << "\033[H";
    }
    
    void setupConsole() {
        // Enable ANSI escape sequences on Windows 10+
        HANDLE hOut = GetStdHandle(STD_OUTPUT_HANDLE);
        if (hOut != INVALID_HANDLE_VALUE) {
            DWORD dwMode = 0;
            if (GetConsoleMode(hOut, &dwMode)) {
                dwMode |= ENABLE_VIRTUAL_TERMINAL_PROCESSING;
                SetConsoleMode(hOut, dwMode);
            }
        }
    }

    bool kbhit() {
        return _kbhit() != 0;
    }

    int getchChar() {
        return _getch();
    }

#else
    #include <unistd.h>
    #include <termios.h>
    #include <fcntl.h>

    void clearScreen() {
        std::cout << "\033[H";
    }

    // Configure terminal for non-blocking raw input on Linux/macOS
    void setupConsole() {
        termios term;
        tcgetattr(0, &term);
        term.c_lflag &= ~ICANON; // Disable canonical mode (line buffering)
        term.c_lflag &= ~ECHO;   // Disable character echo
        tcsetattr(0, TCSANOW, &term);
        fcntl(0, F_SETFL, O_NONBLOCK); // Set non-blocking read
    }

    bool kbhit() {
        char ch;
        int nread = read(0, &ch, 1);
        if (nread > 0) {
            // Push back or handle immediately? For simplicity in this loop, 
            // we read directly in getchChar if kbhit returns true.
            // A more robust buffer can be used, but standard single-char read works for simple games.
            return true;
        }
        return false;
    }

    int getchChar() {
        char ch = 0;
        if (read(0, &ch, 1) < 0) {
            return -1;
        }
        return ch;
    }
#endif

// Game Constants
const int WIDTH = 30;
const int HEIGHT = 20;

// Direction Enum
enum Direction { STOP = 0, UP, DOWN, LEFT, RIGHT };

struct Point {
    int x, y;
    bool operator==(const Point& other) const {
        return x == other.x && y == other.y;
    }
};

class SnakeGame {
private:
    bool gameOver;
    int score;
    int highScore;
    Direction dir;
    Point food;
    std::deque<Point> snake;
    int speedMs;

    void spawnFood() {
        bool collision;
        do {
            collision = false;
            food.x = std::rand() % WIDTH;
            food.y = std::rand() % HEIGHT;
            
            // Ensure food doesn't spawn on the snake
            for (const auto& segment : snake) {
                if (segment == food) {
                    collision = true;
                    break;
                }
            }
        } while (collision);
    }

public:
    SnakeGame() {
        std::srand(static_cast<unsigned int>(std::time(nullptr)));
        highScore = 0;
        resetGame();
    }

    void resetGame() {
        gameOver = false;
        score = 0;
        dir = STOP;
        speedMs = 120; // Game tick delay in milliseconds

        // Initialize snake in the middle
        snake.clear();
        int startX = WIDTH / 2;
        int startY = HEIGHT / 2;
        snake.push_back({startX, startY});
        snake.push_back({startX - 1, startY});
        snake.push_back({startX - 2, startY});

        spawnFood();
    }

    void processInput() {
        if (kbhit()) {
            int ch = getchChar();
            
            // Handle arrow keys or WASD
            if (ch == 227 || ch == 0 || ch == 224) { 
                // Windows arrow key prefix handling
                ch = getchChar();
                switch (ch) {
                    case 72: if (dir != DOWN)  dir = UP;    break; // Up arrow
                    case 80: if (dir != UP)    dir = DOWN;  break; // Down arrow
                    case 75: if (dir != RIGHT) dir = LEFT;  break; // Left arrow
                    case 77: if (dir != LEFT)  dir = RIGHT; break; // Right arrow
                }
            } else {
                // Standard ASCII inputs (WASD / q)
                switch (ch) {
                    case 'w': case 'W': if (dir != DOWN)  dir = UP;    break;
                    case 's': case 'S': if (dir != UP)    dir = DOWN;  break;
                    case 'a': case 'A': if (dir != RIGHT) dir = LEFT;  break;
                    case 'd': case 'D': if (dir != LEFT)  dir = RIGHT; break;
                    case 'q': case 'Q': gameOver = true;               break;
                }
            }
        }
    }

    void update() {
        if (dir == STOP) return;

        // Calculate new head position based on direction
        Point newHead = snake.front();
        switch (dir) {
            case UP:    newHead.y--; break;
            case DOWN:  newHead.y++; break;
            case LEFT:  newHead.x--; break;
            case RIGHT: newHead.x++; break;
            default:                 break;
        }

        // Wall collision check (Game Over)
        if (newHead.x < 0 || newHead.x >= WIDTH || newHead.y < 0 || newHead.y >= HEIGHT) {
            gameOver = true;
            return;
        }

        // Self collision check
        for (const auto& segment : snake) {
            if (newHead == segment) {
                gameOver = true;
                return;
            }
        }

        // Move snake forward
        snake.push_front(newHead);

        // Check if food eaten
        if (newHead == food) {
            score += 10;
            if (score > highScore) highScore = score;
            spawnFood();
            
            // Slight speed increase every 50 points
            if (score % 50 == 0 && speedMs > 50) {
                speedMs -= 10;
            }
        } else {
            // Remove tail if no food eaten
            snake.pop_back();
        }
    }

    void render() {
        std::string buffer = "";
        
        // Build render buffer to minimize I/O flicker
        buffer += "==================================\n";
        buffer += "          C++ CONSOLE SNAKE       \n";
        buffer += "==================================\n";
        buffer += " Score: " + std::to_string(score) + "  | High Score: " + std::to_string(highScore) + "\n";
        
        // Top border
        buffer += "+";
        for (int i = 0; i < WIDTH; ++i) buffer += "-";
        buffer += "+\n";

        // Grid contents
        for (int y = 0; y < HEIGHT; ++y) {
            buffer += "|";
            for (int x = 0; x < WIDTH; ++x) {
                Point current{x, y};
                if (current == snake.front()) {
                    buffer += "O"; // Snake Head
                } else {
                    bool isBody = false;
                    for (size_t i = 1; i < snake.size(); ++i) {
                        if (snake[i] == current) {
                            buffer += "o"; // Snake Body
                            isBody = true;
                            break;
                        }
                    }
                    if (!isBody) {
                        if (current == food) {
                            buffer += "*"; // Food
                        } else {
                            buffer += " "; // Empty space
                        }
                    }
                }
            }
            buffer += "|\n";
        }

        // Bottom border
        buffer += "+";
        for (int i = 0; i < WIDTH; ++i) buffer += "-";
        buffer += "+\n";
        buffer += "Controls: W/A/S/D or Arrow Keys | Q to Quit\n";

        // Output complete frame in one call to reduce flicker
        clearScreen();
        std::cout << buffer;
    }

    bool isGameOver() const {
        return gameOver;
    }

    int getSpeed() const {
        return speedMs;
    }
};

int main() {
    setupConsole();
    
    // Hide terminal cursor using ANSI escape sequence
    std::cout << "\033[?25l";

    SnakeGame game;

    // Main Game Loop
    while (true) {
        game.processInput();
        game.update();
        game.render();

        if (game.isGameOver()) {
            std::cout << "\n==================================\n";
            std::cout << "           GAME OVER!             \n";
            std::cout << "==================================\n";
            std::cout << "Play again? (y/n): ";
            
            // Clear input buffer before asking to restart
            while(kbhit()) getchChar();
            
            char choice;
            // Blocking wait for restart decision
            #if defined(_WIN32) || defined(_WIN64)
                choice = _getch();
            else {
                // Restore canonical mode briefly for clean restart choice
                termios term, oldt;
                tcgetattr(0, &oldt);
                term = oldt;
                term.c_lflag |= ICANON | ECHO;
                tcsetattr(0, TCSANOW, &term);
                std::cin >> choice;
                tcsetattr(0, TCSANOW, &oldt);
                fcntl(0, F_SETFL, O_NONBLOCK);
            }

            if (choice == 'y' || choice == 'Y') {
                game.resetGame();
            } else {
                break;
            }
        }

        // Regulate frame rate / tick speed cross-platform
        std::this_thread::sleep_for(std::chrono::milliseconds(game.getSpeed()));
    }

    // Restore terminal cursor on exit
    std::cout << "\033[?25h";
    std::cout << "Thanks for playing!\n";

    return 0;
}
```

### Usage Note

1. **Compilation:**
   * **Windows (MSVC / MinGW):** Compile directly using your preferred C++ compiler (requires C++11 or higher).
     ```bash
     g++ -std=c++11 snake.cpp -o snake.exe
     ```
   * **Linux / macOS:** Compile using `g++` or `clang++`:
     ```bash
     g++ -std=c++11 snake.cpp -o snake
     ```

2. **Execution:**
   Run the executable from your terminal window:
   ```bash
   ./snake       # On Linux / macOS
   snake.exe     # On Windows
   ```

3. **Controls:**
   * Use **W, A, S, D** or the **Arrow Keys** to change direction.
   * Press **Q** at any time to quit the game.

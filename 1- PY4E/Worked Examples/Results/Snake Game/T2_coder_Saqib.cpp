#include <iostream>
#include <vector>
#include <deque>
#include <chrono>
#include <thread>
#include <random>
#include <string>
#include <cstddef>
#include <windows.h>

#if defined(_WIN32) || defined(_WIN64)
    #include <conio.h>
    #include <windows.h>
    #define PLATFORM_WINDOWS
#else
    #include <termios.h>
    #include <unistd.h>
    #include <fcntl.h>
    #define PLATFORM_UNIX
#endif

// Game Constants
constexpr int WIDTH = 40;
constexpr int HEIGHT = 20;

// Direction Enumeration
enum class Direction {
    UP, DOWN, LEFT, RIGHT
};

// 2D Point
struct Point {
    int x, y;

    bool operator==(const Point& other) const {
        return x == other.x && y == other.y;
    }
};

// Input Manager
class InputManager {
#ifdef PLATFORM_UNIX
private:
    static inline termios originalTerminal{};
    static inline int originalFlags = -1;
    static inline bool terminalConfigured = false;
#endif

public:
    static void SetupTerminal() {
#ifdef PLATFORM_WINDOWS
    // No special terminal configuration required.
    // The game can still use standard console output.
#else
        if (tcgetattr(STDIN_FILENO, &originalTerminal) == -1) {
            return;
        }

        termios raw = originalTerminal;
        raw.c_lflag &= ~(ICANON | ECHO);
        raw.c_cc[VMIN] = 0;
        raw.c_cc[VTIME] = 0;

        if (tcsetattr(STDIN_FILENO, TCSANOW, &raw) == -1) {
            return;
        }

        originalFlags = fcntl(STDIN_FILENO, F_GETFL, 0);

        if (originalFlags != -1) {
            fcntl(STDIN_FILENO, F_SETFL, originalFlags | O_NONBLOCK);
        }

        terminalConfigured = true;
#endif
    }

    static void RestoreTerminal() {
#ifndef PLATFORM_WINDOWS
        if (terminalConfigured) {
            tcsetattr(STDIN_FILENO, TCSANOW, &originalTerminal);

            if (originalFlags != -1) {
                fcntl(STDIN_FILENO, F_SETFL, originalFlags);
            }

            terminalConfigured = false;
        }
#endif
    }

    static bool KeyPressed(int& key) {
#ifdef PLATFORM_WINDOWS
        if (!_kbhit()) {
            return false;
        }

        key = _getch();

        // Windows arrow keys use a prefix followed by a scan code.
        if (key == 0 || key == 224) {
            int scanCode = _getch();

            switch (scanCode) {
                case 72: key = 1001; break; // Up
                case 80: key = 1002; break; // Down
                case 75: key = 1003; break; // Left
                case 77: key = 1004; break; // Right
                default: key = -1; break;
            }
        }

        return true;
#else
        unsigned char c;

        if (read(STDIN_FILENO, &c, 1) != 1) {
            return false;
        }

        key = c;
        return true;
#endif
    }
};

// Snake Model
class Snake {
private:
    std::deque<Point> body;
    Direction dir;
    bool grew = false;

public:
    Snake(int startX, int startY)
        : dir(Direction::RIGHT) {
        body.push_back({startX, startY});
        body.push_back({startX - 1, startY});
        body.push_back({startX - 2, startY});
    }

    void ChangeDirection(Direction newDir) {
        // Prevent 180-degree turns.
        if ((dir == Direction::UP && newDir == Direction::DOWN) ||
            (dir == Direction::DOWN && newDir == Direction::UP) ||
            (dir == Direction::LEFT && newDir == Direction::RIGHT) ||
            (dir == Direction::RIGHT && newDir == Direction::LEFT)) {
            return;
        }

        dir = newDir;
    }

    void Move() {
        Point head = body.front();

        switch (dir) {
            case Direction::UP:
                --head.y;
                break;

            case Direction::DOWN:
                ++head.y;
                break;

            case Direction::LEFT:
                --head.x;
                break;

            case Direction::RIGHT:
                ++head.x;
                break;
        }

        body.push_front(head);

        if (grew) {
            grew = false;
        } else {
            body.pop_back();
        }
    }

    void Grow() {
        grew = true;
    }

    Point GetHead() const {
        return body.front();
    }

    const std::deque<Point>& GetBody() const {
        return body;
    }

    bool CheckSelfCollision() const {
        Point head = body.front();

        for (std::size_t i = 1; i < body.size(); ++i) {
            if (head == body[i]) {
                return true;
            }
        }

        return false;
    }
};

// Food Model
class Food {
private:
    Point pos{};
    std::mt19937 rng{
        std::random_device{}()
    };

public:
    bool Respawn(const std::deque<Point>& snakeBody) {
        std::vector<Point> availablePositions;

        for (int y = 1; y < HEIGHT - 1; ++y) {
            for (int x = 1; x < WIDTH - 1; ++x) {
                Point candidate{x, y};
                bool occupied = false;

                for (const auto& segment : snakeBody) {
                    if (segment == candidate) {
                        occupied = true;
                        break;
                    }
                }

                if (!occupied) {
                    availablePositions.push_back(candidate);
                }
            }
        }

        // The snake has filled the board.
        if (availablePositions.empty()) {
            return false;
        }

        std::uniform_int_distribution<std::size_t> dist(
            0, availablePositions.size() - 1
        );

        pos = availablePositions[dist(rng)];
        return true;
    }

    Point GetPosition() const {
        return pos;
    }
};

// Game Controller
class Game {
private:
    bool isRunning = true;
    bool won = false;
    int score = 0;

    Snake snake;
    Food food;

    void ProcessInput() {
        int key;

        while (InputManager::KeyPressed(key)) {
            if (key == 'q' || key == 'Q') {
                isRunning = false;
                return;
            }

            switch (key) {
                case 'w':
                case 'W':
                case 1001:
                    snake.ChangeDirection(Direction::UP);
                    break;

                case 's':
                case 'S':
                case 1002:
                    snake.ChangeDirection(Direction::DOWN);
                    break;

                case 'a':
                case 'A':
                case 1003:
                    snake.ChangeDirection(Direction::LEFT);
                    break;

                case 'd':
                case 'D':
                case 1004:
                    snake.ChangeDirection(Direction::RIGHT);
                    break;

#ifndef PLATFORM_WINDOWS
                // Unix terminals send arrow keys as ESC [ A/B/C/D.
                case 27: {
                    int second, third;

                    if (InputManager::KeyPressed(second) &&
                        InputManager::KeyPressed(third) &&
                        second == '[') {
                        switch (third) {
                            case 'A':
                                snake.ChangeDirection(Direction::UP);
                                break;
                            case 'B':
                                snake.ChangeDirection(Direction::DOWN);
                                break;
                            case 'D':
                                snake.ChangeDirection(Direction::LEFT);
                                break;
                            case 'C':
                                snake.ChangeDirection(Direction::RIGHT);
                                break;
                        }
                    }
                    break;
                }
#endif
            }
        }
    }

    void Update() {
        if (!isRunning) {
            return;
        }

        // Check whether the next move eats food before moving.
        Point currentHead = snake.GetHead();
        Point nextHead = currentHead;

        // Determine the next position using the current direction
        // indirectly by moving, then check the resulting head.
        snake.Move();

        Point head = snake.GetHead();

        // Wall collision
        if (head.x <= 0 || head.x >= WIDTH - 1 ||
            head.y <= 0 || head.y >= HEIGHT - 1) {
            isRunning = false;
            return;
        }

        // Self collision
        if (snake.CheckSelfCollision()) {
            isRunning = false;
            return;
        }

        // Food consumption
        if (head == food.GetPosition()) {
            score += 10;
            snake.Grow();

            if (!food.Respawn(snake.GetBody())) {
                won = true;
                isRunning = false;
            }
        }
    }

    void Render() {
        // Move cursor to top-left without clearing the entire screen.
        std::cout << "\033[H";

        std::string output;

        for (int y = 0; y < HEIGHT; ++y) {
            for (int x = 0; x < WIDTH; ++x) {
                Point current{x, y};

                if (x == 0 || x == WIDTH - 1 ||
                    y == 0 || y == HEIGHT - 1) {
                    output += '#';
                } else if (current == snake.GetHead()) {
                    output += 'O';
                } else if (current == food.GetPosition()) {
                    output += '*';
                } else {
                    bool isBody = false;

                    const auto& body = snake.GetBody();

                    for (std::size_t i = 1; i < body.size(); ++i) {
                        if (current == body[i]) {
                            isBody = true;
                            break;
                        }
                    }

                    output += isBody ? 'o' : ' ';
                }
            }

            output += '\n';
        }

        output += "Score: " + std::to_string(score);
        output += " | Controls: W/A/S/D or Arrow Keys | Quit: Q\n";

        std::cout << output << std::flush;
    }

public:
    Game()
        : snake(WIDTH / 2, HEIGHT / 2) {
        food.Respawn(snake.GetBody());
    }

    void Run() {
        InputManager::SetupTerminal();

        std::cout << "\033[2J\033[?25l";

        try {
            while (isRunning) {
                ProcessInput();
                Update();
                Render();

                if (isRunning) {
                    Sleep(100);
                }
            }
        } catch (...) {
            InputManager::RestoreTerminal();
            std::cout << "\033[?25h";
            throw;
        }

        InputManager::RestoreTerminal();
        std::cout << "\033[?25h";

        if (won) {
            std::cout << "\nYou Win! You filled the board.\n";
        } else {
            std::cout << "\nGame Over!\n";
        }

        std::cout << "Final Score: " << score << "\n";
    }
};

int main() {
    Game game;
    game.Run();

    return 0;
}

#include <iostream>
#include <vector>
#include <deque>
#include <cstdlib>
#include <ctime>

#ifdef _WIN32
#include <windows.h>
#include <conio.h>
#else
#include <unistd.h>
#include <termios.h>
#include <fcntl.h>
#endif

enum class Direction { STOP = 0, LEFT, RIGHT, UP, DOWN };

struct Point {
    int x, y;
    bool operator==(const Point& other) const {
        return x == other.x && y == other.y;
    }
};

class IInputHandler {
public:
    virtual ~IInputHandler() = default;
    virtual void handleInput(Direction& dir) = 0;
};

class ConsoleInputHandler : public IInputHandler {
public:
#ifdef _WIN32
    void handleInput(Direction& dir) override {
        if (_kbhit()) {
            switch (_getch()) {
                case 'a': if (dir != Direction::RIGHT) dir = Direction::LEFT; break;
                case 'd': if (dir != Direction::LEFT) dir = Direction::RIGHT; break;
                case 'w': if (dir != Direction::DOWN) dir = Direction::UP; break;
                case 's': if (dir != Direction::UP) dir = Direction::DOWN; break;
                case 'x': dir = Direction::STOP; break;
            }
        }
    }
#else
    ConsoleInputHandler() {
        termios term;
        tcgetattr(STDIN_FILENO, &term);
        term.c_lflag &= ~(ICANON | ECHO);
        tcsetattr(STDIN_FILENO, TCSANOW, &term);
        fcntl(STDIN_FILENO, F_SETFL, O_NONBLOCK);
    }

    void handleInput(Direction& dir) override {
        char c;
        if (read(STDIN_FILENO, &c, 1) > 0) {
            switch (c) {
                case 'a': if (dir != Direction::RIGHT) dir = Direction::LEFT; break;
                case 'd': if (dir != Direction::LEFT) dir = Direction::RIGHT; break;
                case 'w': if (dir != Direction::DOWN) dir = Direction::UP; break;
                case 's': if (dir != Direction::UP) dir = Direction::DOWN; break;
                case 'x': dir = Direction::STOP; break;
            }
        }
    }
#endif
};

class Snake {
private:
    std::deque<Point> body;
    Direction currentDir;

public:
    Snake(int startX, int startY) {
        body.push_back({startX, startY});
        body.push_back({startX - 1, startY});
        body.push_back({startX - 2, startY});
        currentDir = Direction::RIGHT;
    }

    const Point& getHead() const {
        return body.front();
    }

    const std::deque<Point>& getBody() const {
        return body;
    }

    void setDirection(Direction dir) {
        currentDir = dir;
    }

    Direction getDirection() const {
        return currentDir;
    }

    void move(bool grow) {
        Point newHead = getHead();
        switch (currentDir) {
            case Direction::LEFT:  newHead.x--; break;
            case Direction::RIGHT: newHead.x++; break;
            case Direction::UP:    newHead.y--; break;
            case Direction::DOWN:  newHead.y++; break;
            case Direction::STOP:  break;
        }
        body.push_front(newHead);
        if (!grow) {
            body.pop_back();
        }
    }

    bool checkSelfCollision() const {
        const Point& head = getHead();
        for (size_t i = 1; i < body.size(); ++i) {
            if (head == body[i]) return true;
        }
        return false;
    }
};

class Food {
private:
    Point pos;
    int width, height;

public:
    Food(int w, int h) : width(w), height(h) {
        respawn();
    }

    void respawn() {
        pos.x = rand() % (width - 2) + 1;
        pos.y = rand() % (height - 2) + 1;
    }

    const Point& getPosition() const {
        return pos;
    }
};

class GameBoard {
private:
    int width, height;

public:
    GameBoard(int w, int h) : width(w), height(h) {}

    int getWidth() const { return width; }
    int getHeight() const { return height; }

    bool isWallCollision(const Point& p) const {
        return p.x <= 0 || p.x >= width - 1 || p.y <= 0 || p.y >= height - 1;
    }
};

class GameController {
private:
    int width, height;
    bool gameOver;
    int score;
    GameBoard board;
    Snake snake;
    Food food;
    ConsoleInputHandler inputHandler;

    void draw() {
#ifdef _WIN32
        system("cls");
#else
        std::cout << "\033[H\033[J";
#endif
        for (int y = 0; y < height; ++y) {
            for (int x = 0; x < width; ++x) {
                if (x == 0 || x == width - 1 || y == 0 || y == height - 1) {
                    std::cout << "#";
                } else if (Point{x, y} == food.getPosition()) {
                    std::cout << "F";
                } else {
                    bool isBodyPart = false;
                    for (const auto& part : snake.getBody()) {
                        if (part == Point{x, y}) {
                            std::cout << (part == snake.getHead() ? "O" : "o");
                            isBodyPart = true;
                            break;
                        }
                    }
                    if (!isBodyPart) {
                        std::cout << " ";
                    }
                }
            }
            std::cout << "\n";
        }
        std::cout << "Score: " << score << "\n";
        std::cout << "Controls: W (Up), A (Left), S (Down), D (Right), X (Quit)\n";
    }

    void update() {
        Direction dir = snake.getDirection();
        inputHandler.handleInput(dir);
        snake.setDirection(dir);

        if (dir == Direction::STOP) return;

        bool growing = (snake.getHead() == food.getPosition());
        if (growing) {
            score += 10;
            food.respawn();
        }

        snake.move(growing);

        if (board.isWallCollision(snake.getHead()) || snake.checkSelfCollision()) {
            gameOver = true;
        }
    }

public:
    GameController(int w, int h) 
        : width(w), height(h), gameOver(false), score(0), 
          board(w, h), snake(w / 2, h / 2), food(w, h) {}

    void run() {
        srand(static_cast<unsigned int>(time(nullptr)));
        while (!gameOver) {
            draw();
            update();
#ifdef _WIN32
            Sleep(100);
#else
            usleep(100000);
#endif
        }
        std::cout << "\nGame Over! Final Score: " << score << "\n";
    }
};

int main() {
    GameController game(40, 20);
    game.run();
    return 0;
}
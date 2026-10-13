<!-- Task T3: Write comprehensive documentation and usage instructions for compiling and playing the C++ Snake game. -->

# C++ Console Snake Game: Documentation & User Guide

Welcome to the official documentation for the cross-platform, console-based C++ Snake game. This implementation is designed for high performance, smooth rendering without screen flickering, and seamless operation across Windows and Unix-like (Linux/macOS) environments.

---

## 1. System Requirements & Prerequisites

To compile and run this game, you will need:
* **C++ Compiler:** A modern compiler supporting **C++11** or higher (e.g., `g++`, `clang++`, or Microsoft Visual C++).
* **Terminal Emulator:** A standard terminal window with a minimum size of **40 columns by 22 rows** to prevent layout wrapping and display distortions.
* **Operating System:** Windows, Linux, or macOS.

---

## 2. Compilation Instructions

Save the source code into a file named `snake_game.cpp`. Open your terminal or command prompt, navigate to the directory containing the file, and use the appropriate compilation command for your operating system:

### Linux / macOS
```bash
g++ -std=c++11 snake_game.cpp -o snake_game
```

### Windows (using MinGW)
```cmd
g++ -std=c++11 snake_game.cpp -o snake_game.exe
```

---

## 3. How to Play & Game Controls

Once compiled, execute the binary directly from your terminal:

* **Linux / macOS:** `./snake_game`
* **Windows:** `snake_game.exe`

### Controls Guide
* **Move Up:** `W` or `Up Arrow`
* **Move Down:** `S` or `Down Arrow`
* **Move Left:** `A` or `Left Arrow`
* **Move Right:** `D` or `Right Arrow`
* **Quit Game:** `Q`

### Legend
* `#` — Arena Boundaries
* `O` — Snake Head
* `o` — Snake Body
* `*` — Food

---

## 4. Technical Architecture Overview

The codebase is engineered around clean Object-Oriented Programming (OOP) principles and platform abstraction:

1. **Platform Abstraction Layer (`InputManager`):** 
   * Uses `#if defined(_WIN32)` directives to switch between Windows-specific console inputs (`<conio.h>`) and POSIX terminal configurations (`<termios.h>` and `fcntl`) for non-blocking raw keyboard input without requiring the user to press the Enter key.
2. **Game Loop & Frame Pacing (`Game`):** 
   * Implements a fixed-timestep loop paired with `std::this_thread::sleep_for` to maintain a stable game speed (~10 FPS / 100ms per frame).
   * Utilizes ANSI escape codes (`\033[H`) to reposition the cursor to the top-left of the console each frame, completely eliminating screen flicker.
3. **Collision & State Management (`Snake`, `Food`):**
   * Dynamically tracks snake segments using `std::deque` for efficient head insertions and tail removals.
   * Features robust boundary checks and self-intersection detection to trigger game-over states cleanly.

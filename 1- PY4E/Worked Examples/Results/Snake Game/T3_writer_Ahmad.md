<!-- Task T3: Write comprehensive documentation and instructions on how to compile, build, and run the C++ Snake game on various operating systems. -->

# C++ Console Snake Game: Compilation, Build, and Execution Documentation

This document provides comprehensive instructions on how to set up, compile, build, and run the cross-platform C++ Console Snake game across major operating systems (Windows, Linux, and macOS).

---

## 1. Prerequisites

Before proceeding, ensure you have a modern C++ compiler installed that supports **C++11** or higher.

* **Windows:** MinGW-w64 (`g++`), Microsoft Visual Studio (MSVC), or Clang.
* **Linux:** GNU Compiler Collection (`g++`) or Clang. Most distributions provide this via build tools packages (e.g., `build-essential`).
* **macOS:** Apple Xcode Command Line Tools (`clang++`).

### Verifying Your Compiler
Open your terminal or command prompt and run the following command to check your compiler version:
```bash
g++ --version
# OR for macOS / Clang:
clang++ --version
```
Ensure the version supports C++11 or newer (GCC 4.8+ or Clang 3.3+).

---

## 2. Source Code Setup

1. Create a new directory for your project:
   ```bash
   mkdir snake_game
   cd snake_game
   ```
2. Create a source file named `snake.cpp` using your preferred text editor (e.g., VS Code, Vim, Notepad).
3. Copy and paste the C++ source code into `snake.cpp` and save the file.

---

## 3. Compiling and Building by Operating System

### Operating System: Windows

Depending on whether you use MinGW or Microsoft Visual Studio, choose one of the following methods:

#### Method A: Using MinGW (`g++`) via Command Prompt / PowerShell
1. Open Command Prompt or PowerShell and navigate to your project directory.
2. Compile the source file into an executable named `snake.exe`:
   ```cmd
   g++ -std=c++11 snake.cpp -o snake.exe
   ```
3. If compilation succeeds without errors, `snake.exe` will be generated in your folder.

#### Method B: Using Microsoft Visual Studio (MSVC) via Developer Command Prompt
1. Open the **Developer Command Prompt for VS** from your Windows start menu.
2. Navigate to your project folder:
   ```cmd
   cd path\to\snake_game
   ```
3. Compile using the MSVC compiler (`cl`):
   ```cmd
   cl /EHsc snake.cpp /Fe:snake.exe
   ```

---

### Operating System: Linux (Ubuntu, Debian, Fedora, Arch, etc.)

1. Open your terminal and ensure you have build essentials installed (Ubuntu/Debian example):
   ```bash
   sudo apt update
   sudo apt install build-essential
   ```
2. Navigate to your project directory.
3. Compile the code using `g++`:
   ```bash
   g++ -std=c++11 snake.cpp -o snake
   ```
4. This produces a binary executable file named `snake`.

---

### Operating System: macOS

1. Open your terminal. If you haven't installed Xcode Command Line Tools yet, install them by running:
   ```bash
   xcode-select --install
   ```
2. Navigate to your project directory.
3. Compile the code using `clang++` (aliased or standard on macOS):
   ```bash
   clang++ -std=c++11 snake.cpp -o snake
   ```
   *(Note: You can also use `g++` if you have installed GCC via Homebrew).*

---

## 4. Running the Game

To ensure smooth gameplay and proper ANSI terminal rendering, run the game directly from an active terminal window.

* **Windows:**
  ```cmd
  snake.exe
  ```
* **Linux / macOS:**
  ```bash
  ./snake
  ```

---

## 5. Game Controls & Instructions

* **Navigation:** Use **W, A, S, D** or the **Arrow Keys** to steer the snake (`O` represents the head, `o` represents the body).
* **Objective:** Collect the food (`*`) to grow longer and increase your score. Every 50 points, the game speed increases slightly.
* **Game Over:** Crashing into the outer walls or into your own tail triggers the Game Over screen. You can choose to restart (`y/n`) or quit.
* **Quit:** Press **Q** at any time during gameplay to exit immediately.

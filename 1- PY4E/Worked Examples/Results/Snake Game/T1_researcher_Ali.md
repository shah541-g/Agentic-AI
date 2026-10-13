<!-- Task T1: Research the requirements and libraries needed to build a console-based Snake game in C++, including handling non-blocking keyboard input and timing across different platforms (Windows/Linux). -->

### 1. Core Requirements
To build a console-based Snake game in C++, the application must meet several fundamental architectural requirements:
*   **Game Loop:** A continuous execution cycle that handles input processing, game state updates (snake movement, collision detection, food generation), and screen rendering.
*   **State Management:** Data structures to track the snake's body segments (typically coordinates), current direction, food location, score, and game over status.
*   **Non-Blocking Input:** The game must not pause or halt execution waiting for the player to press a key. If no key is pressed, the snake must continue moving automatically based on the game tick.
*   **Frame Rate / Timing Control:** A mechanism to regulate the game speed so the snake moves at a consistent, playable velocity regardless of CPU performance.
*   **Screen Rendering / Flicker Reduction:** Redrawing the game board efficiently to minimize visual tearing and flickering in the terminal.

---

### 2. Platform-Specific Requirements and Libraries

Because standard C++ libraries (`<iostream>`) do not support non-blocking console input or millisecond-level sleep functions natively across all operating systems, platform-specific system calls or cross-platform wrappers are required.

#### A. Windows
*   **Headers:** `<windows.h>`, `<conio.h>`
*   **Non-Blocking Input:** 
    *   `_kbhit()`: Checks if a keystroke is currently waiting in the input buffer. Returns non-zero if true, zero otherwise.
    *   `_getch()`: Retrieves the pressed key immediately without echoing it to the console and without requiring the Enter key.
*   **Timing:** 
    *   `Sleep(milliseconds)` from `<windows.h>` pauses execution for the specified duration.
*   **Console Manipulation (Optional for advanced rendering):**
    *   `SetConsoleCursorPosition()` can be used to overwrite characters in place rather than clearing the whole screen, significantly reducing flicker.

#### B. Linux / POSIX
*   **Headers:** `<unistd.h>`, `<termios.h>`, `<fcntl.h>`, `<sys/select.h>`
*   **Non-Blocking Input:** 
    *   Standard Linux terminals operate in "canonical mode" (line-buffered, waiting for Enter). To capture single keystrokes without blocking, the terminal settings (`termios`) must be modified to disable canonical mode and local echo (`ECHO` and `ICANON`).
    *   Alternatively, non-blocking polling can be implemented using `select()` or `poll()` on standard input (`STDIN_FILENO`) combined with `read()`.
*   **Timing:** 
    *   `usleep(microseconds)` or `nanosleep()` from `<unistd.h>` / `<time.h>`. Modern C++ also supports `std::this_thread::sleep_for()` from `<thread>`.

---

### 3. Cross-Platform Abstraction Libraries

To avoid writing conditional compilation blocks (`#ifdef _WIN32`) for every system call, developers often rely on specific libraries or standard C++ features:

*   **Standard C++ Library (`<chrono>` and `<thread>`):** 
    *   Introduced in C++11, `std::this_thread::sleep_for(std::chrono::milliseconds(X))` provides a cross-platform sleep mechanism, replacing platform-specific `Sleep()` and `usleep()`.
*   **Curses / PDCurses (`<curses.h>` or `<ncurses.h>`):**
    *   **Linux/macOS:** `ncurses` is the standard library for terminal handling. It abstracts non-blocking input via `timeout()` or `nodelay()`, manages window rendering, and handles cursor visibility.
    *   **Windows:** `PDCurses` is a public domain version of curses that works natively on Windows.
    *   *Note:* While powerful, curses introduces an external library dependency that may complicate simple single-file projects.

---

### 4. Summary of Standard Implementation Stack

A typical modern C++ (C++11 or higher) console Snake game utilizes:
1.  `<iostream>` / `<vector>` / `<deque>`: Standard containers for the game grid and snake body.
2.  `<chrono>` and `<thread>`: For cross-platform game loop timing (`std::this_thread::sleep_for`).
3.  **Platform Branching:**
    *   **Windows:** `<conio.h>` (`_kbhit`, `_getch`).
    *   **Linux:** Custom terminal configuration via `<termios.h>` or the `ncurses` library.

---

### 5. Uncertainties and Limitations
*   **Terminal Compatibility:** Behavior can vary significantly between modern terminal emulators (e.g., Windows Terminal, GNOME Terminal, xterm, VS Code integrated terminal), particularly regarding ANSI escape code support for colors and cursor positioning.
*   **Input Latency:** Native console input polling (`_kbhit` or modified `termios`) can sometimes suffer from OS-level key repeat rates or buffer delays, making rapid directional changes occasionally feel unresponsive compared to graphical applications.

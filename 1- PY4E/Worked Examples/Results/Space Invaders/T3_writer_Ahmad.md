<!-- Task T3: Write comprehensive instructions and a README explaining how to run the Space Invaders Python game. -->

# Space Invaders - Python Turtle Edition

A complete, arcade-style clone of the classic **Space Invaders** game built entirely using Python’s built-in standard library (`turtle`). No external dependencies or packages (like Pygame) are required to run this game!

---

## Features

- **Zero Dependencies:** Uses only Python's native `turtle` graphics module.
- **Smooth Continuous Movement:** Responsive key handling for fluid player navigation.
- **Dynamic Difficulty:** The alien swarm increases in speed as you eliminate invaders.
- **Retro Color-Coded Swarm:** Multi-colored rows for an authentic arcade aesthetic.
- **Arcade HUD:** Live updating scoreboard tracking your score and game status.
- **Restart Mechanism:** Instantly restart a new game using the `R` key upon victory or defeat.

---

## Prerequisites

- **Python 3.x** installed on your system. 
  *(The `turtle` module comes pre-installed with almost all standard Python distributions for Windows, macOS, and Linux).*

To verify your Python installation, open your terminal or command prompt and run:
```bash
python --version
```

---

## Installation & Setup

1. Copy the source code provided in the script section and save it to a file named `space_invaders.py`.
2. Open your terminal or command prompt and navigate to the directory where you saved the file.

---

## How to Run the Game

Execute the script using Python:

```bash
python space_invaders.py
```

A graphical game window (800x600 pixels) will automatically open, initializing the game loop.

---

## Controls

| Action | Primary Key | Alternative Key |
| :--- | :--- | :--- |
| **Move Left** | Left Arrow (`←`) | `A` |
| **Move Right** | Right Arrow (`→`) | `D` |
| **Fire Laser** | Spacebar | — |
| **Restart Game** | `R` *(after Game Over / Victory)* | — |

---

## Gameplay Instructions

1. **Objective:** Eliminate all alien invaders before they reach your position or breach the bottom boundary of the screen.
2. **Scoring:** Every alien destroyed awards **100 points**.
3. **Winning:** Clear the entire alien swarm from the screen to achieve **Victory**.
4. **Losing:** If an alien collides with your ship or reaches the bottom of the screen ($Y \le -240$), it results in a **Game Over**. Press `R` to try again!

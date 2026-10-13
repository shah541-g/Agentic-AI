<!-- Task T3: Write a user guide explaining how to run the Python script, the controls for the Maze Escape game, and instructions on how to navigate the big maze. -->

# Python Turtle Maze Escape: User Guide

Welcome to **Maze Escape**, an interactive grid-based puzzle game built using Python’s native `turtle` graphics module. Your objective is to guide the crimson circle player from the starting zone to the golden exit.

---

## 1. System Requirements & Running the Script

The game runs on Python's built-in libraries, meaning you do not need to install any external packages (like Pygame or NumPy).

### Prerequisites
* **Python 3.x** installed on your system.
* The `turtle` module (this comes pre-installed with standard Python distributions on Windows, macOS, and most Linux environments).

### How to Run the Game
1. Copy the provided Python script and save it to a file named **`maze_game.py`**.
2. Open your terminal, command prompt, or IDE terminal.
3. Navigate to the directory where you saved the file.
4. Execute the script by running the following command:
   ```bash
   python maze_game.py
   ```
5. A graphical window titled **"Python Turtle Maze Game"** will automatically pop up, displaying the 25x25 maze.

---

## 2. Game Controls

You can control the crimson player circle using either the **Arrow Keys** or traditional **WASD** keyboard layouts:

| Direction | Arrow Key | WASD Key |
| :--- | :--- | :--- |
| **Up** | `Up Arrow` | `W` |
| **Down** | `Down Arrow` | `S` |
| **Left** | `Left Arrow` | `A` |
| **Right** | `Right Arrow` | `D` |

---

## 3. How to Navigate the Maze

The maze is designed as a challenging 25x25 grid layout. Understanding the visual indicators will help you find your way:

* **The Start Zone (`S`)**: Colored in **Light Blue**. This is where your crimson player begins the game at coordinates `(1, 1)`.
* **Walls (`W`)**: Colored in **Black**. These are solid boundaries. The collision detection system prevents you from moving through walls. If you hit a wall, your movement will be blocked until you choose an open path.
* **Paths (`P`)**: The open corridors you must traverse to move through the maze.
* **The Exit Zone (`E`)**: Colored in **Gold**. Located near the bottom right of the grid at coordinates `(23, 23)`. 

### Winning the Game
Carefully navigate the open corridors using your keyboard controls. Once you successfully maneuver the crimson circle onto the **Golden Exit Zone (`E`)**, the game will lock movement and display a congratulatory message: **"YOU WIN! 🎉"** on the screen.

<!-- Task T3: Write documentation explaining how to run the Brick Breaker game, the controls, and a brief overview of the code structure. -->

# Brick Breaker Game Documentation

Welcome to the documentation for the **Brick Breaker** game! This project is a classic arcade-style game built in Python using the built-in `turtle` graphics library. 

---

## Prerequisites & Running the Game

### Requirements
* Python 3.x (the `turtle` module comes pre-installed with standard Python distributions).

### How to Run
1. Save the game code into a file, for example, `brick_breaker.py`.
2. Open your terminal or command prompt.
3. Navigate to the folder where you saved the file.
4. Run the script using the following command:
   ```bash
   python brick_breaker.py
   ```

---

## Controls

* **Left Arrow Key:** Move the paddle to the left.
* **Right Arrow Key:** Move the paddle to the right.
* **'R' / 'r' Key:** Restart the game after reaching a "Game Over" or "You Win" state.

---

## Code Structure Overview

The codebase is organized using an object-oriented programming (OOP) approach, separating concerns into distinct classes that handle rendering, movement, collisions, and game state.

### 1. `Paddle`
* **Purpose:** Represents the player-controlled paddle at the bottom of the screen.
* **Key Features:** Handles smooth continuous movement via `onkey` and `onkeyrelease` event listeners, enforces screen boundaries so the paddle cannot leave the window, and calculates an Axis-Aligned Bounding Box (AABB) for collision detection.

### 2. `Ball`
* **Purpose:** Represents the bouncing projectile that interacts with boundaries, the paddle, and bricks.
* **Key Features:** Manages velocity vectors (`dx`, `dy`), position resets when a life is lost, and AABB bounding box calculations.

### 3. `BrickManager`
* **Purpose:** Generates and manages the grid of colored bricks at the top of the screen.
* **Key Features:** Automatically populates a multi-row, multi-column grid with alternating colors, checks for ball-to-brick collisions, hides destroyed bricks, and tracks whether all bricks have been cleared to trigger a win condition.

### 4. `GameManager`
* **Purpose:** Manages meta-data, including the current score, remaining lives, and game states (`RUNNING`, `WON`, `GAMEOVER`).
* **Key Features:** Updates the Heads-Up Display (HUD) and renders centered text messages on the screen for win/loss conditions.

### 5. `Game`
* **Purpose:** The main game engine loop and controller.
* **Key Features:** Initializes the `turtle.Screen()`, binds keyboard inputs, drives the game loop using `screen.ontimer()` for consistent frame-rate control (targeting 60 FPS), and handles complex collision logic (walls, floor, paddle, and bricks).

<!-- Task T3: Write a clear user guide and code documentation explaining how to run and play the Target Shooter game. -->

# Target Shooter Game: User Guide and Code Documentation

Welcome to the **Target Shooter Game** documentation! This guide provides an overview of how to install, play, and understand the underlying Python code for the game.

---

## Part 1: User Guide

### Introduction
Target Shooter is an interactive, physics-based arcade game built using Python’s built-in `turtle` graphics library. Your goal is to score as many points as possible by aiming your cannon and hitting oscillating targets before your ammunition runs out.

### Prerequisites
* **Python 3.x** installed on your system. 
* The `turtle`, `math`, and `random` libraries (these come pre-installed with standard Python distributions, so no additional package manager like `pip` is required).

### How to Run the Game
1. Copy the Python source code provided in the system output into a file named `target_shooter.py`.
2. Open your terminal or command prompt.
3. Navigate to the folder where you saved the file.
4. Run the script using the following command:
   ```bash
   python target_shooter.py
   ```
5. A window titled **"Target Shooter Game"** will launch, and gameplay will begin immediately.

### Game Controls
* **Left Arrow Key:** Aim the cannon turret further to the left.
* **Right Arrow Key:** Aim the cannon turret further to the right.
* **Spacebar:** Fire a projectile/cannonball.
* **R Key:** Restart the game after reaching a "Game Over" or win state.

### Rules and Objective
* **Ammunition:** You start each game with **10 rounds of ammo**. 
* **Lives:** You start with **3 lives**. You lose a life every time a fired projectile misses the targets and goes out of bounds.
* **Scoring:** Each successful hit awards **10 points**. 
* **Winning/Losing:** The game ends if you lose all 3 lives or run out of ammunition. Keep an eye on your HUD (Heads-Up Display) in the top-left corner to track your progress.

---

## Part 2: Code Documentation

### Architecture Overview
The script is organized into distinct structural blocks:
1. **Constants & Configuration:** Screen dimensions, physics multipliers (gravity, air resistance), and layout sizing.
2. **Game State Variables:** Global tracking elements for `score`, `lives`, `ammo`, `turret_angle`, and projectile kinematics (`proj_vx`, `proj_vy`).
3. **Screen Setup:** Initializes the turtle screen window, background color, and disables automatic screen updates (`screen.tracer(0)`) to implement a custom manual render loop for high performance.
4. **Graphical Elements (Turtles):** Dedicated turtles for the HUD, turret base/barrel, projectile bullet, and active targets.
5. **Event Handlers (Controls):** Keyboard bindings for aiming, firing, and resetting the game state.
6. **Main Game Loop (`game_loop`):** Handles target movement oscillation, projectile physics (applying gravity and air resistance), collision detection (Euclidean distance checks), and win/loss evaluations.

### Key Functions Reference

* **`create_target(x, y)`**
  * *Parameters:* `x` (integer coordinate), `y` (integer coordinate)
  * *Returns:* A dictionary containing the target turtle reference, coordinates, and horizontal velocity (`dx`).
  * *Description:* Instantiates a new target turtle object at a designated position with randomized horizontal drift.

* **`init_targets()`**
  * *Description:* Clears existing targets and spawns a fresh batch of 4 targets across randomized horizontal locations on the upper half of the screen.

* **`aim_left()` / `aim_right()`**
  * *Description:* Modifies the global `turret_angle` within defined safety boundaries (10 to 170 degrees) while the game is active.

* **`fire()`**
  * *Description:* Decrements available ammo, sets `projectile_active` to `True`, calculates directional velocity components using trigonometric functions (`math.sin` and `math.cos`), and deploys the bullet turtle from the turret's origin.

* **`draw_hud()`**
  * *Description:* Clears and redraws the status text displaying current score, lives, and remaining ammo in the top-left corner, as well as overlaying win/loss dialogs when the game concludes.

* **`game_loop()`**
  * *Description:* The core heartbeat function running at ~50 FPS via `screen.ontimer()`. It updates target coordinates (bouncing them off screen borders), updates projectile physics (applying gravity and air resistance), evaluates collision overlaps, and triggers screen refreshes.

<!-- Task T4: Write user instructions and code documentation explaining how to run and play the top-down car racing game. -->

# Top-Down Car Racing - Arcade Edition: User Instructions & Code Documentation

Welcome to the **Top-Down Car Racing - Arcade Edition** documentation. This guide covers the game's prerequisites, execution instructions, control schemes, core gameplay mechanics, and technical codebase architecture.

---

## 1. System Requirements & Installation

This game is built entirely using Python's built-in standard libraries, meaning you do not need to install any external third-party dependencies (like Pygame).

* **Python Version:** Python 3.x (Ensure Python is added to your system's environment variables/PATH).
* **Dependencies:** `turtle`, `math`, `time` (all bundled with standard Python distributions).

### How to Run the Game
1. Save the provided Python code into a file named `racing_game.py`.
2. Open your terminal, command prompt, or IDE terminal in the directory where the file is saved.
3. Execute the script using the command:
   ```bash
   python racing_game.py
   ```

---

## 2. Controls & Game Flow

| Action | Primary Keys | Alternative Keys | Description |
| :--- | :--- | :--- | :--- |
| **Accelerate** | `Up Arrow` | `W` | Increases forward speed up to the maximum velocity limit. |
| **Brake / Reverse** | `Down Arrow` | `S` | Slows the car down, applies brakes, or drives in reverse. |
| **Steer Left** | `Left Arrow` | `A` | Turns the car counter-clockwise (steering scales with speed). |
| **Steer Right** | `Right Arrow` | `D` | Turns the car clockwise. |
| **Start Game** | `Spacebar` | — | Begins the countdown sequence from the Start Menu. |
| **Pause / Resume** | `P` | — | Freezes the race and opens the pause overlay. |
| **Restart Game** | `R` | — | Restarts the race after reaching the Game Over screen. |
| **Quit Game** | `Escape` | — | Immediately closes the game window. |

---

## 3. Gameplay Mechanics & Rules

* **The Track:** The game features an oval asphalt circuit bound by outer track walls and an inner green island barrier. 
* **Surface Physics:** 
  * **Asphalt:** Provides high traction and allows maximum velocity.
  * **Grass (Off-road):** Imposes heavy drag friction and severely restricts top speed (max speed reduced by 60%), punishing drivers who cut corners.
* **Checkpoints & Laps:** 
  * The track is divided into an ordered sequence of 4 checkpoints.
  * You must successfully navigate through all checkpoints in order to complete a lap.
  * The game is won after completing **3 total laps**.
* **Collisions:** Hitting the outer boundary walls or the inner island barrier will cause the car to bounce off and penalize your speed.

---

## 4. Code Architecture & Technical Documentation

The application runs at a targeted **60 FPS** utilizing a custom fixed-timestep game loop powered by `turtle.ontimer()` and manual screen updates (`screen.tracer(0)`).

### Key Modules & Components

#### A. Constants & Configuration
* **Window Dimensions:** `900x700` pixels.
* **Physics Tuning:** Parameters like `MAX_SPEED` (7.0), `ACCELERATION` (0.2), `FRICTION` (0.96), and `OFFROAD_FRICTION` (0.85) are isolated at the top of the script for easy arcade-tuning.

#### B. Game State Machine (`game_state`)
The game operates through a deterministic state machine managing UI renders and update blocks:
* `START`: Displays the title screen and instructions.
* `COUNTDOWN`: Runs a 3-2-1 timer before launching the race.
* `RACING`: The active gameplay loop handling input, physics, and lap counters.
* `PAUSED`: Suspends physical updates while keeping the HUD visible.
* `GAME_OVER`: Displays final elapsed times and restart prompts.

#### C. Physics & Collision Engine (`update_physics()`)
* **Surface Detection:** Uses mathematical ellipse formulas to check whether the car’s coordinates `(car_x, car_y)` lie within the asphalt boundaries:
  $$\left(\frac{x}{R_x}\right)^2 + \left(\frac{y}{R_y}\right)^2$$
* **Steering Dynamics:** Turning response is dynamically scaled based on current velocity (`turn_multiplier = car_speed / MAX_SPEED`), ensuring stationary turning is disabled and high-speed turns require precision.
* **Wall Bounce:** Boundary infractions trigger an elastic reflection by inverting and dampening velocity (`car_speed *= -0.4`).

#### D. Input Event Handling
To prevent operating system key-repeat delays and stuttering during continuous driving, input states are captured via a dictionary flag system (`keys = {"up": False, ...}`) triggered by `.onkeypress` and `.onkeyrelease` bindings.

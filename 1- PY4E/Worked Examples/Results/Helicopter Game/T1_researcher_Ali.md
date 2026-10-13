<!-- Task T1: Research the requirements, game mechanics, and UI library options (like Pygame or Turtle) for creating a 2D Helicopter game in Python. -->

### 1. Requirements & Core Game Loop
To create a 2D Helicopter game in Python (often a *Copter* or *Flappy Bird* style arcade game where the player holds a button to ascend and falls via gravity), the following foundational requirements are necessary:

*   **Python Environment:** Python 3.x installed.
*   **Game State Management:** Logic to handle different screens (Start Menu, Gameplay, Game Over, High Score screen).
*   **Time & Frame Rate Control:** A clock mechanism to lock the game at a consistent frame rate (typically 30 or 60 Frames Per Second) to ensure uniform physics and movement speeds across different hardware.
*   **Asset Management:** Loading and rendering images (helicopter sprites, background, obstacles) and audio (engine hums, explosion/crash sounds, score chimes).

---

### 2. Core Game Mechanics
Implementing a functional 2D helicopter game requires programming several interconnected mechanics:

*   **Physics Engine (Gravity & Lift):**
    *   *Gravity:* A constant downward acceleration applied to the helicopter's vertical velocity every frame ($v_y = v_y + \text{gravity}$).
    *   *Lift/Thrust:* When the player presses/holds a key (e.g., Spacebar or Left Mouse Button), an upward acceleration is applied, counteracting gravity ($v_y = v_y - \text{lift}$).
*   **Movement & Scrolling:**
    *   The background and terrain/obstacles move continuously from right to left to simulate forward flight, while the helicopter remains relatively fixed on the horizontal axis (or moves freely within a restricted horizontal window).
*   **Procedural Obstacle Generation (Cave/Terrain Generation):**
    *   Generating top and bottom boundaries (or cave walls/stalactites) that scroll toward the player.
    *   Walls can be generated using pseudo-random height adjustments constrained by a maximum slope angle to ensure the map remains beatable.
*   **Collision Detection:**
    *   *Bounding Box (AABB) or Pixel-Perfect Collision:* Detecting intersections between the helicopter sprite and the terrain, obstacles, or screen boundaries. 
    *   Upon collision, trigger the "Game Over" state.
*   **Scoring System:**
    *   Score increases proportionally to survival time or distance traveled. Saving high scores locally (via JSON, CSV, or text files).

---

### 3. UI and Graphics Library Options
Two primary standard libraries are available in Python for 2D game development: **Pygame** and **Turtle**.

#### Option A: Pygame (Recommended)
Pygame is a set of Python modules designed for writing games. It provides direct access to the SDL library, offering high performance and extensive features.

*   **Pros:**
    *   **Performance:** Handles high frame rates smoothly, suitable for scrolling backgrounds and multiple sprites.
    *   **Sprite & Image Handling:** Native support for loading, scaling, rotating, and blitting PNGs (useful for tilting the helicopter up/down based on velocity).
    *   **Audio Support:** Built-in mixer (`pygame.mixer`) for sound effects and background music.
    *   **Input Handling:** Robust event loop handling continuous key presses (`pygame.key.get_pressed()`) which is crucial for smooth helicopter controls.
    *   **Collision Detection:** Built-in helper functions like `pygame.Rect.colliderect()` and mask-based pixel-perfect collisions.
*   **Cons:**
    *   Requires external installation (`pip install pygame`).

#### Option B: Turtle (Alternative / Beginner-Only)
Turtle is a pre-installed Python standard library designed for introductory programming and simple graphics.

*   **Pros:**
    *   Comes built-in with Python (zero installation required).
    *   Very gentle learning curve for absolute beginners.
*   **Cons:**
    *   **Performance Bottleneck:** Rendering speed is notoriously slow; it struggles with real-time scrolling backgrounds, rapid sprite updates, and smooth physics.
    *   **Limited UI/Audio:** Lacks native sound mixing and advanced input handling (handling simultaneous key presses or smooth holding mechanics is clumsy).
    *   Not recommended for a responsive, modern-feeling arcade game.

---

### 4. Areas of Uncertainty & Limitations
*   **Physics Determinism:** Depending on how delta time ($dt$) is handled, physics might behave slightly differently if frame rates fluctuate heavily, though this is easily mitigated by using Pygame’s `Clock.tick(FPS)`.
*   **Procedural Generation Balance:** Without careful tuning of the gap size between top and bottom obstacles and the speed of generation, procedural caves can occasionally produce mathematically impossible layouts, requiring a minimum-gap validation algorithm.

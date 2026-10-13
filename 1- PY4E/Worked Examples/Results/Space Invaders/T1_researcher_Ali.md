<!-- Task T1: Research the basic requirements, game mechanics, and setup for a Space Invaders clone using Python's turtle module. -->

### Basic Requirements

To create a functional Space Invaders clone using Python’s built-in `turtle` module, the project requires the following fundamental components:

*   **Python Environment:** Python 3.x installed with access to the standard library (`turtle`, `math`, `random`).
*   **Game Window (`Screen`):** A fixed-dimension graphical window (commonly 800x600 pixels) with a black background and a locked update rate using `tracer(0)` for smooth, flicker-free rendering.
*   **Player Entity:** A controllable sprite at the bottom of the screen that moves horizontally and fires projectiles.
*   **Alien Swarm:** A grid of enemy sprites (e.g., 3 rows of 5–10 aliens) that move collectively across the screen and descend upon reaching boundaries.
*   **Projectiles:** Independent states for player lasers (moving upward) and optionally alien bombs (moving downward).
*   **Collision Detection:** Bounding-box or distance-formula logic to register hits between lasers and aliens, and between aliens and the player.
*   **Score and Lives Tracking:** A text display updating the player's score and remaining lives in real-time.

---

### Game Mechanics

The core gameplay loop relies on event-driven inputs and a manual frame-update loop (`screen.update()`):

1.  **Player Movement:** 
    *   Controlled via keyboard listeners (`screen.onkeypress`).
    *   Left and Right arrow keys alter the player's horizontal coordinate ($x$).
    *   Movement bounds must be enforced so the player cannot exit the screen boundaries.
2.  **Shooting:**
    *   The spacebar triggers a laser. 
    *   *Constraint:* Typically, the player can only have one active laser on screen at a time to maintain balance.
3.  **Alien Swarm Behavior:**
    *   Aliens move synchronously in one direction (left or right).
    *   When the edge of the screen is reached by any alien, the entire swarm shifts downward by a set pixel amount and reverses horizontal direction.
    *   As aliens are destroyed, the remaining swarm often speeds up (by reducing frame delay or increasing step size).
4.  **Collision Handling:**
    *   **Laser vs. Alien:** If the distance between a player laser and an alien is below a specific threshold (e.g., $< 15$ pixels), both objects are deactivated/hidden, and the score increases.
    *   **Alien vs. Player:** If an alien reaches the bottom of the screen or collides with the player, a life is lost, and positions may reset.
5.  **Win/Loss Conditions:**
    *   **Win:** All aliens in the swarm are destroyed.
    *   **Loss:** Aliens reach the player's $y$-coordinate, or the player loses all lives.

---

### Setup and Code Structure

A modular setup ensures the game loop runs efficiently within Python's single-threaded event model.

#### 1. Initialization Boilerplate
```python
import turtle

# Screen setup
screen = turtle.Screen()
screen.setup(width=800, height=600)
screen.bgcolor("black")
screen.title("Space Invaders - Turtle Clone")
screen.tracer(0)  # Turn off automatic updates for manual frame control
```

#### 2. Object Representation
*   Use `turtle.Turtle()` instances for the player, aliens, and lasers.
*   Set shapes using built-in turtle shapes (`"triangle"`, `"square"`, `"circle"`) or custom vector coordinates via `register_shape()`.
*   Hide default turtle cursors using `.penup()` and `.hideturtle()` until positioned.

#### 3. The Game Loop
Because `turtle` does not have a native delta-time game loop, developers use `screen.ontimer()` or a `while True` loop paired with `screen.update()` and `time.sleep()`.

```python
import time

# Example Game Loop Structure
running = True

def game_loop():
    global running
    if not running:
        return

    # 1. Update positions (Player, Aliens, Lasers)
    # 2. Check collisions
    # 3. Redraw screen
    screen.update()

    # Call loop again after roughly 10-20ms (approx. 50-60 FPS)
    screen.ontimer(game_loop, 20)

game_loop()
screen.mainloop()
```

#### 4. Input Binding
```python
# Setup keyboard bindings
screen.listen()
# Functions move_left, move_right, and fire_laser must be defined separately
screen.onkeypress(move_left, "Left")
screen.onkeypress(move_right, "Right")
screen.onkeypress(fire_laser, "space")
```

---

### Areas of Uncertainty / Limitations

*   **Performance Bottlenecks:** The `turtle` module is designed for education, not high-performance gaming. Rendering dozens of moving entities simultaneously (swarm + multiple lasers + text updates) can cause noticeable input lag or frame drops if the screen updates are handled inefficiently.
*   **Collision Accuracy:** Simple distance-based collision (`turtle.distance()`) treats sprites as circular radii rather than rectangular grids, which can occasionally lead to visual "ghost hits" along the diagonal corners of square sprites. 
*   **Sound Effects:** Native support for cross-platform audio within the standard library is absent. Adding sound effects requires importing external modules (like `winsound` on Windows or `pygame`), which technically breaks a pure "standard library only" constraint.

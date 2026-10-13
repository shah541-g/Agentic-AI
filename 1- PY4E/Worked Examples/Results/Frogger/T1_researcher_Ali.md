<!-- Task T1: Research standard Frogger mechanics, screen dimensions, grid layout, and key control mappings suitable for a Python Turtle implementation. -->

### Research Findings: *Frogger* Mechanics, Dimensions, Grid, and Controls for Python Turtle

#### 1. Screen Dimensions & Grid Layout
To replicate the classic 1981 arcade feel within the Python `turtle` module while ensuring smooth integer-based grid movement, specific coordinate systems and scaling are required.

*   **Standard Arcade Resolution Aspect Ratio:** ~4:3 (vertical orientation).
*   **Turtle Implementation Canvas:** 
    *   Width: 480 pixels
    *   Height: 600 pixels (extra vertical space accommodates top scoring/timer areas and bottom start zone).
*   **Grid System (Tile-based):**
    *   The playing field is divided into a discrete grid of columns and rows.
    *   **Columns:** 13 columns (standard for the original arcade layout to allow precise jumping).
    *   **Rows:** 13 rows total.
    *   **Tile Size:** 40 pixels $\times$ 40 pixels ($13 \text{ cols} \times 40\text{px} = 520\text{px}$ width, or adjusted to fit: $12 \text{ cols} \times 40\text{px} = 480\text{px}$). *Correction based on standard 480px width:* **12 columns by 15 rows** of 40x40 pixel blocks, or **14 columns by 13 rows** of 40x40 pixel blocks ($12 \times 40 = 480$, $15 \times 40 = 600$).
    *   *Alternative Classic Arcade Grid Mapping:* 12 columns wide, 13-15 rows high. Let us use a standardized **40px tile size**, resulting in a coordinate grid where each step is exactly 40 pixels.

*   **Row Breakdown (Top to Bottom, 0 to 14):**
    *   **Row 0:** Top banner (Score, Lives, Time).
    *   **Row 1:** Home slots (5 target destinations for frogs).
    *   **Row 2:** Water/River zone (Fast logs/alligators, top tier).
    *   **Row 3:** Water/River zone (Turtles).
    *   **Row 4:** Water/River zone (Logs, middle tier).
    *   **Row 5:** Water/River zone (Long logs).
    *   **Row 6:** Water/River zone (Turtles, slow tier).
    *   **Row 7:** Safety median (Bank/Starting zone before river).
    *   **Row 8:** Road zone (Fast cars).
    *   **Row 9:** Road zone (Trucks).
    *   **Row 10:** Road zone (Race cars).
    *   **Row 11:** Road zone (Bulldozers).
    *   **Row 12:** Road zone (Slow cars, bottom tier).
    *   **Row 13:** Safety median (Starting zone).
    *   **Row 14:** Bottom panel (Lives/Extra stats UI).

#### 2. Core Game Mechanics
*   **Objective:** Guide a frog from the bottom safety zone (Row 13) across a hazardous road and a treacherous river into one of the 5 empty home slots at the top (Row 1).
*   **Movement Mechanics:**
    *   Movement is discrete (grid-locked), not continuous. Pressing a directional key moves the frog exactly one tile (40 pixels) in that direction.
    *   Forward movement increases the player's score. Moving backward does not increase the score.
*   **Road Hazards (Collision Detection):**
    *   Rows 8 through 12 contain moving vehicles.
    *   If the frog's bounding box intersects with any vehicle's bounding box, the frog dies (loses a life, resets to the bottom).
*   **River Mechanics (Platforming):**
    *   Rows 2 through 6 contain water. The frog will drown if it lands directly in the water.
    *   The frog must land on moving platforms (logs and turtles).
    *   While on a log or turtle, the frog inherits the horizontal velocity of that platform (moves automatically with it each game tick).
    *   If the platform moves the frog off the left or right edges of the screen, the frog dies (drowns).
    *   Submerging turtles periodically sink; if the frog is on a turtle when it fully submerges, the frog dies. *(Note: Uncertainty applies to whether turtle submergence is strictly required for a basic MVP Turtle implementation).*
*   **Home Slots:**
    *   The top row contains 5 designated slots. 
    *   The frog must successfully navigate into an empty slot. 
    *   Once all 5 slots are filled, the level is cleared, and the game resets with increased difficulty (faster speeds).
*   **Timer:**
    *   A countdown timer runs per life. If it reaches zero before reaching a home slot, the frog dies.

#### 3. Key Control Mappings
Suitable mappings for a Python Turtle implementation using `screen.listen()` and `screen.onkey()`:

*   **Up Arrow / 'W':** Move Forward (Up 1 grid step / +Y by 40px).
*   **Down Arrow / 'S':** Move Backward (Down 1 grid step / -Y by 40px).
*   **Left Arrow / 'A':** Move Left (-X by 40px).
*   **Right Arrow / 'D':** Move Right (+X by 40px).

#### 4. Areas of Uncertainty / Implementation Notes for Turtle
*   **Performance (FPS):** Python's `turtle` module can suffer from sluggish rendering when updating many moving objects simultaneously. Using `screen.tracer(0)` and manual `screen.update()` loops (e.g., using `ontimer` set to ~30-50ms) is mandatory to achieve fluid traffic and log movement.
*   **Sprite Handling:** Native shapes (`"square"`, `"circle"`, `"triangle"`, `"classic"`) are built-in, but custom shapes require `.gif` images, which have strict format limitations in standard Python/Tkinter setups. Simple geometric polygons or custom stamp shapes are generally more reliable across platforms.
*   **Exact Hitboxes:** Bounding-box collision detection (`collision_distance < threshold`) must be carefully tuned to match the visual size of the 40x40 pixel grid cells to avoid frustrating "pixel-peeking" deaths.

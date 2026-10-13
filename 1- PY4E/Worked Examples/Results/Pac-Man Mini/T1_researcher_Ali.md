<!-- Task T1: Research the core mechanics, grid dimensions, and standard ghost/player behaviors of a classic Pac-Man game to inform implementation. -->

### 1. Grid Dimensions and Layout
*   **Total Grid Size:** The classic *Pac-Man* maze is structured on a grid measuring **28 columns wide by 36 rows high**.
*   **Playable Area:** Not all grid spaces are traversable. The active maze where Pac-Man and the ghosts move is typically 28 columns by 31 rows, with the top and bottom rows reserved for the score panel and user interface.
*   **Tile Scale:** In original hardware terms, the maze is built from tiles measuring $8 \times 8$ pixels, resulting in a total resolution of $224 \times 288$ pixels.
*   **The Tunnel:** A wrap-around tunnel is located on the middle row (Row 14, counting from the top of the playable area), allowing entities to transition instantly from the far left of the screen to the far right, and vice versa. Movement speed is intentionally reduced while traversing this tunnel.
*   **The Ghost House:** Centered in the middle of the maze is a rectangular enclosure (the "Ghost House") measuring roughly $8 \times 4$ tiles, featuring a single exit door at the top center through which ghosts leave and enter.

---

### 2. Core Mechanics
*   **Win/Loss Conditions:** 
    *   *Win:* Clear all 244 dots (240 standard pellets and 4 energizers) from the maze to advance to the next level.
    *   *Loss:* Lose all lives by colliding with a non-vulnerable ghost.
*   **Scoring Elements:**
    *   Small Dot: 10 points.
    *   Energizer (Power Pellet): 50 points.
    *   Ghosts (consecutive eats during a single energizer): 200, 400, 800, and 1600 points.
    *   Fruit (appears twice per round at 70 and 170 dots eaten): Ranges from 100 to 5,000 points depending on the current level.
*   **Intermissions:** Cutscenes (animations of interactions between Pac-Man and Blinky) trigger after specific levels (e.g., after levels 2, 5, 9, 13, and 17).
*   **Global Timer / Wave System:** The game alternates between two primary global states: **Scatter** (ghosts retreat to designated corner targets) and **Chase** (ghosts target Pac-Man directly). This cycle runs on a strict timer across 4 distinct waves per life/level before locking permanently into Chase mode for the remainder of that life.

---

### 3. Player (Pac-Man) Behavior
*   **Input Buffering & Turning:** Pac-Man moves continuously in his current heading unless blocked by a wall. Players can pre-input a turn before reaching an intersection; the game buffers this input and executes the turn at the exact grid tile where the path opens.
*   **Corner-Snapping (The "Cornering" Bug/Feature):** In the original arcade game, Pac-Man could turn into a corner slightly *before* his center alignment reached the intersection, allowing tight maneuvers. Modern implementations often approximate this via a small hitbox tolerance.
*   **Speed Variations:** 
    *   Pac-Man moves slightly slower while eating a dot (a microscopic frame-pause) compared to moving through empty corridors.
    *   Base speed is altered per level (e.g., higher levels increase speeds for both Pac-Man and ghosts, though Pac-Man’s speed ratio relative to ghosts fluctuates).

---

### 4. Standard Ghost Behaviors
Each of the four ghosts (Blinky, Pinky, Inky, Clyde) possesses a distinct AI targeting algorithm, though all share common movement rules: **Ghosts cannot reverse direction immediately** unless a global state change (Scatter/Chase toggle or Energizer consumption) forces a reversal. At any grid intersection, ghosts choose the tile that minimizes Euclidean distance to their target tile. In case of a tie, the priority rule is universally applied: **Up takes precedence over Left, which takes precedence over Down** (Up > Left > Down > Right).

*   **Blinky (Red - "Shadow"):**
    *   *Targeting:* Directly targets Pac-Man’s current tile in Chase mode.
    *   *Special Behavior:* Enters "Cruise Elroy" speed mode after a specific threshold of remaining dots is cleared, speeding up and aggressively pursuing Pac-Man regardless of the current Scatter/Chase timer.
*   **Pinky (Pink - "Speedy"):**
    *   *Targeting:* Targets 4 tiles ahead of Pac-Man's current direction. 
    *   *Special Behavior (Known Bug):* When Pac-Man faces *Up*, Pinky's targeting calculation historically bugs out, targeting 4 tiles Up *and* 4 tiles Left simultaneously due to an overflow error in the original code. Many modern clones replicate or fix this depending on design goals.
*   **Inky (Cyan - "Bashful"):**
    *   *Targeting:* Uses a vector calculation based on both Blinky and Pac-Man. It takes the tile 2 spaces ahead of Pac-Man, draws a vector from Blinky's position to that tile, and doubles the vector length to find its target tile. This makes Inky flank Pac-Man unpredictably based on Blinky's position.
*   **Clyde (Orange - "Pokey"):**
    *   *Targeting:* Dual-mode targeter. If Clyde is more than 8 grid tiles away from Pac-Man, he targets Pac-Man directly (like Blinky). If he comes within 8 tiles of Pac-Man, his target instantly switches to his designated Scatter corner (bottom-left), causing him to loop endlessly near his corner.
*   **Frightened State (Energizer Eaten):**
    *   When an energizer is consumed, all ghosts immediately reverse direction, pick pseudo-random turns at intersections, and move at a significantly reduced speed. They flash blue/white near the end of the timer to warn of expiration.
*   **Eaten State:**
    *   When eaten during a frightened state, the ghost's eyes return to a high-speed state, navigating via shortest-path routing back to the center of the Ghost House, where they regenerate and exit again.

---

### Areas of Uncertainty / Implementation Notes
*   *Exact Frame-Data Parity:* While general behaviors (targeting vectors, corner priorities) are well-documented via reverse-engineering (notably Jamey Pittman’s *The Pac-Man Dossier*), replicating the exact 60Hz integer overflow bugs (such as Pinky’s up/left targeting glitch) depends on whether the developer wants an exact hardware simulation or a polished modern clone. 
*   *Speed Tables:* Exact percentage values for speed adjustments per level (e.g., Level 1 vs. Level 5 vs. Level 21+) vary slightly depending on whether the reference implementation is taken from the original upright arcade ROM or later ports.

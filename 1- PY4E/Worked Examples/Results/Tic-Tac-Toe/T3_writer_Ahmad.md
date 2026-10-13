<!-- Task T3: Create a clear README document explaining how to run the Python turtle Tic-Tac-Toe game, including prerequisites and game controls. -->

# Python Turtle Tic-Tac-Toe

A classic, interactive **Tic-Tac-Toe** game built using Python's standard `turtle` graphics library. Enjoy a clean graphical interface with automatic turn management, win/tie detection, and smooth instant rendering.

---

## Prerequisites

To run this game, you only need:
* **Python 3.x** installed on your system. 
* The `turtle` module (which is included by default in the Python standard library, so no extra installations via `pip` are required).

---

## Getting Started

1. Save the game code into a file named **`tic_tac_toe.py`**.
2. Open your terminal or command prompt and navigate to the folder where you saved the file.
3. Run the game using the following command:
   ```bash
   python tic_tac_toe.py
   ```

---

## Game Controls

* **Player Turns:** Player **X** always goes first, followed by Player **O**. The current player's turn is displayed at the top of the game window.
* **Making a Move:** Use your **mouse** to click inside any of the 9 grid cells. 
  * Clicking an empty cell will place your mark (**X** in red or **O** in blue).
  * Clicking an already occupied cell or outside the grid will be ignored.
* **Winning & Ending:** The game automatically detects wins (3-in-a-row horizontally, vertically, or diagonally) and ties, instantly displaying the final result banner at the top of the screen.

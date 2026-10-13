<!-- Task T3: Write user documentation explaining how to run the game, the controls, and the gameplay rules. -->

# Dodge the Blocks – User Documentation

Welcome to **Dodge the Blocks**, a fast-paced arcade survival game built in Python using the `turtle` graphics module. Your objective is simple: survive as long as possible by dodging the falling obstacles!

---

## 1. System Requirements & How to Run

### Prerequisites
* **Python 3.x** installed on your system.
* The built-in `turtle` module (which comes pre-installed with standard Python distributions).

### Installation & Execution
1. Copy the game source code and save it into a file named `dodge_blocks.py`.
2. Open your terminal or command prompt and navigate to the directory where you saved the file.
3. Run the script using the following command:
   ```bash
   python dodge_blocks.py
   ```
4. A game window titled **"Dodge the Blocks"** will appear, displaying the start screen.

---

## 2. Game Controls

You can control your player character (the cyan rectangular dodger at the bottom of the screen) using either the arrow keys or standard WASD keys:

| Action | Control Keys |
| :--- | :--- |
| **Move Left** | Left Arrow **or** `A` key |
| **Move Right** | Right Arrow **or** `D` key |
| **Start / Restart** | `Spacebar` |
| **Quit Game** | `Escape` key |

*Note: The player character is bounded by the screen edges and cannot move off-screen.*

---

## 3. Gameplay Rules & Mechanics

* **Objective:** Avoid colliding with the falling red obstacle blocks for as long as possible to maximize your score.
* **Scoring:** Your score increases automatically the longer you survive. 
* **Difficulty Progression:** As your score increases, the speed of the falling blocks gradually increases, making the game progressively harder.
* **Game Over:** The game ends immediately if your player character comes into contact with any falling block. Upon game over, your final score and highest score achieved during the session will be displayed.
* **Restarting:** Press the **Spacebar** after a game over to reset the game and try again for a new high score.

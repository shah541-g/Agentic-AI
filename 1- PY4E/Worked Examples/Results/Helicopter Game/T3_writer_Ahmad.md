<!-- Task T3: Write a user-facing guide explaining how to install prerequisites, run the Python helicopter game script, and control the helicopter. -->

# Classic Helicopter Game: Installation & User Guide

Welcome to the Classic Helicopter Game! Navigate your helicopter through a procedurally generated cave system without crashing into the ceiling, floor, or walls. 

---

## 1. System Prerequisites

The game is written in Python and uses **Tkinter** for its graphical interface. 

* **Python 3.x:** Ensure you have Python installed on your system. You can download the latest version from [python.org](https://www.python.org/).
* **Zero Third-Party Dependencies:** Because the game relies entirely on Python’s built-in standard libraries (`tkinter` and `random`), **you do not need to install any external packages** (like `pip install ...`).

---

## 2. How to Run the Script

1. **Save the Code:** Copy the Python script provided by the coder and save it to a file named `helicopter_game.py`.
2. **Open Your Terminal:** Open your command prompt (Windows) or terminal (macOS/Linux) and navigate to the folder where you saved the file.
3. **Launch the Game:** Run the script using the following command:
   ```bash
   python helicopter_game.py
   ```
   *(On some systems, you may need to use `python3 helicopter_game.py`)*

---

## 3. Game Controls

Mastering the physics of the helicopter is the key to achieving a high score:

* **To Fly Up (Thrust):** **Press and hold** the **Spacebar** or the **Left Mouse Button** (`Button-1`). This activates the rotor lift, pushing the helicopter upward against gravity.
* **To Descend:** **Release** the Spacebar or Left Mouse Button. Gravity will naturally pull the helicopter back down toward the floor.
* **Restarting:** After a crash, press the **Spacebar** or click the **Left Mouse Button** to instantly restart a new game.

### Gameplay Tips
* Avoid holding down the thrust continuously; tap or feather the control button to maintain a steady altitude through changing tunnel heights.
* Keep an eye on your live score and personal high score displayed at the top corners of the screen!

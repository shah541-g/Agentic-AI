<!-- Task T3: Create clear instructions and documentation on how to run the Whack-a-Mole Python turtle game, explaining the controls and game rules. -->

# Whack-a-Mole Game Documentation

Welcome to the official documentation and user guide for the **Whack-a-Mole** Python game built using the built-in `turtle` graphics module. 

---

## 1. System Requirements & Installation

This game relies solely on Python's standard library, meaning you do not need to install any external packages (like Pygame).

* **Python Version:** Python 3.6 or higher recommended.
* **Dependencies:** The built-in `turtle` and `random` modules.

### How to Run the Game
1. Copy the Python source code provided by the development team and save it into a file named `whack_a_mole.py`.
2. Open your terminal, command prompt, or preferred IDE (such as VS Code or PyCharm) in the directory where you saved the file.
3. Execute the following command:
   ```bash
   python whack_a_mole.py
   ```
4. A 600x600 pixel graphical window titled **"Whack-a-Mole!"** will automatically appear, and the game will begin immediately.

---

## 2. Game Rules & Objective

* **Objective:** Score as many points as possible before the countdown timer hits zero.
* **Time Limit:** Each game lasts **30 seconds**.
* **Scoring:** 
  * Every time a mole pops up out of a brown hole, you must click directly on it.
  * Successfully clicking an active mole awards **1 point**.
  * Clicking on empty holes or clicking when no mole is visible does not award points or penalize you.
* **Game Over:** Once the 30-second timer expires, the moles will stop appearing, and your **Final Score** will be displayed in the center of the screen in large yellow text.

---

## 3. Controls

* **Device:** Mouse or Trackpad.
* **Action:** **Left-Click** directly on the brown mole when it emerges from any of the $3 \times 3$ grid holes. 
* *Note:* Moles only stay visible for a limited window of time (~800 milliseconds) before ducking back down, so speed and accuracy are crucial!

---

## 4. Configuration Constants (For Developers/Tinkurers)

If you want to customize the difficulty or pacing of the game, you can modify the following configuration constants found at the top of the `whack_a_mole.py` script:

* `MOLE_SHOW_TIME`: Duration (in milliseconds) that the mole stays visible on the screen. *(Default: 800ms)*
* `SPAWN_INTERVAL`: Frequency (in milliseconds) at which new moles attempt to pop up. *(Default: 1100ms)*
* `GAME_DURATION`: Total length of a single game session in seconds. *(Default: 30s)*

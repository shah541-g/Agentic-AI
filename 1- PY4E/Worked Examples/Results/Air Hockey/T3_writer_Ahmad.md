<!-- Task T3: Write a clear user guide and setup instructions explaining how to run the Python air hockey script and detailing the keyboard controls for both players. -->

# Python Air Hockey: User Guide & Setup Instructions

Welcome to the **Python Air Hockey** game! This guide provides all the necessary instructions to set up, run, and play the game using the built-in Python `turtle` graphics library.

---

## 🛠️ System Requirements & Setup Instructions

### Prerequisites
* **Python 3.x** installed on your system.
* The `turtle` module (which is a standard part of the Python Standard Library, so no external installations via `pip` are required).

### How to Run the Script
1. Save the provided Python script into a file named **`air_hockey.py`**.
2. Open your terminal, command prompt, or preferred code editor (like VS Code or PyCharm).
3. Navigate to the directory where you saved the file.
4. Execute the script using the following command:
   ```bash
   python air_hockey.py
   ```
5. A graphical game window titled **"Python Air Hockey"** will automatically open, and the game will start.

---

## 🎮 Game Controls

The game is designed for **two players** playing locally on the same keyboard. Each player is restricted to their respective half of the rink.

### **Player 1 (Left Side)**
* **Move Up:** `W`
* **Move Down:** `S`
* **Move Left:** `A`
* **Move Right:** `D`
* *Movement boundary:* Confined strictly to the left half of the rink (X-axis: -360 to -20).

### **Player 2 (Right Side)**
* **Move Up:** `Up Arrow`
* **Move Down:** `Down Arrow`
* **Move Left:** `Left Arrow`
* **Move Right:** `Right Arrow`
* *Movement boundary:* Confined strictly to the right half of the rink (X-axis: 20 to 360).

---

## 🎯 Gameplay Rules & Objective
* **Objective:** Strike the red puck into your opponent’s goal box to score points.
* **Scoring:** The current score is displayed at the top center of the screen in **Player A : Player B** format. 
* **Puck Reset:** Whenever a goal is scored, the game pauses briefly before resetting the puck to the center circle, serving it toward the conceding player.
* **Physics:** Hitting the puck at different angles and speeds with your paddle will dynamically alter its trajectory and speed.

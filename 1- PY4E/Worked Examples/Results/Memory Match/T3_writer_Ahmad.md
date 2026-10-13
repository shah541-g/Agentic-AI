<!-- Task T3: Create documentation and a README file explaining how to run the Memory Match game and the rules to play. -->

# Memory Match Game - Python Turtle

A classic **Memory Match** (Concentration) game built using Python and the built-in `turtle` graphics library. Test your memory by flipping cards to find matching pairs of emojis before time runs out or until the entire board is cleared!

---

## 🎮 Game Rules

1. **The Board:** The game is played on a $4 \times 4$ grid consisting of 16 face-down cards. These cards conceal 8 unique pairs of matching emoji symbols.
2. **Taking a Turn:** 
   * Click on any face-down card to flip it over and reveal its hidden symbol.
   * Click on a second face-down card to try and find its matching pair.
3. **Evaluating Matches:**
   * **If they match:** Both cards will turn green and remain locked face-up on the board. Your matched pairs counter will increase.
   * **If they do not match:** The cards will remain visible for 1 second so you can memorize their positions, then they will automatically flip back over to their hidden state.
4. **Winning the Game:** Continue flipping cards and clearing pairs until all 8 pairs are found. A celebratory message will appear at the top of the screen when you win!

---

## 🛠️ Prerequisites & System Requirements

* **Python 3.x** installed on your system.
* The `turtle` module comes pre-installed with standard Python distributions on Windows, macOS, and Linux (though Linux users may occasionally need to install the `python3-tk` package via their system package manager if Tkinter isn't present).

---

## 🚀 How to Run the Game

1. **Save the Code:** Copy the Python script into a file named `memory_match.py`.
2. **Open Your Terminal / Command Prompt:** Navigate to the folder where you saved the file.
3. **Run the Script:** Execute the following command:

```bash
python memory_match.py
```

4. **Play:** A graphical window titled `"Memory Match Game - Python Turtle"` will open, presenting the game board. Use your mouse to click and play!

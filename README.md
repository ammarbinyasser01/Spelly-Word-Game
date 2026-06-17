# Spelly Word Game

A Python-based word chain game with a GUI, AI opponent, SQLite database, and hint system — built as part of **AI Task #03** at **Gexton Education** under **Sir Muhammad Arham MH**.

---


## 🎮 How to Play

1. Enter your name and click **Start Game**
2. A random seed word is shown on screen
3. You must enter a valid English word that **starts with the last letter** of the current word
4. The AI takes its turn after you
5. No word can be used twice
6. Your score = total letters of all words you played
7. The player who forces the opponent to run out of words **wins**

---

## ✨ Features

| Feature | Description |
|---|---|
| 🎮 Word Chain Game | Each word must start with the last letter of the previous word |
| 🤖 AI Opponent | AI automatically picks a valid word on its turn |
| 💡 Hint System | Reveals a partially masked example of a valid next word |
| 🔀 Shuffled Letters | Current word shown with scrambled letters as a visual challenge |
| 📊 Score Tracking | Score increases by the length of each word you play |
| 📚 Word Validation | Words validated against the MIT 10,000-word list |
| 🗄️ Word Manager | Full CRUD — Add, Update, Delete, Search custom words via SQLite |
| 🌑 Dark Mode UI | Clean dark-themed interface built with Tkinter |

---

## 📁 Project Structure

```
spelly-word-game/
│
├── spelly.py       # Main source code (single file)
├── README.md            # This file
└── requirements.txt        # List of libraries used
```

---

## ⚙️ Requirements

- Python 3.10 or higher
- Internet connection on first launch (to download the MIT word list)

### Libraries Used

| Library | Purpose | Install needed? |
|---|---|---|
| `tkinter` | GUI framework | ❌ Built-in |
| `sqlite3` | Local database (CRUD) | ❌ Built-in |
| `random` | Shuffle letters, AI word pick | ❌ Built-in |
| `time` | AI thinking delay | ❌ Built-in |
| `threading` | Non-blocking AI turn | ❌ Built-in |
| `urllib` | Download MIT word list | ❌ Built-in |
| `PyDictionary` | Word definitions for hints (optional) | ✅ `pip install PyDictionary` |

---

## 🚀 Installation & Running

### 1. Clone the repository
```bash
git clone https://github.com/your-username/spelly-word-game.git
cd spelly-word-game
```

### 2. (Optional) Install PyDictionary for better hints
```bash
pip install PyDictionary
```
> If not installed, the hint system still works — it shows the first letter, last letter, and length of a valid word instead of a definition.

### 3. Run the game
```bash
python spelly_game.py
```

> On first launch, the game will automatically download the MIT 10,000-word list from the internet. If offline, a built-in fallback word set is used.

---

## 🗄️ Word Manager (CRUD)

Switch to the **Word Manager** tab to manage your custom word database:

- **Add** — Add a new custom word to the SQLite database
- **Update** — Select a word from the list and replace it
- **Delete** — Select a word and remove it from the database
- **Search** — Filter the word list in real time by typing
- **Refresh** — Reload the list from the database

> Custom words added here are immediately available for gameplay.

---

## 🧠 Game Rules

1. Each player's word must **start with the last letter** of the previous word
2. **No word can be repeated** during a game session
3. Words must be **valid English words** (from the MIT word list or your custom DB)
4. Score = number of letters in each word you play
5. If a player (or AI) cannot find a valid word, the other player **wins**

---

## 💡 Hint System

Pressing **Hint** during your turn:
- Finds a valid word you *could* play next (starting with the required letter)
- Shows it partially masked, e.g.: `e _ _ _ _ t  (6 letters, starts with 'E')`
- If PyDictionary is installed, also shows the word's definition
- The hint is logged in the Game Log

---

## 🛠️ Built With

- **Python 3** — Core language
- **Tkinter** — GUI (dark-themed interface)
- **SQLite3** — Local word database
- **MIT 10,000 Word List** — Word validation source

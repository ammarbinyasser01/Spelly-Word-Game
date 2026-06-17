import tkinter as tk
from tkinter import messagebox, simpledialog
import sqlite3
import random
import time
import threading
import urllib.request

# Optional PyDictionary for hints
try:
    from PyDictionary import PyDictionary
    dictionary = PyDictionary()
    HAS_DICT = True
except:
    HAS_DICT = False

# ── Dark theme colors ──────────────────────────────────────
BG      = "#1E1E2E"   # main background
SURFACE = "#2A2A3E"   # cards / panels
BORDER  = "#3A3A5C"   # borders
FG      = "#CDD6F4"   # primary text
SUBFG   = "#7F849C"   # muted text
BLUE    = "#89B4FA"   # accent blue
GREEN   = "#A6E3A1"   # success / player
RED     = "#F38BA8"   # error / AI
YELLOW  = "#F9E2AF"   # warning / hint
ENTRY   = "#313244"   # entry background


# ─────────────────────────────────────────
#  DATABASE  (SQLite3 CRUD)
# ─────────────────────────────────────────
def init_db():
    conn = sqlite3.connect("spelly.db")
    conn.execute("CREATE TABLE IF NOT EXISTS words (word TEXT UNIQUE)")
    conn.commit()
    return conn

def db_add(conn, word):
    try:
        conn.execute("INSERT INTO words VALUES (?)", (word,))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False

def db_get_all(conn):
    return [r[0] for r in conn.execute("SELECT word FROM words ORDER BY word")]

def db_update(conn, old, new):
    try:
        cur = conn.execute("UPDATE words SET word=? WHERE word=?", (new, old))
        conn.commit()
        return cur.rowcount > 0   # FIX: use cursor rowcount, not conn.total_changes
    except sqlite3.IntegrityError:
        return False

def db_delete(conn, word):
    cur = conn.execute("DELETE FROM words WHERE word=?", (word,))
    conn.commit()
    return cur.rowcount > 0       # FIX: use cursor rowcount


# ─────────────────────────────────────────
#  LOAD WORD LIST  (MIT 10000 words)
# ─────────────────────────────────────────
def load_word_list(conn):
    try:
        url  = "https://www.mit.edu/~ecprice/wordlist.10000"
        data = urllib.request.urlopen(url, timeout=8).read().decode()
        words = set(w.strip().lower() for w in data.splitlines() if w.strip())
    except:
        words = {
            "apple","eel","lion","newt","tiger","rat","elephant","table",
            "enter","red","dog","goat","tree","egg","ghost","top","pin",
            "night","hat","ant","net","tail","lake","end","dart","ring",
            "oak","key","yarn","note","ear","rain","noon","open","name",
        }
    for w in db_get_all(conn):    # merge custom DB words into valid set
        words.add(w)
    return words


# ─────────────────────────────────────────
#  AI OPPONENT
# ─────────────────────────────────────────
def ai_pick_word(letter, used, word_list):
    candidates = [
        w for w in word_list
        if w.startswith(letter) and w not in used and len(w) >= 3
    ]
    return random.choice(candidates) if candidates else None


# ─────────────────────────────────────────
#  HINT  (FIX: hint helps player find a
#  word starting with the required letter,
#  not reveal the already-visible cur_word)
# ─────────────────────────────────────────
def get_hint(required_letter, used, word_list):
    """
    Give the player a hint: find an example valid word they could play
    that starts with the required letter, and reveal it partially.
    e.g.  required='e'  →  "Hint: e _ _ _ (4 letters)"
    """
    candidates = [
        w for w in word_list
        if w.startswith(required_letter) and w not in used and len(w) >= 3
    ]
    if not candidates:
        return f"No available words starting with '{required_letter.upper()}' found!"

    # Pick a random candidate and partially reveal it
    word = random.choice(candidates)

    if HAS_DICT:
        try:
            meaning = dictionary.meaning(word)
            if meaning:
                pos  = list(meaning.keys())[0]
                defn = meaning[pos][0]
                # Show only first letter + blanks + length, plus definition
                masked = word[0] + " _ " * (len(word) - 1)
                return f"Hint: '{masked.strip()}'  — {pos}: {defn}"
        except:
            pass

    # Fallback: show first letter, last letter, length
    masked = word[0] + "_ " * (len(word) - 2) + word[-1]
    return f"Hint: '{masked}'  ({len(word)} letters, starts with '{word[0].upper()}')"


# ─────────────────────────────────────────
#  MAIN APP
# ─────────────────────────────────────────
class SpellyApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Spelly Word Game")
        self.geometry("700x600")
        self.resizable(False, False)
        self.configure(bg=BG)

        self.conn      = init_db()
        self.word_list = load_word_list(self.conn)
        self.used      = set()
        self.cur_word  = ""
        self.p_score   = 0
        self.ai_score  = 0
        self.my_turn   = True
        self.playing   = False

        self._build()

    # ──────────────────────────────────────
    #  BUILD UI
    # ──────────────────────────────────────
    def _build(self):
        # Title
        tk.Label(self, text="SPELLY WORD GAME", font=("Arial", 18, "bold"),
                 bg=BG, fg=BLUE).pack(pady=(14, 2))
        tk.Label(self,
                 text="Chain words — each word must start with the last letter of the previous one.",
                 font=("Arial", 9), bg=BG, fg=SUBFG).pack()
        tk.Frame(self, height=1, bg=BORDER).pack(fill="x", padx=20, pady=8)

        # Tab buttons
        tab_bar = tk.Frame(self, bg=BG)
        tab_bar.pack()
        self.btn_gtab = tk.Button(tab_bar, text="Game", width=12,
            command=lambda: self._show_tab("game"),
            relief="flat", bg=BLUE, fg=BG, font=("Arial", 10, "bold"), cursor="hand2")
        self.btn_gtab.pack(side="left", padx=4)
        self.btn_wtab = tk.Button(tab_bar, text="Word Manager", width=14,
            command=lambda: self._show_tab("words"),
            relief="flat", bg=SURFACE, fg=SUBFG, font=("Arial", 10), cursor="hand2")
        self.btn_wtab.pack(side="left", padx=4)

        # ── GAME PANEL ──────────────────────
        self.game_panel = tk.Frame(self, bg=BG)

        # Score row
        srow = tk.Frame(self.game_panel, bg=SURFACE, pady=7)
        srow.pack(fill="x", padx=20, pady=(10, 0))
        self.lbl_ps = tk.Label(srow, text="You: 0", font=("Arial", 11, "bold"),
                               bg=SURFACE, fg=GREEN)
        self.lbl_ps.pack(side="left", padx=16)
        self.lbl_turn = tk.Label(srow, text="", font=("Arial", 11),
                                 bg=SURFACE, fg=SUBFG)
        self.lbl_turn.pack(side="left", expand=True)
        self.lbl_ais = tk.Label(srow, text="AI: 0", font=("Arial", 11, "bold"),
                                bg=SURFACE, fg=RED)
        self.lbl_ais.pack(side="right", padx=16)

        # Word display card
        wbox = tk.Frame(self.game_panel, bg=SURFACE, pady=14)
        wbox.pack(fill="x", padx=20, pady=10)

        tk.Label(wbox, text="Current Word", font=("Arial", 9),
                 bg=SURFACE, fg=SUBFG).pack()
        self.lbl_word = tk.Label(wbox, text="—", font=("Arial", 26, "bold"),
                                 bg=SURFACE, fg=FG)
        self.lbl_word.pack()

        tk.Label(wbox, text="Shuffled Letters", font=("Arial", 9),
                 bg=SURFACE, fg=SUBFG).pack(pady=(6, 0))
        self.lbl_shuf = tk.Label(wbox, text="", font=("Courier New", 13, "bold"),
                                 bg=SURFACE, fg=BLUE)
        self.lbl_shuf.pack()

        tk.Label(wbox, text="Your word must start with:", font=("Arial", 9),
                 bg=SURFACE, fg=SUBFG).pack(pady=(8, 0))
        self.lbl_req = tk.Label(wbox, text="", font=("Arial", 22, "bold"),
                                bg=SURFACE, fg=YELLOW)
        self.lbl_req.pack()

        # Input row
        inp = tk.Frame(self.game_panel, bg=BG)
        inp.pack(pady=8)
        self.word_var = tk.StringVar()
        self.entry = tk.Entry(inp, textvariable=self.word_var, font=("Arial", 13),
                              width=20, bg=ENTRY, fg=FG, insertbackground=FG,
                              relief="flat", bd=6)
        self.entry.pack(side="left", padx=(0, 6))
        self.entry.bind("<Return>", lambda e: self._submit())

        tk.Button(inp, text="Submit", command=self._submit, width=8,
                  bg=BLUE, fg=BG, relief="flat", cursor="hand2",
                  font=("Arial", 10, "bold")).pack(side="left", padx=2)
        tk.Button(inp, text="Hint", command=self._hint, width=6,
                  bg=YELLOW, fg=BG, relief="flat", cursor="hand2",
                  font=("Arial", 10, "bold")).pack(side="left", padx=2)

        # Status
        self.lbl_status = tk.Label(self.game_panel, text="", font=("Arial", 10),
                                   bg=BG, fg=FG, wraplength=620)
        self.lbl_status.pack(pady=2)

        # Log
        tk.Label(self.game_panel, text="Game Log", font=("Arial", 9),
                 bg=BG, fg=SUBFG).pack(anchor="w", padx=22)
        lf = tk.Frame(self.game_panel, bg=BG)
        lf.pack(fill="both", expand=True, padx=20, pady=(0, 6))
        self.log = tk.Text(lf, height=7, font=("Arial", 9), bg=SURFACE, fg=FG,
                           relief="flat", bd=0, state="disabled", wrap="word",
                           insertbackground=FG)
        self.log.pack(side="left", fill="both", expand=True)
        sb = tk.Scrollbar(lf, bg=SURFACE, command=self.log.yview)
        sb.pack(side="right", fill="y")
        self.log.configure(yscrollcommand=sb.set)

        # Bottom buttons
        bot = tk.Frame(self.game_panel, bg=BG)
        bot.pack(pady=6)
        tk.Button(bot, text="New Game", command=self._new_game, width=10,
                  bg=GREEN, fg=BG, relief="flat", cursor="hand2",
                  font=("Arial", 10, "bold")).pack(side="left", padx=8)
        tk.Button(bot, text="End Game", command=self._end_game, width=10,
                  bg=RED, fg=BG, relief="flat", cursor="hand2",
                  font=("Arial", 10, "bold")).pack(side="left", padx=8)

        # Start screen overlay
        self.start_screen = tk.Frame(self.game_panel, bg=BG)
        self.start_screen.place(relx=0, rely=0, relwidth=1, relheight=1)
        tk.Label(self.start_screen, text="Welcome to Spelly!", font=("Arial", 16, "bold"),
                 bg=BG, fg=BLUE).pack(pady=(80, 4))
        tk.Label(self.start_screen, text="Enter your name to begin", font=("Arial", 10),
                 bg=BG, fg=SUBFG).pack(pady=(0, 16))
        self.name_var = tk.StringVar(value="Player")
        tk.Entry(self.start_screen, textvariable=self.name_var, font=("Arial", 12),
                 width=20, bg=ENTRY, fg=FG, insertbackground=FG,
                 relief="flat", bd=6, justify="center").pack(pady=4)
        tk.Button(self.start_screen, text="Start Game", command=self._start,
                  bg=BLUE, fg=BG, font=("Arial", 12, "bold"),
                  relief="flat", padx=20, pady=6, cursor="hand2").pack(pady=16)

        # ── WORD MANAGER PANEL ──────────────
        self.word_panel = tk.Frame(self, bg=BG)

        tk.Label(self.word_panel, text="Word Database Manager", font=("Arial", 13, "bold"),
                 bg=BG, fg=BLUE).pack(pady=12)

        sf = tk.Frame(self.word_panel, bg=BG)
        sf.pack(fill="x", padx=20, pady=(0, 6))
        tk.Label(sf, text="Search:", font=("Arial", 10), bg=BG, fg=SUBFG).pack(side="left")
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *_: self._filter())
        tk.Entry(sf, textvariable=self.search_var, font=("Arial", 10), width=24,
                 bg=ENTRY, fg=FG, insertbackground=FG, relief="flat", bd=6).pack(side="left", padx=8)

        lb_frame = tk.Frame(self.word_panel, bg=BG)
        lb_frame.pack(fill="both", expand=True, padx=20)
        self.listbox = tk.Listbox(lb_frame, font=("Arial", 11), bg=SURFACE, fg=FG,
                                  selectbackground=BLUE, selectforeground=BG,
                                  relief="flat", bd=0, activestyle="none",
                                  highlightthickness=0)
        self.listbox.pack(side="left", fill="both", expand=True)
        sb2 = tk.Scrollbar(lb_frame, bg=SURFACE, command=self.listbox.yview)
        sb2.pack(side="right", fill="y")
        self.listbox.configure(yscrollcommand=sb2.set)

        crud = tk.Frame(self.word_panel, bg=BG)
        crud.pack(pady=10)
        for txt, cmd, color in [
            ("Add",     self._add,     GREEN),
            ("Update",  self._update,  YELLOW),
            ("Delete",  self._delete,  RED),
            ("Refresh", self._refresh, BLUE),
        ]:
            tk.Button(crud, text=txt, command=cmd, width=9,
                      bg=color, fg=BG, relief="flat", cursor="hand2",
                      font=("Arial", 10, "bold")).pack(side="left", padx=5)

        self.lbl_db = tk.Label(self.word_panel, text="", font=("Arial", 9),
                               bg=BG, fg=SUBFG)
        self.lbl_db.pack(pady=4)

        self._refresh()
        self._show_tab("game")

    # ──────────────────────────────────────
    #  TAB SWITCHING
    # ──────────────────────────────────────
    def _show_tab(self, tab):
        self.game_panel.pack_forget()
        self.word_panel.pack_forget()
        if tab == "game":
            self.game_panel.pack(fill="both", expand=True)
            self.btn_gtab.config(bg=BLUE, fg=BG)
            self.btn_wtab.config(bg=SURFACE, fg=SUBFG)
        else:
            self.word_panel.pack(fill="both", expand=True)
            self.btn_wtab.config(bg=BLUE, fg=BG)
            self.btn_gtab.config(bg=SURFACE, fg=SUBFG)

    # ──────────────────────────────────────
    #  GAME LOGIC
    # ──────────────────────────────────────
    def _start(self):
        self.player_name = self.name_var.get().strip() or "Player"
        self.used     = set()
        self.p_score  = 0
        self.ai_score = 0
        self.my_turn  = True
        self.playing  = True
        self.cur_word = random.choice(list(self.word_list))
        self.used.add(self.cur_word)
        self.start_screen.place_forget()
        self._log(f"Game started!  Seed word: {self.cur_word}")
        self._update_ui()
        self.entry.focus()

    def _update_ui(self):
        self.lbl_word.config(text=self.cur_word.upper())
        shuf = list(self.cur_word)
        random.shuffle(shuf)
        self.lbl_shuf.config(text="  ".join(shuf).upper())
        self.lbl_req.config(text=self.cur_word[-1].upper())
        self.lbl_ps.config(text=f"{self.player_name}: {self.p_score}")
        self.lbl_ais.config(text=f"AI: {self.ai_score}")
        self.lbl_turn.config(text="Your turn" if self.my_turn else "AI's turn")

    def _submit(self):
        if not self.playing or not self.my_turn:
            return
        word = self.word_var.get().strip().lower()
        self.word_var.set("")
        if not word:
            return
        if word[0] != self.cur_word[-1]:
            self._status(f"Must start with '{self.cur_word[-1].upper()}'", RED)
            return
        if word in self.used:
            self._status("That word was already used!", RED)
            return
        if word not in self.word_list:
            self._status("Not a valid English word.", RED)
            return
        # Accept word
        self.used.add(word)
        self.cur_word  = word
        self.p_score  += len(word)
        self.my_turn   = False
        self._status(f"Nice!  +{len(word)} pts", GREEN)
        self._log(f"  You  »  {word}  (+{len(word)})")
        self._update_ui()
        self.after(800, self._ai_turn)

    def _ai_turn(self):
        self.entry.config(state="disabled")
        self._status("AI is thinking…", SUBFG)

        def run():
            time.sleep(1)
            word = ai_pick_word(self.cur_word[-1], self.used, self.word_list)
            self.after(0, lambda: self._ai_done(word))

        threading.Thread(target=run, daemon=True).start()

    def _ai_done(self, word):
        self.entry.config(state="normal")
        if not word:
            self._status("AI has no words left — You win!", GREEN)
            self._log("  AI gave up — YOU WIN!")
            self.playing = False
            return
        self.used.add(word)
        self.cur_word  = word
        self.ai_score += len(word)
        self.my_turn   = True
        self._status(f"AI played: {word.upper()}", RED)
        self._log(f"  AI   »  {word}  (+{len(word)})")
        self._update_ui()
        self.entry.focus()

    def _hint(self):
        if not self.playing:
            return
        # FIX: pass required_letter so hint helps player pick their NEXT word
        required = self.cur_word[-1]
        hint_text = get_hint(required, self.used, self.word_list)
        self._status(hint_text, YELLOW)
        self._log(f"  [Hint] {hint_text}")

    def _new_game(self):
        if self.playing and not messagebox.askyesno("New Game", "Start a new game?"):
            return
        self.playing = False
        self._clear_log()
        self._status("")
        self.lbl_word.config(text="—")
        self.lbl_shuf.config(text="")
        self.lbl_req.config(text="")
        self.lbl_turn.config(text="")
        self.lbl_ps.config(text="You: 0")
        self.lbl_ais.config(text="AI: 0")
        self.start_screen.place(relx=0, rely=0, relwidth=1, relheight=1)

    def _end_game(self):
        if not self.playing:
            return
        self.playing = False
        if self.p_score > self.ai_score:
            winner = f"{self.player_name} wins!"
        elif self.ai_score > self.p_score:
            winner = "AI wins!"
        else:
            winner = "It's a draw!"
        messagebox.showinfo("Game Over",
            f"{self.player_name}: {self.p_score} pts\nAI: {self.ai_score} pts\n\n{winner}")
        self._new_game()

    def _status(self, msg, color=FG):
        self.lbl_status.config(text=msg, fg=color)

    def _log(self, msg):
        self.log.config(state="normal")
        self.log.insert("end", msg + "\n")
        self.log.see("end")
        self.log.config(state="disabled")

    def _clear_log(self):
        self.log.config(state="normal")
        self.log.delete("1.0", "end")
        self.log.config(state="disabled")

    # ──────────────────────────────────────
    #  WORD MANAGER  (CRUD)
    # ──────────────────────────────────────
    def _refresh(self):
        # FIX: also sync word_list with current DB state
        self.word_list.update(db_get_all(self.conn))
        self.listbox.delete(0, "end")
        for w in db_get_all(self.conn):
            self.listbox.insert("end", w)
        self.lbl_db.config(
            text=f"{self.listbox.size()} custom word(s) in database.", fg=SUBFG)

    def _filter(self):
        q = self.search_var.get().lower()
        self.listbox.delete(0, "end")
        for w in db_get_all(self.conn):
            if q in w:
                self.listbox.insert("end", w)

    def _add(self):
        word = simpledialog.askstring("Add Word", "Enter new word:", parent=self)
        if not word:
            return
        word = word.strip().lower()
        if not word.isalpha():
            messagebox.showerror("Error", "Only letters are allowed.")
            return
        if db_add(self.conn, word):
            self.word_list.add(word)   # FIX: immediately add to live word_list
            self._refresh()
            self.lbl_db.config(text=f"'{word}' added successfully.", fg=GREEN)
        else:
            self.lbl_db.config(text=f"'{word}' already exists in database.", fg=YELLOW)

    def _update(self):
        sel = self.listbox.curselection()
        if not sel:
            messagebox.showwarning("Update", "Please select a word to update.")
            return
        old = self.listbox.get(sel[0])
        new = simpledialog.askstring("Update Word", f"Replace '{old}' with:", parent=self)
        if not new:
            return
        new = new.strip().lower()
        if not new.isalpha():
            messagebox.showerror("Error", "Only letters are allowed.")
            return
        if db_update(self.conn, old, new):
            self.word_list.discard(old)   # FIX: remove old from live word_list
            self.word_list.add(new)       # FIX: add new to live word_list
            self._refresh()
            self.lbl_db.config(text=f"'{old}' updated to '{new}'.", fg=GREEN)
        else:
            self.lbl_db.config(text=f"Update failed — '{new}' may already exist.", fg=RED)

    def _delete(self):
        sel = self.listbox.curselection()
        if not sel:
            messagebox.showwarning("Delete", "Please select a word to delete.")
            return
        word = self.listbox.get(sel[0])
        if messagebox.askyesno("Delete", f"Delete '{word}' from the database?"):
            if db_delete(self.conn, word):
                self.word_list.discard(word)   # FIX: remove from live word_list
                self._refresh()
                self.lbl_db.config(text=f"'{word}' deleted.", fg=RED)
            else:
                self.lbl_db.config(text=f"Delete failed.", fg=RED)

    def destroy(self):
        self.conn.close()
        super().destroy()


# ─────────────────────────────────────────
if __name__ == "__main__":
    app = SpellyApp()
    app.mainloop()
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import sqlite3
import os
import hashlib
import time
import random
import threading

# =====================================================================
# Constants & Theme Definitions
# =====================================================================
THEMES = {
    "Cyberpunk Dark": {
        "bg": "#0B0C10",
        "card_bg": "#1F2833",
        "accent": "#66FCF1",
        "secondary": "#45A29E",
        "text": "#FFFFFF",
        "muted": "#C5C6C7",
        "error": "#FF007F",
        "correct": "#00FF66",
        "btn_fg": "#0B0C10",
        "kbd_highlight": "#FFB703"
    },
    "Classic Light": {
        "bg": "#F5F7FA",
        "card_bg": "#FFFFFF",
        "accent": "#4A90E2",
        "secondary": "#CBD5E0",
        "text": "#2D3748",
        "muted": "#718096",
        "error": "#E53E3E",
        "correct": "#38A169",
        "btn_fg": "#FFFFFF",
        "kbd_highlight": "#ED8936"
    },
    "Forest Minimalist": {
        "bg": "#1E2522",
        "card_bg": "#2A3430",
        "accent": "#A2E8DD",
        "secondary": "#4E615D",
        "text": "#E6ECE9",
        "muted": "#8D9B97",
        "error": "#E57373",
        "correct": "#81C784",
        "btn_fg": "#1E2522",
        "kbd_highlight": "#FFB703"
    }
}

# Key widths mapping to construct a 15-unit grid layout keyboard
KEYBOARD_LAYOUT = [
    # Row 0
    [("`", 1.0), ("1", 1.0), ("2", 1.0), ("3", 1.0), ("4", 1.0), ("5", 1.0), 
     ("6", 1.0), ("7", 1.0), ("8", 1.0), ("9", 1.0), ("0", 1.0), ("-", 1.0), 
     ("=", 1.0), ("Backspace", 2.0)],
    # Row 1
    [("Tab", 1.5), ("q", 1.0), ("w", 1.0), ("e", 1.0), ("r", 1.0), ("t", 1.0), 
     ("y", 1.0), ("u", 1.0), ("i", 1.0), ("o", 1.0), ("p", 1.0), ("[", 1.0), 
     ("]", 1.0), ("\\", 1.5)],
    # Row 2
    [("Caps", 1.8), ("a", 1.0), ("s", 1.0), ("d", 1.0), ("f", 1.0), ("g", 1.0), 
     ("h", 1.0), ("j", 1.0), ("k", 1.0), ("l", 1.0), (";", 1.0), ("'", 1.0), 
     ("Enter", 2.2)],
    # Row 3
    [("Shift_L", 2.3), ("z", 1.0), ("x", 1.0), ("c", 1.0), ("v", 1.0), ("b", 1.0), 
     ("n", 1.0), ("m", 1.0), (",", 1.0), (".", 1.0), ("/", 1.0), ("Shift_R", 2.7)],
    # Row 4
    [("Ctrl_L", 1.5), ("Win_L", 1.25), ("Alt_L", 1.25), ("space", 6.0), 
     ("Alt_R", 1.25), ("Win_R", 1.25), ("Ctrl_R", 1.5)]
]

# =====================================================================
# Database Manager
# =====================================================================
class DBManager:
    def __init__(self, db_path="typing_software.db"):
        self.db_path = db_path
        self.init_db()

    def get_connection(self):
        return sqlite3.connect(self.db_path)

    def init_db(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS lessons (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                level TEXT NOT NULL,
                content TEXT NOT NULL
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS progress (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                lesson_id INTEGER NOT NULL,
                wpm REAL NOT NULL,
                accuracy REAL NOT NULL,
                completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS game_scores (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                game_name TEXT NOT NULL,
                score INTEGER NOT NULL,
                level_reached INTEGER NOT NULL,
                played_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                user_id INTEGER PRIMARY KEY,
                theme TEXT DEFAULT 'Cyberpunk Dark',
                sound_enabled INTEGER DEFAULT 1,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS key_errors (
                user_id INTEGER NOT NULL,
                key_char TEXT NOT NULL,
                error_count INTEGER DEFAULT 0,
                PRIMARY KEY (user_id, key_char),
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)

        # Check if we need to initialize or re-seed lessons to have 1000+ words
        needs_seed = False
        cursor.execute("SELECT COUNT(*) FROM lessons")
        if cursor.fetchone()[0] == 0:
            needs_seed = True
        else:
            cursor.execute("SELECT content FROM lessons LIMIT 1")
            first_content = cursor.fetchone()
            if first_content and len(first_content[0].split()) < 100:
                needs_seed = True

        if needs_seed:
            cursor.execute("DELETE FROM lessons")
            cursor.execute("DELETE FROM sqlite_sequence WHERE name='lessons'") # reset autoincrement
            
            pools = {
                1: "asdf",
                2: "jkl;",
                3: "asdfjkl;",
                4: "asdfjkl;gh",
                5: "asdfjkl;gh",
                6: "qwert",
                7: "uiop",
                8: "qwertyuiop",
                9: "qwertyuiopasdfjkl;gh",
                10: "zxcvb",
                11: "nm,./",
                12: "zxcvbnm,./",
                13: "abcdefghijklmnopqrstuvwxyz",
                14: "asdfgqwertzxcvbASDFGQWERTZXCVB",
                15: "jkl;yuiopnmjkl;yuiopnmJKL;YUIOPNM",
                16: "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ.",
                17: "12345",
                18: "67890",
                19: "1234567890-= [];\',./",
                20: "!@#$%^&*()_+{}|:\"<>?"
            }
            
            titles_and_levels = [
                (1, "Lesson 1: Home Row - Left Hand", "Beginner"),
                (2, "Lesson 2: Home Row - Right Hand", "Beginner"),
                (3, "Lesson 3: Home Row - Combined", "Beginner"),
                (4, "Lesson 4: Home Row - G & H Keys", "Beginner"),
                (5, "Lesson 5: Home Row - Full Words", "Beginner"),
                (6, "Lesson 6: Top Row - Left Hand", "Beginner"),
                (7, "Lesson 7: Top Row - Right Hand", "Beginner"),
                (8, "Lesson 8: Top Row - Combined", "Beginner"),
                (9, "Lesson 9: Top & Home Row Mixed", "Beginner"),
                (10, "Lesson 10: Bottom Row - Left Hand", "Beginner"),
                (11, "Lesson 11: Bottom Row - Right Hand", "Beginner"),
                (12, "Lesson 12: Bottom Row - Combined", "Beginner"),
                (13, "Lesson 13: Full Alphabet Practice", "Intermediate"),
                (14, "Lesson 14: Shift & Left Capitals", "Intermediate"),
                (15, "Lesson 15: Shift & Right Capitals", "Intermediate"),
                (16, "Lesson 16: Shift & Full Sentences", "Intermediate"),
                (17, "Lesson 17: Numbers - Left Hand", "Advanced"),
                (18, "Lesson 18: Numbers - Right Hand", "Advanced"),
                (19, "Lesson 19: Numbers & Basic Punctuation", "Advanced"),
                (20, "Lesson 20: Advanced Symbols", "Advanced")
            ]
            
            def generate_typing_drill(lesson_id, char_pool, count=1010):
                char_list = [c for c in char_pool if c != ' ']
                words = []
                
                if lesson_id == 5:
                    real_words = ["dad", "lad", "glass", "salad", "flash", "glad", "flask", "half", "gash", "fall", "shall", "ask", "gas", "dash", "lash", "fad", "fads", "lag", "lags", "flag", "flags"]
                    for _ in range(count):
                        if random.random() < 0.4:
                            words.append(random.choice(real_words))
                        else:
                            words.append("".join(random.choice(char_list) for _ in range(random.randint(2, 5))))
                elif lesson_id == 13:
                    real_words = ["the", "quick", "brown", "fox", "jumps", "over", "the", "lazy", "dog", "pack", "my", "box", "with", "five", "dozen", "liquor", "jugs", "typing", "practice", "keyboard", "master", "speed", "accuracy"]
                    for _ in range(count):
                        if random.random() < 0.5:
                            words.append(random.choice(real_words))
                        else:
                            words.append("".join(random.choice(char_list) for _ in range(random.randint(3, 6))))
                elif lesson_id == 16:
                    real_words = ["The", "Quick", "Brown", "Fox", "Jumps", "Over", "The", "Lazy", "Dog.", "Typing", "Is", "Very", "Fun", "And", "Useful.", "Hello", "World!", "How", "Are", "You?"]
                    for _ in range(count):
                        if random.random() < 0.5:
                            words.append(random.choice(real_words))
                        else:
                            w = "".join(random.choice(char_list) for _ in range(random.randint(3, 6)))
                            if random.random() < 0.3:
                                w = w.capitalize()
                            words.append(w)
                else:
                    # Repetitive drills (first 100 patterns)
                    for _ in range(100):
                        pat = random.choice([1, 2, 3])
                        if pat == 1:
                            words.append(random.choice(char_list) * random.randint(3, 5))
                        elif pat == 2 and len(char_list) >= 2:
                            c1, c2 = random.sample(char_list, 2)
                            words.append((c1+c2)*2)
                        else:
                            words.append("".join(random.choice(char_list) for _ in range(random.randint(3, 4))))
                    
                    # Random patterns (910 patterns)
                    for _ in range(count - 100):
                        words.append("".join(random.choice(char_list) for _ in range(random.randint(2, 6))))
                        
                random.shuffle(words)
                return " ".join(words[:count])
                
            lessons_data = []
            for lid, title, level in titles_and_levels:
                content = generate_typing_drill(lid, pools[lid], 1010)
                lessons_data.append((title, level, content))
                
            cursor.executemany("INSERT INTO lessons (title, level, content) VALUES (?, ?, ?)", lessons_data)
            
        conn.commit()
        conn.close()

db_manager = DBManager()

# =====================================================================
# Audio Helper
# =====================================================================
def play_sound_async(sound_type, sound_enabled):
    pass

# =====================================================================
# Custom Modern Widgets
# =====================================================================
class HoverButton(tk.Label):
    def __init__(self, master, text, command=None, theme=None, font=("Segoe UI", 10, "bold"), **kwargs):
        self.command = command
        self.theme = theme
        super().__init__(
            master,
            text=text,
            font=font,
            padx=16,
            pady=8,
            cursor="hand2",
            bd=0,
            relief="flat",
            anchor="center",
            **kwargs
        )
        self.bind("<Enter>", self.on_enter)
        self.bind("<Leave>", self.on_leave)
        self.bind("<ButtonPress-1>", self.on_press)
        self.bind("<ButtonRelease-1>", self.on_release)
        if theme:
            self.apply_theme(theme)

    def apply_theme(self, theme):
        self.theme = theme
        self.config(
            bg=theme["accent"],
            fg=theme["btn_fg"]
        )

    def on_enter(self, event):
        if self.theme:
            self.config(bg=self.theme["secondary"])

    def on_leave(self, event):
        if self.theme:
            self.config(bg=self.theme["accent"])

    def on_press(self, event):
        if self.theme:
            self.config(bg=self.theme["muted"])

    def on_release(self, event):
        if self.theme:
            self.config(bg=self.theme["secondary"])
        if self.command:
            self.command()

class CardFrame(tk.Frame):
    def __init__(self, master, theme, *args, **kwargs):
        super().__init__(master, bg=theme["card_bg"], highlightthickness=1, highlightbackground=theme["secondary"], *args, **kwargs)

class ScrollableFrame(tk.Frame):
    def __init__(self, container, theme, *args, **kwargs):
        super().__init__(container, bg=theme["bg"], *args, **kwargs)
        
        self.canvas = tk.Canvas(self, borderwidth=0, highlightthickness=0, bg=theme["bg"])
        self.scrollbar = tk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = tk.Frame(self.canvas, bg=theme["bg"])

        self.scrollable_frame.bind(
            "<Configure>",
            lambda event: self.canvas.configure(
                scrollregion=self.canvas.bbox("all")
            )
        )

        self.canvas_window = self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        
        # Bind canvas resize to match internal frame width
        self.canvas.bind('<Configure>', self._on_canvas_configure)

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")
        
        # Mousewheel binding
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)

    def _on_canvas_configure(self, event):
        self.canvas.itemconfig(self.canvas_window, width=event.width)

    def _on_mousewheel(self, event):
        try:
            self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        except Exception:
            pass

    def destroy(self):
        # Unbind mousewheel from canvas when destroyed
        self.canvas.unbind_all("<MouseWheel>")
        super().destroy()

# =====================================================================
# Main Application Framework
# =====================================================================
class TypingApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("SpeedType - Touch Typing Software")
        self.geometry("1024x720")
        self.minsize(960, 650)
        
        # User session variables
        self.current_user_id = None
        self.current_username = None
        
        # Default global config settings
        self.current_theme_name = "Cyberpunk Dark"
        self.theme = THEMES[self.current_theme_name]
        self.sound_enabled = True

        self.current_frame = None
        
        self.configure(bg=self.theme["bg"])
        self.show_login()

    def set_session(self, user_id, username):
        self.current_user_id = user_id
        self.current_username = username
        
        # Load user configurations
        settings = self.load_settings(user_id)
        self.current_theme_name = settings["theme"]
        self.theme = THEMES[self.current_theme_name]
        self.sound_enabled = settings["sound_enabled"]
        self.configure(bg=self.theme["bg"])
        
        self.show_dashboard()

    def load_settings(self, user_id):
        conn = db_manager.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT theme, sound_enabled FROM settings WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()
        conn.close()
        if row:
            return {"theme": row[0], "sound_enabled": bool(row[1])}
        return {"theme": "Cyberpunk Dark", "sound_enabled": True}

    def update_settings(self, theme_name, sound_enabled):
        self.current_theme_name = theme_name
        self.theme = THEMES[theme_name]
        self.sound_enabled = sound_enabled
        self.configure(bg=self.theme["bg"])
        
        # Save to database
        if self.current_user_id:
            conn = db_manager.get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO settings (user_id, theme, sound_enabled)
                VALUES (?, ?, ?)
            """, (self.current_user_id, theme_name, int(sound_enabled)))
            conn.commit()
            conn.close()

    def logout(self):
        self.current_user_id = None
        self.current_username = None
        self.show_login()

    def show_login(self):
        if self.current_frame:
            self.current_frame.destroy()
        self.current_frame = LoginPage(self, self.theme)
        self.current_frame.pack(fill="both", expand=True)

    def show_dashboard(self):
        self.show_main_layout(DashboardPage)

    def show_lessons(self):
        self.show_main_layout(LessonsPage)

    def show_custom_practice(self):
        self.show_main_layout(CustomPracticePage)

    def show_games(self):
        self.show_main_layout(GamesPage)

    def show_settings(self):
        self.show_main_layout(SettingsPage)

    def show_main_layout(self, view_class, *args, **kwargs):
        if self.current_frame:
            self.current_frame.destroy()
        
        self.current_frame = MainLayoutFrame(self, self.theme, view_class, *args, **kwargs)
        self.current_frame.pack(fill="both", expand=True)

# =====================================================================
# Sidebar Navigation View Layout
# =====================================================================
class MainLayoutFrame(tk.Frame):
    def __init__(self, master, theme, inner_view_class, *args, **kwargs):
        super().__init__(master, bg=theme["bg"])
        self.theme = theme
        self.master_app = master
        
        # Grid layout
        self.grid_columnconfigure(0, weight=0) # Sidebar
        self.grid_columnconfigure(1, weight=1) # Main View
        self.grid_rowconfigure(0, weight=1)
        
        # Sidebar Frame
        self.sidebar = tk.Frame(self, width=220, bg=theme["card_bg"], bd=0)
        self.sidebar.grid(row=0, column=0, sticky="ns", padx=(0, 2))
        self.sidebar.grid_propagate(False)
        
        # User details card in sidebar
        self.user_card = tk.Frame(self.sidebar, bg=theme["bg"], padx=10, pady=15)
        self.user_card.pack(fill="x", padx=10, pady=(15, 20))
        
        self.avatar_lbl = tk.Label(self.user_card, text="👤", font=("Segoe UI", 28), bg=theme["bg"], fg=theme["accent"])
        self.avatar_lbl.pack()
        
        self.username_lbl = tk.Label(self.user_card, text=self.master_app.current_username, font=("Segoe UI", 12, "bold"), bg=theme["bg"], fg=theme["text"])
        self.username_lbl.pack(pady=(5, 2))
        
        # Sidebar Navigation Buttons
        self.add_nav_btn("Dashboard Overview", self.master_app.show_dashboard)
        self.add_nav_btn("Structured Lessons", self.master_app.show_lessons)
        self.add_nav_btn("Custom Practice", self.master_app.show_custom_practice)
        self.add_nav_btn("Typing Games", self.master_app.show_games)
        self.add_nav_btn("Settings", self.master_app.show_settings)
        
        # Spacer
        self.spacer = tk.Frame(self.sidebar, bg=theme["card_bg"])
        self.spacer.pack(fill="both", expand=True)
        
        # Logout Button
        self.logout_btn = HoverButton(self.sidebar, text="Sign Out ➔", command=self.master_app.logout, theme=theme)
        self.logout_btn.pack(fill="x", padx=15, pady=15)
        
        # Content frame container
        self.content_area = tk.Frame(self, bg=theme["bg"], padx=20, pady=20)
        self.content_area.grid(row=0, column=1, sticky="nsew")
        
        # Load inner page frame
        self.inner_frame = inner_view_class(self.content_area, self.master_app, theme, *args, **kwargs)
        self.inner_frame.pack(fill="both", expand=True)

    def add_nav_btn(self, text, command):
        btn = HoverButton(self.sidebar, text=text, command=command, theme=self.theme, font=("Segoe UI", 10))
        btn.pack(fill="x", padx=15, pady=5)

# =====================================================================
# LOGIN PAGE VIEW
# =====================================================================
class LoginPage(tk.Frame):
    def __init__(self, master, theme):
        super().__init__(master, bg=theme["bg"])
        self.theme = theme
        self.master_app = master
        
        # Card Layout Container
        self.container = CardFrame(self, theme)
        self.container.place(relx=0.5, rely=0.5, anchor="center", width=420, height=440)
        
        # Header / Title
        self.title_lbl = tk.Label(self.container, text="⚡ SpeedType", font=("Segoe UI", 26, "bold"), bg=theme["card_bg"], fg=theme["accent"])
        self.title_lbl.pack(pady=(35, 10))
        
        self.subtitle_lbl = tk.Label(self.container, text="Master the Keyboard Interactive Platform", font=("Segoe UI", 10), bg=theme["card_bg"], fg=theme["muted"])
        self.subtitle_lbl.pack(pady=(0, 25))
        
        # Username Entry
        self.user_lbl = tk.Label(self.container, text="Username", font=("Segoe UI", 9, "bold"), bg=theme["card_bg"], fg=theme["muted"])
        self.user_lbl.pack(anchor="w", padx=45, pady=(5, 2))
        self.username_entry = tk.Entry(self.container, font=("Segoe UI", 12), bg=theme["bg"], fg=theme["text"], insertbackground=theme["text"], bd=1, relief="solid", highlightthickness=0)
        self.username_entry.pack(fill="x", padx=45, ipady=6)
        
        # Password Entry
        self.pass_lbl = tk.Label(self.container, text="Password", font=("Segoe UI", 9, "bold"), bg=theme["card_bg"], fg=theme["muted"])
        self.pass_lbl.pack(anchor="w", padx=45, pady=(15, 2))
        self.password_entry = tk.Entry(self.container, show="*", font=("Segoe UI", 12), bg=theme["bg"], fg=theme["text"], insertbackground=theme["text"], bd=1, relief="solid", highlightthickness=0)
        self.password_entry.pack(fill="x", padx=45, ipady=6)
        
        # Error Label
        self.err_lbl = tk.Label(self.container, text="", font=("Segoe UI", 9), bg=theme["card_bg"], fg=theme["error"])
        self.err_lbl.pack(pady=(10, 0))
        
        # Button container
        self.btn_frame = tk.Frame(self.container, bg=theme["card_bg"])
        self.btn_frame.pack(fill="x", padx=45, pady=(15, 20))
        
        self.login_btn = HoverButton(self.btn_frame, text="Log In", command=self.handle_login, theme=theme)
        self.login_btn.pack(side="left", fill="x", expand=True, padx=(0, 5))
        
        self.register_btn = HoverButton(self.btn_frame, text="Register", command=self.handle_register, theme=theme)
        # Shift styling to differentiate register button slightly
        self.register_btn.config(bg=theme["secondary"], fg=theme["text"])
        self.register_btn.bind("<Enter>", lambda e: self.register_btn.config(bg=theme["accent"], fg=theme["btn_fg"]))
        self.register_btn.bind("<Leave>", lambda e: self.register_btn.config(bg=theme["secondary"], fg=theme["text"]))
        self.register_btn.pack(side="right", fill="x", expand=True, padx=(5, 0))

    def handle_login(self):
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()
        
        if not username or not password:
            self.err_lbl.config(text="Please fill in all fields.")
            return
            
        conn = db_manager.get_connection()
        cursor = conn.cursor()
        pw_hash = hashlib.sha256(password.encode()).hexdigest()
        cursor.execute("SELECT id FROM users WHERE username = ? AND password_hash = ?", (username, pw_hash))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            self.master_app.set_session(row[0], username)
        else:
            self.err_lbl.config(text="Invalid username or password.")

    def handle_register(self):
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()
        
        if not username or not password:
            self.err_lbl.config(text="Please fill in all fields.")
            return
            
        if len(password) < 4:
            self.err_lbl.config(text="Password must be at least 4 characters long.")
            return
            
        conn = db_manager.get_connection()
        cursor = conn.cursor()
        pw_hash = hashlib.sha256(password.encode()).hexdigest()
        try:
            cursor.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)", (username, pw_hash))
            user_id = cursor.lastrowid
            # Create default settings
            cursor.execute("INSERT INTO settings (user_id) VALUES (?)", (user_id,))
            conn.commit()
            conn.close()
            messagebox.showinfo("Success", "Account registered successfully! Logging in...")
            self.master_app.set_session(user_id, username)
        except sqlite3.IntegrityError:
            conn.close()
            self.err_lbl.config(text="Username already exists. Please pick another.")

# =====================================================================
# DASHBOARD OVERVIEW VIEW
# =====================================================================
class DashboardPage(tk.Frame):
    def __init__(self, master, master_app, theme):
        super().__init__(master, bg=theme["bg"])
        self.theme = theme
        self.master_app = master_app
        
        # Title
        self.header_lbl = tk.Label(self, text="Dashboard Overview", font=("Segoe UI", 20, "bold"), bg=theme["bg"], fg=theme["accent"])
        self.header_lbl.pack(anchor="w", pady=(0, 15))
        
        # Calculate stats
        conn = db_manager.get_connection()
        cursor = conn.cursor()
        user_id = self.master_app.current_user_id
        
        cursor.execute("SELECT AVG(wpm), MAX(wpm), AVG(accuracy), COUNT(*) FROM progress WHERE user_id = ?", (user_id,))
        avg_wpm, max_wpm, avg_acc, lessons_completed = cursor.fetchone()
        
        cursor.execute("SELECT COUNT(DISTINCT lesson_id) FROM progress WHERE user_id = ?", (user_id,))
        unique_lessons = cursor.fetchone()[0]
        
        # Query total available lessons
        cursor.execute("SELECT COUNT(*) FROM lessons")
        total_lessons = cursor.fetchone()[0]
        
        conn.close()
        
        avg_wpm = round(avg_wpm, 1) if avg_wpm else 0
        max_wpm = round(max_wpm, 1) if max_wpm else 0
        avg_acc = round(avg_acc, 1) if avg_acc else 0
        
        # Stats panel frame
        self.stats_panel = tk.Frame(self, bg=theme["bg"])
        self.stats_panel.pack(fill="x", pady=10)
        self.stats_panel.grid_columnconfigure((0, 1, 2, 3), weight=1, uniform="stats")
        
        self.create_stat_card(self.stats_panel, 0, "Average Speed", f"{avg_wpm} WPM", "Based on completed lessons")
        self.create_stat_card(self.stats_panel, 1, "Peak Speed", f"{max_wpm} WPM", "Your all-time highest WPM")
        self.create_stat_card(self.stats_panel, 2, "Average Accuracy", f"{avg_acc}%", "Keystroke hit ratio")
        self.create_stat_card(self.stats_panel, 3, "Curriculum Progress", f"{unique_lessons} / {total_lessons}", "Unique lessons finished")
        
        # Graph & Problem Keys Panel (2 Columns)
        self.details_panel = tk.Frame(self, bg=theme["bg"])
        self.details_panel.pack(fill="both", expand=True, pady=15)
        self.details_panel.grid_columnconfigure(0, weight=3) # Chart
        self.details_panel.grid_columnconfigure(1, weight=2) # Problem keys
        self.details_panel.grid_rowconfigure(0, weight=1)
        
        # Visual WPM progression chart container
        self.chart_card = CardFrame(self.details_panel, theme, padx=15, pady=15)
        self.chart_card.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        
        self.chart_lbl = tk.Label(self.chart_card, text="📈 WPM Performance Progression", font=("Segoe UI", 12, "bold"), bg=theme["card_bg"], fg=theme["text"])
        self.chart_lbl.pack(anchor="w", pady=(0, 10))
        
        self.chart_canvas = tk.Canvas(self.chart_card, bg=theme["card_bg"], bd=0, highlightthickness=0)
        self.chart_canvas.pack(fill="both", expand=True)
        self.chart_canvas.bind("<Configure>", lambda e: self.draw_chart())
        
        # Problem Keys container
        self.key_card = CardFrame(self.details_panel, theme, padx=15, pady=15)
        self.key_card.grid(row=0, column=1, sticky="nsew", padx=(10, 0))
        
        self.key_lbl = tk.Label(self.key_card, text="⚠️ Keys Requiring Review (Problem Keys)", font=("Segoe UI", 12, "bold"), bg=theme["card_bg"], fg=theme["text"])
        self.key_lbl.pack(anchor="w", pady=(0, 15))
        
        self.load_problem_keys()

    def create_stat_card(self, parent, col, title, val, desc):
        card = CardFrame(parent, self.theme, padx=15, pady=15)
        card.grid(row=0, column=col, sticky="nsew", padx=6)
        
        t_lbl = tk.Label(card, text=title, font=("Segoe UI", 9, "bold"), bg=self.theme["card_bg"], fg=self.theme["muted"])
        t_lbl.pack(anchor="w")
        
        v_lbl = tk.Label(card, text=val, font=("Segoe UI", 20, "bold"), bg=self.theme["card_bg"], fg=self.theme["accent"])
        v_lbl.pack(anchor="w", pady=4)
        
        d_lbl = tk.Label(card, text=desc, font=("Segoe UI", 8), bg=self.theme["card_bg"], fg=self.theme["muted"])
        d_lbl.pack(anchor="w")

    def draw_chart(self):
        canvas = self.chart_canvas
        canvas.delete("all")
        
        W = canvas.winfo_width()
        H = canvas.winfo_height()
        if W < 50 or H < 50:
            return
            
        # Query chart data (last 15 sessions)
        conn = db_manager.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT wpm FROM progress WHERE user_id = ? ORDER BY completed_at ASC", (self.master_app.current_user_id,))
        rows = cursor.fetchall()
        conn.close()
        
        data = [r[0] for r in rows]
        # Keep only last 12
        if len(data) > 12:
            data = data[-12:]
            
        pad_x = 40
        pad_y = 30
        
        # Grid helper lines
        for y_lvl in [0.25, 0.5, 0.75]:
            y_pos = pad_y + y_lvl * (H - 2 * pad_y)
            canvas.create_line(pad_x, y_pos, W - pad_x, y_pos, fill=self.theme["secondary"], dash=(2, 2))
            
        if not data:
            canvas.create_text(W/2, H/2, text="No completed lesson records found yet.\nComplete lessons to plot speeds!", fill=self.theme["muted"], font=("Segoe UI", 10), justify="center")
            return
            
        max_val = max(data)
        max_y = max(max_val * 1.15, 60) # Scale graph nicely
        
        pts = []
        n = len(data)
        for i, val in enumerate(data):
            x = pad_x + (i * (W - 2 * pad_x) / max(n - 1, 1))
            y = H - pad_y - (val / max_y) * (H - 2 * pad_y)
            pts.append((x, y, val))
            
        # Draw plot line
        for i in range(len(pts) - 1):
            x1, y1, _ = pts[i]
            x2, y2, _ = pts[i+1]
            canvas.create_line(x1, y1, x2, y2, fill=self.theme["accent"], width=3)
            
        # Draw plot dots and text
        for x, y, val in pts:
            canvas.create_oval(x-5, y-5, x+5, y+5, fill=self.theme["correct"], outline=self.theme["accent"], width=1)
            # Speed annotation
            canvas.create_text(x, y - 14, text=f"{int(val)}", fill=self.theme["text"], font=("Segoe UI", 8, "bold"))
            
        # X & Y bottom baseline
        canvas.create_line(pad_x, H - pad_y, W - pad_x, H - pad_y, fill=self.theme["muted"], width=1)
        canvas.create_text(pad_x, H - pad_y + 14, text="Oldest Session", fill=self.theme["muted"], font=("Segoe UI", 8), anchor="w")
        canvas.create_text(W - pad_x, H - pad_y + 14, text="Latest Session", fill=self.theme["muted"], font=("Segoe UI", 8), anchor="e")

    def load_problem_keys(self):
        conn = db_manager.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT key_char, error_count FROM key_errors WHERE user_id = ? ORDER BY error_count DESC LIMIT 5", (self.master_app.current_user_id,))
        rows = cursor.fetchall()
        conn.close()
        
        if not rows:
            no_lbl = tk.Label(self.key_card, text="No keyboard errors registered yet!\nKeep up the high accuracy to stay error-free.", font=("Segoe UI", 10), bg=self.theme["card_bg"], fg=self.theme["muted"], justify="center")
            no_lbl.pack(pady=40)
            return
            
        for char, count in rows:
            row_frame = tk.Frame(self.key_card, bg=self.theme["card_bg"], pady=8)
            row_frame.pack(fill="x")
            
            # Key indicator
            key_tag = tk.Label(row_frame, text=f" Key '{char.upper()}' ", font=("Courier New", 11, "bold"), bg=self.theme["bg"], fg=self.theme["error"], highlightthickness=1, highlightbackground=self.theme["error"])
            key_tag.pack(side="left", padx=(5, 10))
            
            # Message description
            msg = f"Missed {count} times"
            desc_lbl = tk.Label(row_frame, text=msg, font=("Segoe UI", 10), bg=self.theme["card_bg"], fg=self.theme["text"])
            desc_lbl.pack(side="left")
            
            # Bar visualization
            bar_lbl = tk.Label(row_frame, text="█" * min(count, 15), font=("Segoe UI", 8), bg=self.theme["card_bg"], fg=self.theme["error"])
            bar_lbl.pack(side="right", padx=10)

# =====================================================================
# CURRICULUM LESSONS BROWSER VIEW
# =====================================================================
class LessonsPage(tk.Frame):
    def __init__(self, master, master_app, theme):
        super().__init__(master, bg=theme["bg"])
        self.theme = theme
        self.master_app = master_app
        
        # Header Info
        self.header_lbl = tk.Label(self, text="Structured Typing Curriculum", font=("Segoe UI", 20, "bold"), bg=theme["bg"], fg=theme["accent"])
        self.header_lbl.pack(anchor="w", pady=(0, 2))
        
        self.sub_lbl = tk.Label(self, text="Advance step-by-step to progress from beginner home-row keys to special characters.", font=("Segoe UI", 10), bg=theme["bg"], fg=theme["muted"])
        self.sub_lbl.pack(anchor="w", pady=(0, 15))
        
        # Scrollable View Window
        self.scroll_view = ScrollableFrame(self, theme)
        self.scroll_view.pack(fill="both", expand=True)
        
        self.render_lessons()

    def render_lessons(self):
        # Clear existing
        for child in self.scroll_view.scrollable_frame.winfo_children():
            child.destroy()
            
        # Connect & fetch lessons
        conn = db_manager.get_connection()
        cursor = conn.cursor()
        
        # Get lessons and match max user scores
        cursor.execute("""
            SELECT l.id, l.title, l.level, MAX(p.wpm), MAX(p.accuracy)
            FROM lessons l
            LEFT JOIN progress p ON l.id = p.lesson_id AND p.user_id = ?
            GROUP BY l.id
        """, (self.master_app.current_user_id,))
        lessons = cursor.fetchall()
        conn.close()
        
        # Render lessons in 3 Columns
        row_idx = 0
        col_idx = 0
        
        # Allow grids to stretch evenly
        self.scroll_view.scrollable_frame.grid_columnconfigure((0, 1, 2), weight=1, uniform="lessons")
        
        for idx, title, level, max_wpm, max_acc in lessons:
            card = CardFrame(self.scroll_view.scrollable_frame, self.theme, padx=15, pady=15)
            card.grid(row=row_idx, column=col_idx, padx=8, pady=8, sticky="nsew")
            
            # Level Badge
            badge_color = self.theme["accent"]
            if level == "Intermediate":
                badge_color = self.theme["secondary"]
            elif level == "Advanced":
                badge_color = self.theme["error"]
                
            lvl_badge = tk.Label(card, text=level.upper(), font=("Segoe UI", 8, "bold"), bg=badge_color, fg=self.theme["btn_fg"], padx=6, pady=2)
            lvl_badge.pack(anchor="w")
            
            title_lbl = tk.Label(card, text=title, font=("Segoe UI", 11, "bold"), bg=self.theme["card_bg"], fg=self.theme["text"], justify="left")
            title_lbl.pack(anchor="w", pady=(8, 12))
            
            # Performance Records
            rec_frame = tk.Frame(card, bg=self.theme["card_bg"])
            rec_frame.pack(fill="x", pady=(0, 15))
            
            if max_wpm is not None:
                record_text = f"🏆 Best: {round(max_wpm, 1)} WPM  |  🎯 Acc: {round(max_acc, 1)}%"
                rec_lbl = tk.Label(rec_frame, text=record_text, font=("Segoe UI", 9), bg=self.theme["card_bg"], fg=self.theme["correct"])
            else:
                rec_lbl = tk.Label(rec_frame, text="🔒 Not attempted yet", font=("Segoe UI", 9, "italic"), bg=self.theme["card_bg"], fg=self.theme["muted"])
            rec_lbl.pack(anchor="w")
            
            # Start Practice Trigger
            start_btn = HoverButton(card, text="Start Lesson ➔", command=lambda lid=idx: self.start_lesson(lid), theme=self.theme)
            start_btn.pack(fill="x")
            
            col_idx += 1
            if col_idx > 2:
                col_idx = 0
                row_idx += 1

    def start_lesson(self, lesson_id):
        self.master_app.show_main_layout(PracticePage, lesson_id=lesson_id)

# =====================================================================
# TYPING INTERACTIVE TRAINER (PRACTICE SCREEN)
# =====================================================================
class PracticePage(tk.Frame):
    def __init__(self, master, master_app, theme, lesson_id=None, custom_text=None):
        super().__init__(master, bg=theme["bg"])
        self.theme = theme
        self.master_app = master_app
        self.lesson_id = lesson_id
        
        # Load Content Text and setup word generators
        if lesson_id:
            conn = db_manager.get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT title, content FROM lessons WHERE id = ?", (lesson_id,))
            self.title_str, db_content = cursor.fetchone()
            conn.close()
            # Clean character pool from spaces/newlines to get unique chars
            self.char_pool = "".join(sorted(list(set(db_content.replace("\n", "").replace("\r", "")))))
        else:
            self.title_str = "Custom Practice Mode"
            db_content = custom_text if custom_text else "the quick brown fox jumps over the lazy dog."
            self.custom_words = db_content.split()
            if not self.custom_words:
                self.custom_words = ["practice"]
            self.custom_word_idx = 0
            
        # Keystroke Metrics tracking
        self.current_idx = 0
        self.total_keystrokes = 0
        self.correct_keystrokes = 0
        self.error_count = 0
        self.start_time = None
        self.time_left = 600  # 10 minutes total timer (600s)
        self.is_paused = False
        self.errors_logged = {} # Local key index errors tracker
        
        # Generate initial 2 lines
        self.line1 = self.generate_new_line() + " "
        self.line2 = self.generate_new_line() + " "
        self.target_text = self.line1 + "\n" + self.line2
        
        # UI Top Header panel
        self.setup_header()
        
        # Main typing text area
        self.text_frame = CardFrame(self, theme, padx=15, pady=15)
        self.text_frame.pack(fill="both", expand=True, pady=(10, 15))
        
        self.text_widget = tk.Text(
            self.text_frame,
            font=("Courier New", 20, "bold"),
            bg=theme["card_bg"],
            fg=theme["muted"],
            bd=0,
            highlightthickness=0,
            wrap="none",
            height=2,
            spacing2=18,
            padx=10,
            pady=10
        )
        self.text_widget.pack(fill="both", expand=True)
        
        # Configure typography color tags
        self.text_widget.tag_config("correct", foreground=theme["correct"])
        self.text_widget.tag_config("incorrect", foreground=theme["error"], underline=True)
        self.text_widget.tag_config("current", foreground=theme["btn_fg"], background=theme["accent"])
        self.text_widget.tag_config("remaining", foreground=theme["muted"])
        
        # Insert target text & apply tags
        self.text_widget.insert("1.0", self.target_text)
        self.text_widget.config(state="disabled") # Disable typing directly
        
        # Keyboard visual layout canvas
        self.kbd_canvas = tk.Canvas(self, bg=theme["bg"], bd=0, highlightthickness=0, height=220)
        self.kbd_canvas.pack(fill="x", side="bottom")
        
        # Intercept window keys
        self.master_app.bind("<Key>", self.on_keypress)
        self.kbd_canvas.bind("<Configure>", lambda e: self.draw_keyboard())
        
        self.pressed_key_state = None
        self.update_metrics_view()
        self.highlight_current_char()
        self.draw_keyboard()
        
    def setup_header(self):
        self.header_panel = tk.Frame(self, bg=self.theme["bg"])
        self.header_panel.pack(fill="x")
        
        # Back navigation
        self.back_btn = HoverButton(self.header_panel, text="◀ Exit", command=self.exit_practice, theme=self.theme, font=("Segoe UI", 9, "bold"))
        self.back_btn.pack(side="left", padx=(0, 15))
        
        # Pause/Resume Button
        self.pause_btn = HoverButton(self.header_panel, text="⏸ Pause", command=self.toggle_pause, theme=self.theme, font=("Segoe UI", 9, "bold"))
        self.pause_btn.pack(side="left", padx=5)
        
        # Details title
        self.title_lbl = tk.Label(self.header_panel, text=self.title_str, font=("Segoe UI", 14, "bold"), bg=self.theme["bg"], fg=self.theme["text"])
        self.title_lbl.pack(side="left", padx=15)
        
        # Live display metrics stats dashboard indicators
        self.metrics_frame = tk.Frame(self.header_panel, bg=self.theme["bg"])
        self.metrics_frame.pack(side="right")
        
        self.wpm_lbl = self.add_metric_indicator("WPM: 0")
        self.acc_lbl = self.add_metric_indicator("ACC: 100%")
        self.err_lbl = self.add_metric_indicator("Errors: 0")
        self.prog_lbl = self.add_metric_indicator("Progress: 0%")
        self.time_lbl = self.add_metric_indicator("Time: 10:00")
        
    def add_metric_indicator(self, text):
        lbl = tk.Label(self.metrics_frame, text=text, font=("Segoe UI", 10, "bold"), bg=self.theme["card_bg"], fg=self.theme["accent"], padx=10, pady=5, highlightthickness=1, highlightbackground=self.theme["secondary"])
        lbl.pack(side="left", padx=4)
        return lbl

    def get_next_word(self):
        if self.lesson_id:
            char_list = [c for c in self.char_pool if c != ' ']
            if not char_list:
                char_list = ['a']
                
            real_words = []
            if self.lesson_id == 5:
                real_words = ["dad", "lad", "glass", "salad", "flash", "glad", "flask", "half", "gash", "fall", "shall", "ask", "gas", "dash", "lash", "fad", "fads", "lag", "lags", "flag", "flags"]
            elif self.lesson_id == 13:
                real_words = ["the", "quick", "brown", "fox", "jumps", "over", "the", "lazy", "dog", "pack", "my", "box", "with", "five", "dozen", "liquor", "jugs", "typing", "practice", "keyboard", "master", "speed", "accuracy"]
            elif self.lesson_id == 16:
                real_words = ["The", "Quick", "Brown", "Fox", "Jumps", "Over", "The", "Lazy", "Dog.", "Typing", "Is", "Very", "Fun", "And", "Useful.", "Hello", "World!", "How", "Are", "You?"]

            if real_words and random.random() < 0.4:
                w = random.choice(real_words)
                if self.lesson_id == 16 and random.random() < 0.3:
                    w = w.capitalize()
                return w
            else:
                if random.random() < 0.15:
                    pat_type = random.choice([1, 2])
                    if pat_type == 1:
                        w = random.choice(char_list) * random.randint(3, 5)
                    else:
                        c1 = random.choice(char_list)
                        c2 = random.choice(char_list)
                        w = (c1 + c2) * 2
                else:
                    w_len = random.randint(2, 6)
                    w = "".join(random.choice(char_list) for _ in range(w_len))
                    
                if any(c.isupper() for c in char_list) and random.random() < 0.25:
                    w = w.capitalize()
                return w
        else:
            w = self.custom_words[self.custom_word_idx]
            self.custom_word_idx = (self.custom_word_idx + 1) % len(self.custom_words)
            return w

    def generate_new_line(self):
        words = []
        current_len = 0
        while current_len < 55:
            w = self.get_next_word()
            words.append(w)
            current_len += len(w) + 1
        return " ".join(words)

    def toggle_pause(self):
        if self.start_time is None:
            return
            
        self.is_paused = not self.is_paused
        
        if self.is_paused:
            self.pause_btn.config(text="▶ Resume")
            self.pause_overlay = tk.Label(
                self.text_frame,
                text="PAUSED\n\nClick 'Resume' to continue typing.",
                font=("Segoe UI", 16, "bold"),
                bg=self.theme["card_bg"],
                fg=self.theme["accent"]
            )
            self.pause_overlay.place(relx=0, rely=0, relwidth=1, relheight=1)
        else:
            self.pause_btn.config(text="⏸ Pause")
            if hasattr(self, "pause_overlay"):
                self.pause_overlay.place_forget()

    def highlight_current_char(self):
        # Reset colors
        self.text_widget.tag_remove("correct", "1.0", "end")
        self.text_widget.tag_remove("incorrect", "1.0", "end")
        self.text_widget.tag_remove("current", "1.0", "end")
        self.text_widget.tag_remove("remaining", "1.0", "end")
        
        # Character segments
        self.text_widget.tag_add("correct", "1.0", f"1.0 + {self.current_idx} chars")
        
        if self.current_idx < len(self.line1):
            self.text_widget.tag_add("current", f"1.0 + {self.current_idx} chars", f"1.0 + {self.current_idx + 1} chars")
            self.text_widget.tag_add("remaining", f"1.0 + {self.current_idx + 1} chars", "end")

    def on_keypress(self, event):
        if self.is_paused:
            return
            
        # Ignore keyboard control commands
        if not event.char and event.keysym not in ("space", "Return"):
            return
        # Ignore copy/paste Ctrl shortcuts
        if event.state & 0x4: # Control mask
            return
            
        target_char = self.line1[self.current_idx]
        pressed_char = event.char
        
        # Standardize return keys
        if event.keysym == "Return":
            pressed_char = "\n"
        elif event.keysym == "space":
            pressed_char = " "
            
        if not pressed_char:
            return
            
        if self.start_time is None:
            self.start_time = time.time()
            self.tick_timer()
            
        self.total_keystrokes += 1
        
        # Matching keystroke verification logic
        if pressed_char == target_char:
            self.correct_keystrokes += 1
            self.pressed_key_state = {
                "key": self.get_key_name_from_event(event),
                "correct": True
            }
            play_sound_async("click", self.master_app.sound_enabled)
            
            self.current_idx += 1
            if self.current_idx >= len(self.line1):
                # Slide text lines infinitely
                self.line1 = self.line2
                self.line2 = self.generate_new_line() + " "
                self.current_idx = 0
                self.target_text = self.line1 + "\n" + self.line2
                
                self.text_widget.config(state="normal")
                self.text_widget.delete("1.0", "end")
                self.text_widget.insert("1.0", self.target_text)
                self.text_widget.config(state="disabled")
        else:
            # Mistake logic
            self.error_count += 1
            self.pressed_key_state = {
                "key": self.get_key_name_from_event(event),
                "correct": False
            }
            play_sound_async("error", self.master_app.sound_enabled)
            
            # Log problem keys
            self.errors_logged[target_char] = self.errors_logged.get(target_char, 0) + 1
            
        self.update_metrics_view()
        self.highlight_current_char()
        self.draw_keyboard()
        
        # Redraw normal keyboard state after split second delay
        self.after(140, self.clear_pressed_key)

    def clear_pressed_key(self):
        self.pressed_key_state = None
        self.draw_keyboard()

    def tick_timer(self):
        if self.start_time is None or self.time_left <= 0:
            return
        if self.is_paused:
            self.after(1000, self.tick_timer)
            return
            
        self.time_left -= 1
        mins = int(self.time_left // 60)
        secs = int(self.time_left % 60)
        self.time_lbl.config(text=f"Time: {mins:02d}:{secs:02d}")
        
        self.update_metrics_view()
        
        if self.time_left <= 0:
            self.complete_practice()
        else:
            self.after(1000, self.tick_timer)

    def update_metrics_view(self):
        # Accurate Speed calculation
        elapsed_sec = 600 - self.time_left
        elapsed_min = elapsed_sec / 60.0
        
        if elapsed_min > 0.01:
            # WPM = (typed correct chars / 5) / elapsed minutes
            wpm = (self.correct_keystrokes / 5.0) / elapsed_min
        else:
            wpm = 0.0
            
        accuracy = (self.correct_keystrokes / self.total_keystrokes * 100) if self.total_keystrokes > 0 else 100
        progress = (elapsed_sec / 600.0) * 100
        
        self.wpm_lbl.config(text=f"WPM: {round(wpm, 1)}")
        self.acc_lbl.config(text=f"ACC: {round(accuracy, 1)}%")
        self.err_lbl.config(text=f"Errors: {self.error_count}")
        self.prog_lbl.config(text=f"Progress: {int(progress)}%")


    def get_key_name_from_event(self, event):
        keysym = event.keysym
        char = event.char
        
        if keysym == "space" or char == " ":
            return "space"
        elif keysym == "Return" or char in ("\r", "\n"):
            return "Enter"
        elif keysym in ("BackSpace", "Backspace"):
            return "Backspace"
        elif keysym == "Tab":
            return "Tab"
        elif keysym in ("Caps_Lock", "Caps"):
            return "Caps"
        elif keysym == "Shift_L":
            return "Shift_L"
        elif keysym == "Shift_R":
            return "Shift_R"
            
        char_to_key = {
            '!': '1', '@': '2', '#': '3', '$': '4', '%': '5', '^': '6', '&': '7', '*': '8', '(': '9', ')': '0',
            '_': '-', '+': '=', '{': '[', '}': ']', '|': '\\', ':': ';', '"': "'", '<': ',', '>': '.', '?': '/',
            '~': '`'
        }
        if char in char_to_key:
            return char_to_key[char]
            
        if char and char.isalnum():
            return char.lower()
            
        return keysym.lower()

    def get_target_keys(self, char):
        if not char:
            return []
        if char == " ":
            return ["space"]
        if char in ("\n", "\r"):
            return ["Enter"]
        if char == "\t":
            return ["Tab"]
            
        shift_symbols = {
            '!': '1', '@': '2', '#': '3', '$': '4', '%': '5', '^': '6', '&': '7', '*': '8', '(': '9', ')': '0',
            '_': '-', '+': '=', '{': '[', '}': ']', '|': '\\', ':': ';', '"': "'", '<': ',', '>': '.', '?': '/',
            '~': '`'
        }
        left_hand_chars = "qwertasedfgzxcvb12345!@#$%"
        
        if char.isupper():
            base = char.lower()
            if base in left_hand_chars:
                return ["Shift_R", base]
            return ["Shift_L", base]
            
        if char in shift_symbols:
            base = shift_symbols[char]
            if base in left_hand_chars:
                return ["Shift_R", base]
            return ["Shift_L", base]
            
        return [char.lower()]

    def draw_keyboard(self):
        canvas = self.kbd_canvas
        canvas.delete("all")
        
        W = canvas.winfo_width()
        H = canvas.winfo_height()
        if W < 100 or H < 50:
            return
            
        # Draw base keyboard bg card frame
        canvas.create_rectangle(5, 5, W-5, H-5, fill=self.theme["card_bg"], outline=self.theme["secondary"], width=1)
        
        row_h = (H - 20) / 5
        pad = 2
        
        target_char = self.target_text[self.current_idx] if self.current_idx < len(self.target_text) else ""
        target_keys = self.get_target_keys(target_char)
        
        for row_idx, row in enumerate(KEYBOARD_LAYOUT):
            x_unit = 0.0
            for name, w_unit in row:
                x1 = 10 + x_unit * (W - 20) / 15.0
                x2 = 10 + (x_unit + w_unit) * (W - 20) / 15.0
                y1 = 10 + row_idx * row_h
                y2 = 10 + (row_idx + 1) * row_h
                
                # Check styling rules
                bg_color = self.theme["bg"]
                fg_color = self.theme["text"]
                
                # Highlight active target keys
                if name in target_keys:
                    bg_color = self.theme["kbd_highlight"]
                    fg_color = self.theme["btn_fg"]
                
                # Highlight keys currently pressed
                if self.pressed_key_state and name == self.pressed_key_state["key"]:
                    bg_color = self.theme["correct"] if self.pressed_key_state["correct"] else self.theme["error"]
                    fg_color = self.theme["btn_fg"]
                    
                canvas.create_rectangle(x1 + pad, y1 + pad, x2 - pad, y2 - pad, fill=bg_color, outline=self.theme["secondary"], width=1)
                
                # Label keys
                label_txt = name.upper() if len(name) == 1 else name
                canvas.create_text((x1+x2)/2, (y1+y2)/2, text=label_txt, fill=fg_color, font=("Segoe UI", 9, "bold"))
                
                x_unit += w_unit

    def complete_practice(self):
        # Stop keyboard binding
        self.master_app.unbind("<Key>")
        
        elapsed_sec = 600 - self.time_left
        if elapsed_sec < 1:
            elapsed_sec = 1
        elapsed_min = elapsed_sec / 60.0
        
        # Calculate scores
        wpm = (self.correct_keystrokes / 5.0) / elapsed_min
        accuracy = (self.correct_keystrokes / self.total_keystrokes * 100) if self.total_keystrokes > 0 else 100
        
        wpm = round(wpm, 1)
        accuracy = round(accuracy, 1)
        
        # Persistence values
        user_id = self.master_app.current_user_id
        
        conn = db_manager.get_connection()
        cursor = conn.cursor()
        
        # Log lesson metrics if structured
        if self.lesson_id:
            cursor.execute("INSERT INTO progress (user_id, lesson_id, wpm, accuracy) VALUES (?, ?, ?, ?)", (user_id, self.lesson_id, wpm, accuracy))
            
        # Log typing mistakes problem keys count
        for char, count in self.errors_logged.items():
            if char.isspace() or len(char) != 1:
                continue
            cursor.execute("""
                INSERT INTO key_errors (user_id, key_char, error_count)
                VALUES (?, ?, ?)
                ON CONFLICT(user_id, key_char) DO UPDATE SET error_count = error_count + ?
            """, (user_id, char.lower(), count, count))
            
        conn.commit()
        conn.close()
        
        # Display completion popups modal card summary
        sum_str = f"Practice complete!\n\nSpeed: {wpm} WPM\nAccuracy: {accuracy}%\nErrors made: {self.error_count}"
        messagebox.showinfo("Practice Completed Successfully!", sum_str)
        self.exit_practice()

    def exit_practice(self):
        self.master_app.unbind("<Key>")
        if self.lesson_id:
            self.master_app.show_lessons()
        else:
            self.master_app.show_custom_practice()

# =====================================================================
# CUSTOM PRACTICE PORTAL VIEW
# =====================================================================
class CustomPracticePage(tk.Frame):
    def __init__(self, master, master_app, theme):
        super().__init__(master, bg=theme["bg"])
        self.theme = theme
        self.master_app = master_app
        
        # Headings
        self.header_lbl = tk.Label(self, text="Custom Typing Practice", font=("Segoe UI", 20, "bold"), bg=theme["bg"], fg=theme["accent"])
        self.header_lbl.pack(anchor="w", pady=(0, 2))
        
        self.sub_lbl = tk.Label(self, text="Upload text documents (.txt) or paste target paragraph text blocks below to load.", font=("Segoe UI", 10), bg=theme["bg"], fg=theme["muted"])
        self.sub_lbl.pack(anchor="w", pady=(0, 15))
        
        # Input Frame Card
        self.input_card = CardFrame(self, theme, padx=15, pady=15)
        self.input_card.pack(fill="both", expand=True, pady=10)
        
        self.text_box = tk.Text(
            self.input_card,
            font=("Consolas", 12),
            bg=theme["bg"],
            fg=theme["text"],
            bd=1,
            relief="solid",
            insertbackground=theme["text"],
            height=12
        )
        self.text_box.pack(fill="both", expand=True, pady=(0, 15))
        
        # Controls Frame bar
        self.ctrl_frame = tk.Frame(self.input_card, bg=theme["card_bg"])
        self.ctrl_frame.pack(fill="x")
        
        self.load_btn = HoverButton(self.ctrl_frame, text="📁 Import Text File...", command=self.import_file, theme=theme)
        self.load_btn.pack(side="left", padx=(0, 5))
        
        self.clear_btn = HoverButton(self.ctrl_frame, text="Clear text", command=self.clear_text, theme=theme)
        self.clear_btn.config(bg=theme["secondary"], fg=theme["text"])
        self.clear_btn.bind("<Enter>", lambda e: self.clear_btn.config(bg=theme["accent"], fg=theme["btn_fg"]))
        self.clear_btn.bind("<Leave>", lambda e: self.clear_btn.config(bg=theme["secondary"], fg=theme["text"]))
        self.clear_btn.pack(side="left", padx=5)
        
        self.start_btn = HoverButton(self.ctrl_frame, text="Start Practice Session ➔", command=self.start_custom_practice, theme=theme)
        self.start_btn.pack(side="right")

    def import_file(self):
        fpath = filedialog.askopenfilename(filetypes=[("Text files", "*.txt")])
        if fpath:
            try:
                with open(fpath, "r", encoding="utf-8") as f:
                    content = f.read()
                self.text_box.delete("1.0", "end")
                self.text_box.insert("1.0", content)
            except Exception as e:
                messagebox.showerror("Error", f"Could not load selected file: {e}")

    def clear_text(self):
        self.text_box.delete("1.0", "end")

    def start_custom_practice(self):
        text = self.text_box.get("1.0", "end-1c").strip()
        if not text:
            messagebox.showwarning("Warning", "Please input or load text content before practicing.")
            return
        if len(text) < 5:
            messagebox.showwarning("Warning", "Typing target is too short. Please add more words.")
            return
            
        self.master_app.show_main_layout(PracticePage, custom_text=text)

# =====================================================================
# TYPING GAMES HUB VIEW
# =====================================================================
class GamesPage(tk.Frame):
    def __init__(self, master, master_app, theme):
        super().__init__(master, bg=theme["bg"])
        self.theme = theme
        self.master_app = master_app
        
        # Headings
        self.header_lbl = tk.Label(self, text="Typing Games", font=("Segoe UI", 20, "bold"), bg=theme["bg"], fg=theme["accent"])
        self.header_lbl.pack(anchor="w", pady=(0, 2))
        
        self.sub_lbl = tk.Label(self, text="Sharpen mechanical typing reflex speeds with interactive gaming modules.", font=("Segoe UI", 10), bg=theme["bg"], fg=theme["muted"])
        self.sub_lbl.pack(anchor="w", pady=(0, 20))
        
        self.game_panel = tk.Frame(self, bg=theme["bg"])
        self.game_panel.pack(fill="both", expand=True)
        self.game_panel.grid_columnconfigure((0, 1), weight=1, uniform="games")
        self.game_panel.grid_rowconfigure(0, weight=1)
        
        # Query user personal records
        conn = db_manager.get_connection()
        cursor = conn.cursor()
        user_id = self.master_app.current_user_id
        
        cursor.execute("SELECT MAX(score) FROM game_scores WHERE user_id = ? AND game_name = ?", (user_id, "Word Rain"))
        rain_hi = cursor.fetchone()[0] or 0
        
        cursor.execute("SELECT MAX(score) FROM game_scores WHERE user_id = ? AND game_name = ?", (user_id, "Target Invaders"))
        inv_hi = cursor.fetchone()[0] or 0
        
        conn.close()
        
        # Game 1 Card
        self.create_game_card(
            parent=self.game_panel,
            col=0,
            title="🎮 Word Rain (Falling Words)",
            desc="Words drop from the top. Type each word completely and hit Enter to clear them out before they crash at the bottom limit!",
            hi_score=f"Personal Best: {rain_hi} Points",
            action=self.start_word_rain
        )
        
        # Game 2 Card
        self.create_game_card(
            parent=self.game_panel,
            col=1,
            title="🛸 Target Invaders (Single Keys)",
            desc="Single keys are invading! Directly press the matching character key on your physical keyboard to zap targets down.",
            hi_score=f"Personal Best: {inv_hi} Points",
            action=self.start_invaders
        )

    def create_game_card(self, parent, col, title, desc, hi_score, action):
        card = CardFrame(parent, self.theme, padx=25, pady=25)
        card.grid(row=0, column=col, padx=12, pady=10, sticky="nsew")
        
        t_lbl = tk.Label(card, text=title, font=("Segoe UI", 14, "bold"), bg=self.theme["card_bg"], fg=self.theme["accent"])
        t_lbl.pack(anchor="w")
        
        d_lbl = tk.Label(card, text=desc, font=("Segoe UI", 10), bg=self.theme["card_bg"], fg=self.theme["text"], justify="left", wrap=300)
        d_lbl.pack(anchor="w", pady=(12, 20))
        
        s_lbl = tk.Label(card, text=hi_score, font=("Segoe UI", 9, "bold"), bg=self.theme["card_bg"], fg=self.theme["correct"])
        s_lbl.pack(anchor="w", pady=(0, 20))
        
        # Center filler frame
        fill = tk.Frame(card, bg=self.theme["card_bg"])
        fill.pack(fill="both", expand=True)
        
        play_btn = HoverButton(card, text="Launch Game Mode ➔", command=action, theme=self.theme)
        play_btn.pack(fill="x")

    def start_word_rain(self):
        self.master_app.show_main_layout(WordRainGamePage)

    def start_invaders(self):
        self.master_app.show_main_layout(TargetInvadersGamePage)

# =====================================================================
# GAME 1: WORD RAIN (FALLING WORDS ENGINE)
# =====================================================================
class WordRainGamePage(tk.Frame):
    def __init__(self, master, master_app, theme):
        super().__init__(master, bg=theme["bg"])
        self.theme = theme
        self.master_app = master_app
        
        # Word corpus bank
        self.words_list = [
            "apple", "board", "space", "click", "laser", "input", "sound", "theme",
            "curry", "setup", "green", "wrong", "level", "speed", "grade", "learn",
            "typing", "master", "sqlite", "python", "window", "canvas", "thread",
            "timing", "button", "accent", "matrix", "source", "module", "system",
            "gaming", "invader", "correct", "session", "average", "accrue", "active",
            "profile", "records", "dynamic", "feedback", "visual", "pointer", "curricle",
            "algorithm", "binary", "compiler", "database", "encryption", "function",
            "graphics", "hardware", "internet", "javascript", "keyboard", "library",
            "network", "object", "protocol", "query", "runtime", "software", "terminal",
            "utility", "variable", "website", "desktop", "application", "developer",
            "program", "syntax", "cursor", "monitor", "layout", "responsive", "custom",
            "interactive", "statistics", "accuracy", "practice", "lesson", "achievement",
            "score", "level", "lives", "invaders", "rain", "falling", "typingmaster",
            "cyberpunk", "forest", "classic", "minimalist", "soundtrack", "mechanical",
            "keystroke", "character", "symbol", "number", "capital", "shift", "timer"
        ]
        
        # State tracking
        self.score = 0
        self.lives = 3
        self.level = 1
        self.active_words = [] # Dictionaries representing active Canvas text objects
        self.spawn_timer_val = 2000
        self.base_speed = 1.0
        self.is_active = True
        
        # Layout components
        self.setup_header()
        
        # Game canvas board
        self.game_frame = CardFrame(self, theme)
        self.game_frame.pack(fill="both", expand=True, pady=10)
        
        self.canvas = tk.Canvas(self.game_frame, bg=theme["card_bg"], bd=0, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        
        # Text input tray bar
        self.tray = tk.Frame(self, bg=theme["bg"])
        self.tray.pack(fill="x", pady=(5, 10))
        
        self.entry = tk.Entry(self.tray, font=("Segoe UI", 14), bg=theme["card_bg"], fg=theme["text"], insertbackground=theme["text"], justify="center", bd=1, relief="solid")
        self.entry.pack(side="left", fill="x", expand=True, ipady=5, padx=(0, 10))
        self.entry.bind("<Return>", self.on_word_submit)
        self.entry.focus_set()
        
        self.submit_btn = HoverButton(self.tray, text="Fire 🚀", command=self.on_word_submit, theme=theme)
        self.submit_btn.pack(side="right")
        
        # Start game engine loop
        self.after(500, self.game_loop)
        self.after(1000, self.spawn_word)

    def setup_header(self):
        self.hdr = tk.Frame(self, bg=self.theme["bg"])
        self.hdr.pack(fill="x")
        
        self.exit_btn = HoverButton(self.hdr, text="◀ Quit Game", command=self.quit_game, theme=self.theme, font=("Segoe UI", 9, "bold"))
        self.exit_btn.pack(side="left")
        
        self.title_lbl = tk.Label(self.hdr, text="🎮 Game Mode: Word Rain", font=("Segoe UI", 12, "bold"), bg=self.theme["bg"], fg=self.theme["text"])
        self.title_lbl.pack(side="left", padx=15)
        
        # Metrics status
        self.scores_frame = tk.Frame(self.hdr, bg=self.theme["bg"])
        self.scores_frame.pack(side="right")
        
        self.score_lbl = self.add_game_stat("Score: 0")
        self.level_lbl = self.add_game_stat("Level: 1")
        self.lives_lbl = self.add_game_stat("Lives: ❤️ ❤️ ❤️")

    def add_game_stat(self, txt):
        lbl = tk.Label(self.scores_frame, text=txt, font=("Segoe UI", 10, "bold"), bg=self.theme["card_bg"], fg=self.theme["accent"], padx=10, pady=5, highlightthickness=1, highlightbackground=self.theme["secondary"])
        lbl.pack(side="left", padx=3)
        return lbl

    def spawn_word(self):
        if not self.is_active or self.lives <= 0:
            return
            
        W = self.canvas.winfo_width()
        if W > 100:
            word = random.choice(self.words_list)
            # Pick random screen column boundary spacing
            x = random.randint(50, W - 100)
            
            # Draw word to canvas
            obj_id = self.canvas.create_text(
                x, 15,
                text=word,
                fill=self.theme["accent"],
                font=("Consolas", 14, "bold"),
                anchor="n"
            )
            
            speed = self.base_speed * (0.8 + random.random() * 0.5)
            self.active_words.append({
                "id": obj_id,
                "word": word,
                "x": x,
                "y": 15.0,
                "speed": speed
            })
            
        # Spawn interval timing reduces as score climbs
        spawn_delay = max(2000 - (self.score // 100) * 100, 600)
        self.after(spawn_delay, self.spawn_word)

    def game_loop(self):
        if not self.is_active or self.lives <= 0:
            return
            
        H = self.canvas.winfo_height()
        
        # Keep lists of indexes to prune
        words_reached_bottom = []
        
        for idx, w_obj in enumerate(self.active_words):
            w_obj["y"] += w_obj["speed"]
            self.canvas.coords(w_obj["id"], w_obj["x"], w_obj["y"])
            
            # Words cross base limit check
            if w_obj["y"] > H - 25:
                words_reached_bottom.append(idx)
                
        # Handle failures
        for idx in reversed(words_reached_bottom):
            w_obj = self.active_words.pop(idx)
            self.canvas.delete(w_obj["id"])
            
            self.lives -= 1
            play_sound_async("error", self.master_app.sound_enabled)
            self.update_lives_badge()
            
            if self.lives <= 0:
                self.end_game()
                return
                
        self.after(30, self.game_loop)

    def on_word_submit(self, event=None):
        if not self.is_active or self.lives <= 0:
            return
            
        typed = self.entry.get().strip()
        self.entry.delete(0, "end")
        
        found = False
        for idx, w_obj in enumerate(self.active_words):
            if w_obj["word"] == typed:
                # Destroy Canvas node
                self.canvas.delete(w_obj["id"])
                self.active_words.pop(idx)
                
                # Update stats score
                points = len(typed) * 10
                self.score += points
                self.score_lbl.config(text=f"Score: {self.score}")
                
                # Check levels increment
                old_lvl = self.level
                self.level = 1 + (self.score // 300)
                self.base_speed = 1.0 + (self.level - 1) * 0.45
                self.level_lbl.config(text=f"Level: {self.level}")
                
                if self.level > old_lvl:
                    # Laser flash reward effect
                    self.flash_canvas_border()
                    
                play_sound_async("click", self.master_app.sound_enabled)
                found = True
                break
                
        if not found:
            play_sound_async("error", self.master_app.sound_enabled)

    def flash_canvas_border(self):
        # Flashes border to notify leveling up
        self.canvas.config(highlightthickness=2, highlightbackground=self.theme["correct"])
        self.after(300, lambda: self.canvas.config(highlightthickness=0))

    def update_lives_badge(self):
        badges = "❤️ " * self.lives
        self.lives_lbl.config(text=f"Lives: {badges}")

    def end_game(self):
        self.is_active = False
        
        # Save metrics to scores
        user_id = self.master_app.current_user_id
        conn = db_manager.get_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO game_scores (user_id, game_name, score, level_reached) VALUES (?, ?, ?, ?)", (user_id, "Word Rain", self.score, self.level))
        conn.commit()
        conn.close()
        
        # Card Game Over layout overlay
        self.canvas.create_text(
            self.canvas.winfo_width() / 2,
            self.canvas.winfo_height() / 2 - 20,
            text="GAME OVER",
            font=("Segoe UI", 36, "bold"),
            fill=self.theme["error"]
        )
        
        self.canvas.create_text(
            self.canvas.winfo_width() / 2,
            self.canvas.winfo_height() / 2 + 30,
            text=f"Final score: {self.score} points  |  Level: {self.level}",
            font=("Segoe UI", 14),
            fill=self.theme["text"]
        )
        self.entry.config(state="disabled")

    def quit_game(self):
        self.is_active = False
        self.master_app.show_games()

# =====================================================================
# GAME 2: TARGET INVADERS (SINGLE KEY PRESS DETECT ENG)
# =====================================================================
class TargetInvadersGamePage(tk.Frame):
    def __init__(self, master, master_app, theme):
        super().__init__(master, bg=theme["bg"])
        self.theme = theme
        self.master_app = master_app
        
        # Corpus bank characters
        self.char_list = "abcdefghijklmnopqrstuvwxyz1234567890"
        
        # State indicators
        self.score = 0
        self.lives = 3
        self.level = 1
        self.active_targets = [] # Dictionaries representing active single falling characters
        self.is_active = True
        self.base_speed = 1.2
        
        self.setup_header()
        
        self.game_frame = CardFrame(self, theme)
        self.game_frame.pack(fill="both", expand=True, pady=10)
        
        self.canvas = tk.Canvas(self.game_frame, bg=theme["card_bg"], bd=0, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        
        # Hint label
        self.hint_lbl = tk.Label(self, text="⚡ Press the physical character key on your keyboard to instantly zap falling items down!", font=("Segoe UI", 10, "italic"), bg=theme["bg"], fg=theme["muted"])
        self.hint_lbl.pack(pady=5)
        
        # Direct keyboard capture binding
        self.master_app.bind("<Key>", self.on_keypress)
        
        self.after(500, self.game_loop)
        self.after(1000, self.spawn_target)

    def setup_header(self):
        self.hdr = tk.Frame(self, bg=self.theme["bg"])
        self.hdr.pack(fill="x")
        
        self.exit_btn = HoverButton(self.hdr, text="◀ Quit Game", command=self.quit_game, theme=self.theme, font=("Segoe UI", 9, "bold"))
        self.exit_btn.pack(side="left")
        
        self.title_lbl = tk.Label(self.hdr, text="🛸 Game Mode: Target Invaders", font=("Segoe UI", 12, "bold"), bg=self.theme["bg"], fg=self.theme["text"])
        self.title_lbl.pack(side="left", padx=15)
        
        self.scores_frame = tk.Frame(self.hdr, bg=self.theme["bg"])
        self.scores_frame.pack(side="right")
        
        self.score_lbl = self.add_game_stat("Score: 0")
        self.level_lbl = self.add_game_stat("Level: 1")
        self.lives_lbl = self.add_game_stat("Lives: ❤️ ❤️ ❤️")

    def add_game_stat(self, txt):
        lbl = tk.Label(self.scores_frame, text=txt, font=("Segoe UI", 10, "bold"), bg=self.theme["card_bg"], fg=self.theme["accent"], padx=10, pady=5, highlightthickness=1, highlightbackground=self.theme["secondary"])
        lbl.pack(side="left", padx=3)
        return lbl

    def spawn_target(self):
        if not self.is_active or self.lives <= 0:
            return
            
        W = self.canvas.winfo_width()
        if W > 100:
            char = random.choice(self.char_list)
            x = random.randint(40, W - 40)
            
            # Render visual UFO target bubble
            circle_id = self.canvas.create_oval(x-18, 5, x+18, 41, fill=self.theme["bg"], outline=self.theme["error"], width=2)
            text_id = self.canvas.create_text(x, 23, text=char.upper(), font=("Courier New", 14, "bold"), fill=self.theme["text"])
            
            speed = self.base_speed * (0.85 + random.random() * 0.4)
            self.active_targets.append({
                "char": char,
                "x": x,
                "y": 23.0,
                "circle_id": circle_id,
                "text_id": text_id,
                "speed": speed
            })
            
        spawn_delay = max(1800 - (self.score // 80) * 100, 450)
        self.after(spawn_delay, self.spawn_target)

    def game_loop(self):
        if not self.is_active or self.lives <= 0:
            return
            
        H = self.canvas.winfo_height()
        targets_reached_bottom = []
        
        for idx, target in enumerate(self.active_targets):
            target["y"] += target["speed"]
            self.canvas.coords(target["circle_id"], target["x"]-18, target["y"]-18, target["x"]+18, target["y"]+18)
            self.canvas.coords(target["text_id"], target["x"], target["y"])
            
            if target["y"] > H - 20:
                targets_reached_bottom.append(idx)
                
        for idx in reversed(targets_reached_bottom):
            target = self.active_targets.pop(idx)
            self.canvas.delete(target["circle_id"])
            self.canvas.delete(target["text_id"])
            
            self.lives -= 1
            play_sound_async("error", self.master_app.sound_enabled)
            self.update_lives_badge()
            
            if self.lives <= 0:
                self.end_game()
                return
                
        self.after(30, self.game_loop)

    def on_keypress(self, event):
        if not self.is_active or self.lives <= 0:
            return
            
        key = event.char.lower() if event.char else ""
        if not key or key not in self.char_list:
            return
            
        # Find matches. Prioritize lowest targets on screen (highest y-coord)
        match_idx = -1
        highest_y = -1.0
        
        for idx, target in enumerate(self.active_targets):
            if target["char"] == key:
                if target["y"] > highest_y:
                    highest_y = target["y"]
                    match_idx = idx
                    
        if match_idx != -1:
            target = self.active_targets.pop(match_idx)
            
            # Visual laser blast line to target
            W = self.canvas.winfo_width()
            H = self.canvas.winfo_height()
            laser = self.canvas.create_line(W/2, H - 10, target["x"], target["y"], fill=self.theme["accent"], width=3)
            self.after(100, lambda lid=laser: self.canvas.delete(lid))
            
            self.canvas.delete(target["circle_id"])
            self.canvas.delete(target["text_id"])
            
            # Score
            self.score += 15
            self.score_lbl.config(text=f"Score: {self.score}")
            
            # Level increments
            self.level = 1 + (self.score // 250)
            self.base_speed = 1.2 + (self.level - 1) * 0.4
            self.level_lbl.config(text=f"Level: {self.level}")
            
            play_sound_async("click", self.master_app.sound_enabled)
        else:
            # Type error beep
            play_sound_async("error", self.master_app.sound_enabled)

    def update_lives_badge(self):
        badges = "❤️ " * self.lives
        self.lives_lbl.config(text=f"Lives: {badges}")

    def end_game(self):
        self.is_active = False
        self.master_app.unbind("<Key>")
        
        user_id = self.master_app.current_user_id
        conn = db_manager.get_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO game_scores (user_id, game_name, score, level_reached) VALUES (?, ?, ?, ?)", (user_id, "Target Invaders", self.score, self.level))
        conn.commit()
        conn.close()
        
        self.canvas.create_text(
            self.canvas.winfo_width() / 2,
            self.canvas.winfo_height() / 2 - 20,
            text="GAME OVER",
            font=("Segoe UI", 36, "bold"),
            fill=self.theme["error"]
        )
        self.canvas.create_text(
            self.canvas.winfo_width() / 2,
            self.canvas.winfo_height() / 2 + 30,
            text=f"Final score: {self.score} points  |  Level: {self.level}",
            font=("Segoe UI", 14),
            fill=self.theme["text"]
        )

    def quit_game(self):
        self.is_active = False
        self.master_app.unbind("<Key>")
        self.master_app.show_games()

# =====================================================================
# CONFIGURATION SETTINGS VIEW
# =====================================================================
class SettingsPage(tk.Frame):
    def __init__(self, master, master_app, theme):
        super().__init__(master, bg=theme["bg"])
        self.theme = theme
        self.master_app = master_app
        
        # Headings
        self.header_lbl = tk.Label(self, text="Application Settings", font=("Segoe UI", 20, "bold"), bg=theme["bg"], fg=theme["accent"])
        self.header_lbl.pack(anchor="w", pady=(0, 2))
        
        self.sub_lbl = tk.Label(self, text="Configure color palettes and visual settings.", font=("Segoe UI", 10), bg=theme["bg"], fg=theme["muted"])
        self.sub_lbl.pack(anchor="w", pady=(0, 15))
        
        # Configuration Card Panel
        self.card = CardFrame(self, theme, padx=25, pady=25)
        self.card.pack(fill="both", expand=True, pady=10)
        
        # Themes Selector Dropdown OptionMenu
        self.theme_lbl = tk.Label(self.card, text="Interface Color Theme", font=("Segoe UI", 11, "bold"), bg=theme["card_bg"], fg=theme["text"])
        self.theme_lbl.pack(anchor="w", pady=(5, 5))
        
        self.theme_var = tk.StringVar(value=self.master_app.current_theme_name)
        theme_keys = list(THEMES.keys())
        
        # Styled OptionMenu wrapper dropdown
        self.theme_menu = ttk.Combobox(self.card, textvariable=self.theme_var, values=theme_keys, state="readonly", font=("Segoe UI", 10))
        self.theme_menu.pack(anchor="w", fill="x", pady=(0, 30), ipady=4)
        
        # Form submission
        self.save_btn = HoverButton(self.card, text="Save Settings Configuration 💾", command=self.save_settings, theme=theme)
        self.save_btn.pack(fill="x")

    def save_settings(self):
        new_theme = self.theme_var.get()
        
        self.master_app.update_settings(new_theme, False)
        messagebox.showinfo("Success", "Settings configured successfully! Applying values...")
        
        # Immediate refresh page
        self.master_app.show_settings()

# =====================================================================
# Program Root Main Entry
# =====================================================================
if __name__ == "__main__":
    app = TypingApp()
    app.mainloop()

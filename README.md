# SpeedType - Desktop Touch Typing Trainer

SpeedType is a modern, premium desktop touch-typing software built in Python using the `tkinter` GUI framework and `sqlite3`. Taking design inspiration from professional typing utilities like TypingMaster, it offers a complete typing school experience—featuring user profile authentication, progress monitoring with Canvas graphing, a 20-lesson custom-tailored curriculum, custom text loading, visual key interactive highlighting, and retro typing games.

---

## 🚀 Key Features

### 1. 20-Lesson Structured Typing Curriculum
- **Beginner Home, Top, and Bottom Rows**: Progressive drills covering left-hand, right-hand, and combined layouts.
- **Intermediate & Shift Key Practice**: Lessons on capitalization and punctuation.
- **Advanced Numbers & Special Characters**: Mastery drills for symbols and number layouts.
- **Infinite Word Sliding Engine**: Lessons dynamically generate words on-the-fly from the lesson's target keys, providing an endless typing experience. Custom practice loads user words sequentially in a continuous stream.

### 2. Live Performance Metrics & Visual Keyboard
- **Tactile Typing Interface**: Highlights typed text green (correct) or red/underlined (errors) with a retro block cursor.
- **Real-Time Calculation**: Live Words Per Minute (WPM) and Accuracy % counters.
- **Keyboard Visualizer**: Displays a QWERTY layout showing which key to type next (including proper Shift recommendations for capitalized keys or top-row symbols) and flashing keystroke feedback.
- **Time Controls & No-Scroll Sliding Layout**: Practice sessions run for **10 minutes** with **Pause / Resume** overlays. The typing frame displays exactly **2 lines** of text with a **generous line spacing** (`spacing2=18`) and automatically slides text up line-by-line as you type, completely eliminating vertical scroll bars or scrolling visual jumps.

### 3. Gamified Refleshing Modules
- **Word Rain (Falling Words)**: Type whole words and press `Enter` to clear them before they hit the ground. Fall speeds scale with levels.
- **Target Invaders (Single Keys)**: Zap single falling letter UFOs by pressing matching keyboard keys directly. Features colorful laser visuals!

### 4. Progress Dashboard & Statistics
- **Career Reports**: Tracks lifetime average/peak typing speed, overall accuracy, and total lesson attempts.
- **Problem Keys**: Automatically logs your typing errors to report the top 5 keys requiring extra review.
- **Speed Progression Chart**: Renders a custom performance line chart dynamically on a `Canvas` across typing sessions.

### 5. Custom Practice & Aesthetic Themes
- **Importer**: Paste custom paragraphs or upload `.txt` files directly into the practice view.
- **Themes**: Instantly change colors with multiple curated aesthetics:
  - 🌌 **Cyberpunk Dark** (Neon Cyan/Green/Pink on Deep Dark Grey)
  - ☀️ **Classic Light** (Clean Blue/Grey Minimalist)
  - 🌲 **Forest Minimalist** (Sage/Mint/Sage-Green Earthy Theme)

---

## 🛠️ Installation & Setup

### Prerequisites
SpeedType relies purely on **Python 3.x** and its standard libraries. No external package installations (`pip`) are required.

### Getting Started
1. Clone or download this repository:
   ```bash
   git clone https://github.com/yourusername/TouchTypingSoftware.git
   cd TouchTypingSoftware
   ```
2. Run the application:
   ```powershell
   python app.py
   ```

---

## 💾 Technical Architecture & Persistence

SpeedType uses a single-file modular layout ([app.py](file:///d:/Github%20Python%20Projects/TouchTypingSoftware/app.py)) with an integrated SQLite database manager (`typing_software.db`):

- **`users`**: User identifiers and SHA256 hashed credentials.
- **`lessons`**: Seeding tables containing titles, difficulty levels, and generated text contents.
- **`progress`**: Logs user WPM, accuracy, and timestamps for completed sessions.
- **`game_scores`**: Session scores and levels for *Word Rain* and *Target Invaders*.
- **`settings`**: User interface selections (theme preference, sound config).
- **`key_errors`**: Aggregates mistyped keys to generate "Problem Keys" metrics.

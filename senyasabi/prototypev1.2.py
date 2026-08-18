import cv2
import json
import pickle
import random
import tkinter as tk
from tkinter import font as tkfont
from pathlib import Path

import mediapipe as mp
import numpy as np
import tensorflow as tf
from PIL import Image, ImageTk

# ── CONFIG ────────────────────────────────────────────────────────────────────
BASE_DIR      = Path(__file__).resolve().parent
OUTPUT_DIR    = BASE_DIR / 'output'
IMG_DIR       = BASE_DIR / 'img'
MODEL_PATH    = OUTPUT_DIR / 'best_landmark_model.keras'
CLASSES_PATH  = OUTPUT_DIR / 'class_names.json'
SCALER_PATH   = OUTPUT_DIR / 'scaler.pkl'
VRM_SIGNS_DIR = BASE_DIR / 'VRM_SIGNS'
LESSONS_PATH  = BASE_DIR / 'lessons.json'
MAINBG_PATH   = IMG_DIR / 'mainbg.png'

NORM_MODE            = 'scale'
CONFIDENCE_THRESHOLD = 0.70
HOLD_FRAMES          = 18
CAM_INDEX            = 0

# ── Palette ───────────────────────────────────────────────────────────────────
BG          = "#e8f0c8"
BG_RGB      = tuple(int(BG.lstrip('#')[i:i+2], 16) for i in (0, 2, 4))
PANEL_LEFT  = "#f0c842"
PANEL_RIGHT = "#afc8e8"
ACCENT      = "#e8913a"
BTN_BG      = "#f0c842"
BTN_HOVER   = "#e0b030"
TEXT_DARK   = "#3a3020"
TEXT_MID    = "#6a5a30"
HEADER_BG   = "#c8d4a0"
BADGE_GREEN = "#7ab840"
WHITE       = "#ffffff"
GREEN_GOOD  = "#4caf50"
RED_BAD     = "#e53935"
PURPLE      = "#9b59b6"
CARD_BG     = "#faffdc"
MENU_BTN    = "#f0c842"
MENU_BTN_H  = "#e0b030"

# ── Load model ────────────────────────────────────────────────────────────────
print("Loading model…")
model       = tf.keras.models.load_model(MODEL_PATH)
class_names = json.loads(CLASSES_PATH.read_text())
scaler      = pickle.loads(SCALER_PATH.read_bytes())
LESSONS     = json.loads(LESSONS_PATH.read_text(encoding="utf-8"))
print(f"Loaded — {len(class_names)} classes")

# ── MediaPipe ─────────────────────────────────────────────────────────────────
mp_hands   = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils
hands = mp_hands.Hands(static_image_mode=False, max_num_hands=1,
                       min_detection_confidence=0.5, min_tracking_confidence=0.5)

# ── Core helpers ──────────────────────────────────────────────────────────────
def extract_landmarks(frame):
    rgb    = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    result = hands.process(rgb)
    if not result.multi_hand_landmarks:
        return None, result
    lm     = result.multi_hand_landmarks[0].landmark
    coords = np.array([[l.x, l.y, l.z] for l in lm])
    origin = coords[0]; coords -= origin
    scale  = np.linalg.norm(coords[9])
    if scale == 0: return None, result
    coords /= scale
    return coords.flatten(), result

def predict(features):
    scaled = scaler.transform([features])
    probs  = model.predict(scaled, verbose=0)[0]
    idx    = int(np.argmax(probs))
    return class_names[idx], float(probs[idx])

def load_vrm_image(label, size=(480, 480)):
    for ext in ('.png', '.jpg', '.jpeg', '.webp'):
        p = VRM_SIGNS_DIR / f"{label}{ext}"
        if p.exists():
            img = Image.open(p).convert("RGBA")
            img.thumbnail(size, Image.LANCZOS)
            canvas = Image.new("RGBA", size, (240, 200, 66, 255))
            canvas.paste(img, ((size[0]-img.width)//2, (size[1]-img.height)//2), img)
            return ImageTk.PhotoImage(canvas)
    return None

def placeholder_vrm(size=(480,480)):
    return ImageTk.PhotoImage(Image.new("RGBA", size, (240, 200, 66, 255)))

# ── Shared header ─────────────────────────────────────────────────────────────
def build_header(parent, left_extra=None):
    hdr = tk.Frame(parent, bg=HEADER_BG, height=52)
    hdr.pack(fill="x"); hdr.pack_propagate(False)
    logo_f = tk.Frame(hdr, bg=HEADER_BG)
    logo_f.pack(side="left", padx=14, pady=8)
    c = tk.Canvas(logo_f, width=32, height=32, bg=HEADER_BG, highlightthickness=0)
    c.pack(side="left")
    c.create_oval(2,2,30,30, fill=ACCENT, outline="")
    c.create_text(16,16, text="S", fill=WHITE, font=("Helvetica",14,"bold"))
    tk.Label(logo_f, text="SenyaSabi", bg=HEADER_BG, fg=TEXT_DARK,
             font=("Helvetica",15,"bold")).pack(side="left", padx=6)
    if left_extra: left_extra(hdr)
    bf = tk.Frame(hdr, bg=HEADER_BG); bf.pack(side="right", padx=14, pady=8)
    for txt,bg,fg in [("🔥 67 Days",ACCENT,WHITE),("⭐ Master",BADGE_GREEN,WHITE),("6.7k W",WHITE,TEXT_DARK)]:
        f = tk.Frame(bf, bg=bg, padx=10, pady=4)
        tk.Label(f, text=txt, bg=bg, fg=fg, font=("Helvetica",11,"bold")).pack()
        f.pack(side="left", padx=4)

def menu_btn(parent, text, cmd, w=260, h=58, bg=MENU_BTN, fg=TEXT_DARK):
    f = tk.Frame(parent, bg=bg, cursor="hand2", width=w, height=h)
    f.pack_propagate(False)
    lbl = tk.Label(f, text=text, bg=bg, fg=fg, font=("Helvetica",16,"bold"), cursor="hand2")
    lbl.place(relx=.5, rely=.5, anchor="center")
    def enter(e): f.config(bg=MENU_BTN_H); lbl.config(bg=MENU_BTN_H)
    def leave(e): f.config(bg=bg); lbl.config(bg=bg)
    def click(e): cmd()
    for w2 in (f, lbl):
        w2.bind("<Enter>", enter); w2.bind("<Leave>", leave); w2.bind("<Button-1>", click)
    return f

def back_btn(parent, cmd):
    tk.Button(parent, text="← Back", font=("Helvetica",11),
              bg=CARD_BG, fg=TEXT_DARK, relief="flat", padx=10, pady=4,
              cursor="hand2", command=cmd).pack(side="left", padx=8)

def build_taskbar(parent, app, active=None):
    """Bottom navigation taskbar."""
    TB = "#b8c890"
    bar = tk.Frame(parent, bg=TB, height=58)
    bar.pack(fill="x", side="bottom")
    bar.pack_propagate(False)
    tabs = [
        ("🏠",  "Home",            app.go_main,                None),
        ("📷",  "Recognizer",      app.go_recognizer,          "recognizer"),
        ("🔤",  "Alphabet",        app.go_alphabet_menu,       "alphabet"),
        ("✋",  "FingerSpelling",  app.go_fingerspelling_menu, "fingerspelling"),
        ("🔀",  "MegaShuffle",     app.go_megashuffle,         "megashuffle"),
    ]
    for icon, label, cmd, key in tabs:
        active_tab = (key == active)
        col = ACCENT if active_tab else TB
        fgc = WHITE  if active_tab else TEXT_DARK
        f = tk.Frame(bar, bg=col, cursor="hand2", padx=16, pady=4)
        f.pack(side="left", fill="y")
        tk.Label(f, text=icon,  bg=col, fg=fgc, font=("Helvetica",15)).pack()
        tk.Label(f, text=label, bg=col, fg=fgc, font=("Helvetica",8,"bold")).pack()
        hover = BTN_HOVER if not active_tab else col
        def _en(e, ff=f, h=hover):
            ff.config(bg=h)
            for ch in ff.winfo_children(): ch.config(bg=h)
        def _le(e, ff=f, c=col):
            ff.config(bg=c)
            for ch in ff.winfo_children(): ch.config(bg=c)
        def _cl(e, c=cmd): c()
        for w in [f] + f.winfo_children():
            w.bind("<Enter>", _en); w.bind("<Leave>", _le); w.bind("<Button-1>", _cl)
    # Quit
    qf = tk.Frame(bar, bg=TB, cursor="hand2", padx=16, pady=4)
    qf.pack(side="right", fill="y")
    tk.Label(qf, text="✕",    bg=TB, fg=RED_BAD, font=("Helvetica",15)).pack()
    tk.Label(qf, text="Quit", bg=TB, fg=RED_BAD, font=("Helvetica",8,"bold")).pack()
    def _qen(e):
        qf.config(bg=RED_BAD)
        for ch in qf.winfo_children(): ch.config(bg=RED_BAD, fg=WHITE)
    def _qle(e):
        qf.config(bg=TB)
        for ch in qf.winfo_children(): ch.config(bg=TB, fg=RED_BAD)
    for w in [qf] + qf.winfo_children():
        w.bind("<Enter>", _qen); w.bind("<Leave>", _qle)
        w.bind("<Button-1>", lambda e: (hands.close(), parent.winfo_toplevel().destroy()))
    return bar


# ══════════════════════════════════════════════════════════════════════════════
# MAIN MENU
# ══════════════════════════════════════════════════════════════════════════════
class MainMenu(tk.Frame):
    def __init__(self, root, app):
        super().__init__(root)
        self.app = app
        self.pack(fill="both", expand=True)
        root.title("SenyaSabi: Prototype v1.2")
        self._build()
        build_taskbar(self, app, active=None)

    def _build(self):
        # Background image
        try:
            bg_img = Image.open(MAINBG_PATH)
            sw = self.app.root.winfo_screenwidth()
            sh = self.app.root.winfo_screenheight()
            bg_img = bg_img.resize((sw, sh), Image.LANCZOS)
            self._bg = ImageTk.PhotoImage(bg_img)
            canvas = tk.Canvas(self, highlightthickness=0)
            canvas.pack(fill="both", expand=True)
            canvas.create_image(0, 0, image=self._bg, anchor="nw")
            container = canvas
        except Exception:
            container = self
            self.config(bg=BG)

        # Title card
        title_f = tk.Frame(container, bg="#faffdc", bd=0)
        title_f.place(relx=0.1, rely=0.12)
        tk.Label(title_f, text="SenyaSabi", bg="#faffdc", fg=TEXT_DARK,
                 font=("Helvetica", 42, "bold")).pack(anchor="w", padx=24, pady=(18,0))
        tk.Label(title_f, text="Prototype v1.2", bg="#faffdc", fg=TEXT_MID,
                 font=("Helvetica", 16)).pack(anchor="w", padx=24)
        tk.Label(title_f, text="",
                 bg="#faffdc", fg=TEXT_MID, font=("Helvetica", 13)).pack(anchor="w", padx=24, pady=(0,18))

        # Buttons
        btn_f = tk.Frame(container, bg="#f5f8e0")
        btn_f.place(relx=0.08, rely=0.45)

        entries = [
            ("📷  Recognizer",     self.app.go_recognizer),
            ("🔤  Alphabet",       self.app.go_alphabet_menu),
            ("✋  FingerSpelling",  self.app.go_fingerspelling_menu),
            ("🔀  MegaShuffle",    self.app.go_megashuffle),
        ]
        colors = [ACCENT, BADGE_GREEN, "#5090d0", PURPLE]
        for i, ((txt, cmd), col) in enumerate(zip(entries, colors)):
            menu_btn(btn_f, txt, cmd, w=300, h=62, bg=col, fg=WHITE).pack(pady=8)

# ══════════════════════════════════════════════════════════════════════════════
# ALPHABET SUBMENU
# ══════════════════════════════════════════════════════════════════════════════
class AlphabetMenu(tk.Frame):
    def __init__(self, root, app):
        super().__init__(root, bg=BG)
        self.app = app
        self.pack(fill="both", expand=True)
        root.title("SenyaSabi — Alphabet")
        self._build()
        build_taskbar(self, app, active="alphabet")

    def _build(self):
        def le(hdr): back_btn(hdr, self.app.go_main)
        build_header(self, le)
        body = tk.Frame(self, bg=BG)
        body.pack(expand=True)
        tk.Label(body, text="Alphabet Mode", bg=BG, fg=TEXT_DARK,
                 font=("Helvetica",28,"bold")).pack(pady=(40,8))
        tk.Label(body, text="Practice the FSL alphabet A–Z",
                 bg=BG, fg=TEXT_MID, font=("Helvetica",13)).pack(pady=(0,36))
        menu_btn(body, "📖  Normal Lesson  (A → Z)", lambda: self.app.go_lesson("lesson"), w=320, h=62).pack(pady=10)
        menu_btn(body, "🔀  Shuffle",                lambda: self.app.go_lesson("shuffle"), w=320, h=62).pack(pady=10)

# ══════════════════════════════════════════════════════════════════════════════
# FINGERSPELLING SUBMENU
# ══════════════════════════════════════════════════════════════════════════════
class FingerSpellingMenu(tk.Frame):
    def __init__(self, root, app):
        super().__init__(root, bg=BG)
        self.app = app
        self.pack(fill="both", expand=True)
        root.title("SenyaSabi — FingerSpelling")
        self._build()
        build_taskbar(self, app, active="fingerspelling")

    def _build(self):
        def le(hdr): back_btn(hdr, self.app.go_main)
        build_header(self, le)
        body = tk.Frame(self, bg=BG)
        body.pack(expand=True)
        tk.Label(body, text="FingerSpelling", bg=BG, fg=TEXT_DARK,
                 font=("Helvetica",28,"bold")).pack(pady=(40,8))
        tk.Label(body, text="Spell Filipino words using FSL signs",
                 bg=BG, fg=TEXT_MID, font=("Helvetica",13)).pack(pady=(0,36))
        entries = [
            ("🔀  Shuffle",      lambda: self.app.go_word_lesson(None, None, mode="shuffle")),
            ("📚  Categories",   self.app.go_categories),
            ("  Coming Soon",     self.app.go_type_it_menu),
            ("✋  Sign It",      self.app.go_sign_it_menu),
        ]
        colors = [BADGE_GREEN, ACCENT, "#5090d0", PURPLE]
        for (txt,cmd), col in zip(entries, colors):
            menu_btn(body, txt, cmd, w=300, h=62, bg=col, fg=WHITE).pack(pady=8)

# ══════════════════════════════════════════════════════════════════════════════
# CATEGORIES SCREEN
# ══════════════════════════════════════════════════════════════════════════════
class CategoriesScreen(tk.Frame):
    """Shows category buttons only. Click one to open WordsScreen."""
    def __init__(self, root, app, mode="sign"):
        super().__init__(root, bg=BG)
        self.app  = app
        self.mode = mode
        self.pack(fill="both", expand=True)
        root.title("SenyaSabi — Categories")
        self._build()
        build_taskbar(self, app, active="fingerspelling")

    def _build(self):
        def le(hdr): back_btn(hdr, self.app.go_fingerspelling_menu)
        build_header(self, le)

        tk.Label(self, text="Choose a Category", bg=BG, fg=TEXT_DARK,
                 font=("Helvetica",22,"bold")).pack(pady=(28,6))
        tk.Label(self, text="Click a category to see its words",
                 bg=BG, fg=TEXT_MID, font=("Helvetica",12)).pack(pady=(0,20))

        grid_f = tk.Frame(self, bg=BG)
        grid_f.pack(expand=True)

        COLS = 3
        for i, (cat, words) in enumerate(LESSONS.items()):
            r, c = divmod(i, COLS)
            card = tk.Frame(grid_f, bg=CARD_BG, cursor="hand2",
                            width=280, height=100, bd=0)
            card.grid(row=r, column=c, padx=14, pady=10)
            card.pack_propagate(False)

            tk.Label(card, text=cat, bg=CARD_BG, fg=TEXT_DARK,
                     font=("Helvetica",13,"bold"), wraplength=240,
                     justify="center", cursor="hand2").place(relx=.5, rely=.42, anchor="center")
            tk.Label(card, text=f"{len(words)} words", bg=CARD_BG, fg=TEXT_MID,
                     font=("Helvetica",10), cursor="hand2").place(relx=.5, rely=.76, anchor="center")

            def _en(e, f=card):
                f.config(bg=BTN_HOVER)
                for ch in f.winfo_children(): ch.config(bg=BTN_HOVER)
            def _le(e, f=card):
                f.config(bg=CARD_BG)
                for ch in f.winfo_children(): ch.config(bg=CARD_BG)
            def _cl(e, ca=cat): self.app.go_words_screen(ca, self.mode)
            for w in [card] + card.winfo_children():
                w.bind("<Enter>", _en); w.bind("<Leave>", _le); w.bind("<Button-1>", _cl)


class WordsScreen(tk.Frame):
    """Shows all words in a category. Click one to start the lesson."""
    def __init__(self, root, app, category, mode="sign"):
        super().__init__(root, bg=BG)
        self.app      = app
        self._cat     = category
        self.mode     = mode
        self.pack(fill="both", expand=True)
        root.title(f"SenyaSabi — {category}")
        self._build()
        build_taskbar(self, app, active="fingerspelling")

    def _build(self):
        def le(hdr):
            back_btn(hdr, lambda: self.app.go_categories(self.mode))
            tk.Label(hdr, text=self._cat, bg=HEADER_BG, fg=TEXT_MID,
                     font=("Helvetica",11,"bold")).pack(side="left", padx=4)
        build_header(self, le)

        # Shuffle button row
        top = tk.Frame(self, bg=BG); top.pack(fill="x", padx=30, pady=(16,4))
        tk.Label(top, text=self._cat, bg=BG, fg=TEXT_DARK,
                 font=("Helvetica",20,"bold")).pack(side="left")
        tk.Button(top, text="🔀  Shuffle category", font=("Helvetica",11,"bold"),
                  bg=BADGE_GREEN, fg=WHITE, relief="flat", padx=12, pady=6,
                  cursor="hand2",
                  command=lambda: self.app.go_word_lesson(self._cat, None, mode="shuffle_cat")
                  ).pack(side="right")

        outer = tk.Frame(self, bg=BG)
        outer.pack(fill="both", expand=True, padx=30, pady=(8,8))
        canvas = tk.Canvas(outer, bg=BG, highlightthickness=0)
        sb = tk.Scrollbar(outer, orient="vertical", command=canvas.yview)
        inner = tk.Frame(canvas, bg=BG)
        inner.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0,0), window=inner, anchor="nw")
        canvas.configure(yscrollcommand=sb.set)
        canvas.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")
        canvas.bind_all("<MouseWheel>",
                        lambda e: canvas.yview_scroll(int(-1*(e.delta/120)), "units"))

        row = tk.Frame(inner, bg=BG); row.pack(fill="x", pady=6)
        for word in LESSONS[self._cat]:
            letters = [c for c in word if c != ' ']
            chip = tk.Frame(row, bg=BTN_BG, padx=12, pady=8, cursor="hand2")
            chip.pack(side="left", padx=(0,8), pady=4)
            lbl  = tk.Label(chip, text=word, bg=BTN_BG, fg=TEXT_DARK,
                            font=("Helvetica",12,"bold"), cursor="hand2")
            lbl.pack(side="left")
            cnt  = tk.Label(chip, text=f"{len(letters)}L", bg=ACCENT, fg=WHITE,
                            font=("Helvetica",8,"bold"), padx=4, pady=1)
            cnt.pack(side="left", padx=(6,0))
            def _en(e, c=chip, l=lbl, b=cnt):
                c.config(bg=ACCENT); l.config(bg=ACCENT, fg=WHITE); b.config(bg=CARD_BG, fg=ACCENT)
            def _le(e, c=chip, l=lbl, b=cnt):
                c.config(bg=BTN_BG); l.config(bg=BTN_BG, fg=TEXT_DARK); b.config(bg=ACCENT, fg=WHITE)
            def _cl(e, w=word): self.app.go_word_lesson(self._cat, w, mode=self.mode)
            for ww in (chip, lbl, cnt):
                ww.bind("<Enter>",_en); ww.bind("<Leave>",_le); ww.bind("<Button-1>",_cl)

# ══════════════════════════════════════════════════════════════════════════════
# TYPE IT — show VRM sign one at a time, user presses the key
# ══════════════════════════════════════════════════════════════════════════════
class TypeItScreen(tk.Frame):
    VRM_W, VRM_H = 480, 480
    STATE_WAITING  = "waiting"
    STATE_FEEDBACK = "feedback"
    STATE_DONE     = "done"

    def __init__(self, root, app, category, word):
        super().__init__(root, bg=BG)
        self.app      = app
        self._cat     = category
        self._word    = word
        self._letters = [c for c in word if c != ' ']
        self._idx     = 0
        self._score   = 0
        self._state   = self.STATE_WAITING
        self._after_id= None
        self._vrm_cache = {}
        self._ph      = placeholder_vrm((self.VRM_W, self.VRM_H))
        self.pack(fill="both", expand=True)
        root.title(f"SenyaSabi — Type It: {word}")
        self._build()
        build_taskbar(self, app, active="fingerspelling")
        self._load_letter()
        root.bind("<Key>", self._on_key)

    def _build(self):
        def le(hdr):
            back_btn(hdr, self._go_back)
            tk.Label(hdr, text=f"  Coming Soon — {self._cat}", bg=HEADER_BG,
                     fg=TEXT_MID, font=("Helvetica",11)).pack(side="left", padx=8)
        build_header(self, le)

        body = tk.Frame(self, bg=BG)
        body.pack(fill="both", expand=True, padx=30, pady=20)

        # Left: VRM
        left = tk.Frame(body, bg=BG); left.pack(side="left", fill="y")
        vrm_f = tk.Frame(left, bg=PANEL_LEFT, width=self.VRM_W, height=self.VRM_H)
        vrm_f.pack(); vrm_f.pack_propagate(False)
        self.vrm_lbl = tk.Label(vrm_f, bg=PANEL_LEFT, image=self._ph)
        self.vrm_lbl.pack(expand=True)

        # Right: word tiles + input area
        right = tk.Frame(body, bg=BG); right.pack(side="left", fill="both", expand=True, padx=30)

        # Word tiles row
        self._tiles_f = tk.Frame(right, bg=BG)
        self._tiles_f.pack(pady=(0,20))

        # Feedback label
        self._fb_var = tk.StringVar(value="")
        self._fb_lbl = tk.Label(right, textvariable=self._fb_var, bg=BG,
                                font=("Helvetica",22,"bold"), fg=GREEN_GOOD)
        self._fb_lbl.pack(pady=10)

        tk.Label(right, text="Press the correct letter key", bg=BG,
                 fg=TEXT_MID, font=("Helvetica",13)).pack(pady=(0,10))

        # Status
        self._status_var = tk.StringVar(value="")
        tk.Label(right, textvariable=self._status_var, bg=BG,
                 fg=TEXT_MID, font=("Helvetica",11)).pack()

        # Post-done buttons (hidden)
        self._post_f = tk.Frame(right, bg=BG)
        for txt, cmd in [("↺ Try Again", self._restart), ("← Back", self._go_back)]:
            tk.Button(self._post_f, text=txt, font=("Helvetica",12,"bold"),
                      bg=ACCENT, fg=WHITE, relief="flat", padx=14, pady=6,
                      cursor="hand2", command=cmd).pack(side="left", padx=6)

    def _load_letter(self):
        self._state = self.STATE_WAITING
        letter = self._letters[self._idx]
        img = self._get_vrm(letter)
        self.vrm_lbl.config(image=img)
        self._refresh_tiles()
        self._fb_var.set("")
        self._status_var.set(f"Sign shown: press  '{letter}'  on your keyboard  ({self._idx+1}/{len(self._letters)})")

    def _refresh_tiles(self):
        for w in self._tiles_f.winfo_children(): w.destroy()
        for i, ch in enumerate(self._letters):
            if i < self._idx:
                bg, fg = BADGE_GREEN, WHITE
            elif i == self._idx:
                bg, fg = ACCENT, WHITE
            else:
                bg, fg = CARD_BG, TEXT_MID
            f = tk.Frame(self._tiles_f, bg=bg, width=52, height=52); f.pack(side="left", padx=3)
            f.pack_propagate(False)
            tk.Label(f, text=ch, bg=bg, fg=fg, font=("Helvetica",22,"bold")).pack(expand=True)

    def _on_key(self, event):
        if self._state != self.STATE_WAITING: return
        pressed = event.char.upper()
        target  = self._letters[self._idx]
        if pressed == target:
            self._score += 1
            self._state  = self.STATE_FEEDBACK
            self._fb_lbl.config(fg=GREEN_GOOD)
            self._fb_var.set("✓  Correct!")
            self._after_id = self.master.after(800, self._advance)
        else:
            self._state = self.STATE_FEEDBACK
            self._fb_lbl.config(fg=RED_BAD)
            self._fb_var.set(f"✗  That was '{pressed}' — try again!")
            self._after_id = self.master.after(700, self._back_to_waiting)

    def _back_to_waiting(self):
        self._state = self.STATE_WAITING
        self._fb_var.set("")
        self._status_var.set(f"Sign shown: press  '{self._letters[self._idx]}'  ({self._idx+1}/{len(self._letters)})")

    def _advance(self):
        self._idx += 1
        if self._idx >= len(self._letters): self._show_done()
        else: self._load_letter()

    def _show_done(self):
        self._state = self.STATE_DONE
        pct   = int(self._score/len(self._letters)*100)
        emoji = "🌟 Perfect!" if pct==100 else "👏 Well done!" if pct>=70 else "💪 Keep practising!"
        self._fb_lbl.config(fg=GREEN_GOOD if pct>=70 else RED_BAD)
        self._fb_var.set(f'"{self._word}" — {self._score}/{len(self._letters)}  ({pct}%)\n{emoji}')
        self._refresh_tiles()
        self._status_var.set("")
        self._post_f.pack(pady=16)

    def _restart(self):
        if self._after_id: self.master.after_cancel(self._after_id)
        self._post_f.pack_forget()
        self._idx = 0; self._score = 0
        self._load_letter()

    def _go_back(self):
        self.master.unbind("<Key>")
        self.app.go_categories(mode="type")

    def _get_vrm(self, label):
        if label not in self._vrm_cache:
            self._vrm_cache[label] = load_vrm_image(label,(self.VRM_W,self.VRM_H)) or self._ph
        return self._vrm_cache[label]

# ══════════════════════════════════════════════════════════════════════════════
# SIGN IT / WORD LESSON  (camera-based word spelling)
# ══════════════════════════════════════════════════════════════════════════════
class SignItScreen(tk.Frame):
    CAM_W, CAM_H = 1000, 1200
    VRM_W, VRM_H = 480, 480
    BTN_SIZE     = 44
    STATE_WAITING  = "waiting"
    STATE_FEEDBACK = "feedback"
    STATE_DONE     = "done"

    def __init__(self, root, app, category, word, queue=None, q_idx=0):
        super().__init__(root, bg=BG)
        self.app      = app
        self._cat     = category
        self._word    = word
        self._letters = [c for c in word if c != ' ']
        self._idx     = 0
        self._score   = 0
        self._state   = self.STATE_WAITING
        self._hold    = 0
        self._fb_id   = None
        self._paused  = False
        self._vrm_cache = {}
        self._ph      = placeholder_vrm((self.VRM_W, self.VRM_H))
        # For queue-based modes (shuffle / mega)
        self._queue   = queue
        self._q_idx   = q_idx
        self.pack(fill="both", expand=True)
        root.title(f"SenyaSabi — Sign It: {word}")
        self._build()
        build_taskbar(self, app, active="fingerspelling")
        self._load_letter()
        self.cap = cv2.VideoCapture(CAM_INDEX)
        self.running = True
        self._update()

    def _build(self):
        def le(hdr):
            back_btn(hdr, self._go_back)
            tk.Label(hdr, text=f"✋ Sign It — {self._cat}", bg=HEADER_BG,
                     fg=TEXT_MID, font=("Helvetica",11)).pack(side="left", padx=8)
            tk.Button(hdr, text="⏸", font=("Helvetica",12),
                      bg=ACCENT, fg=WHITE, relief="flat", padx=8, pady=2,
                      cursor="hand2", command=self._toggle_pause).pack(side="left")
        build_header(self, le)

        body = tk.Frame(self, bg=BG)
        body.pack(fill="both", expand=True, padx=16, pady=(12,4))

        # Left: VRM
        lw = tk.Frame(body, bg=BG); lw.pack(side="left", fill="y")
        vf = tk.Frame(lw, bg=PANEL_LEFT, width=self.VRM_W, height=self.VRM_H)
        vf.pack(); vf.pack_propagate(False)
        self.vrm_lbl = tk.Label(vf, bg=PANEL_LEFT, image=self._ph)
        self.vrm_lbl.pack(expand=True)
        self._word_f = tk.Frame(lw, bg=BG); self._word_f.pack(pady=(8,0))

        # Centre buttons
        mid = tk.Frame(body, bg=BG, width=60); mid.pack(side="left", fill="y", padx=8)
        mid.pack_propagate(False); tk.Frame(mid, bg=BG).pack(expand=True)
        for icon,cmd,bg,fg in [("→",self._skip,BTN_BG,TEXT_DARK),
                                ("↺",self._restart,BTN_BG,TEXT_DARK)]:
            b = tk.Canvas(mid, width=self.BTN_SIZE, height=self.BTN_SIZE,
                          bg=BG, highlightthickness=0, cursor="hand2")
            r = self.BTN_SIZE//2
            ov = b.create_oval(2,2,self.BTN_SIZE-2,self.BTN_SIZE-2, fill=bg, outline="")
            b.create_text(r,r, text=icon, fill=fg, font=("Helvetica",int(r*0.8),"bold"))
            b.bind("<Button-1>", lambda e,c=cmd: c())
            b.pack(pady=5)
        tk.Frame(mid, bg=BG).pack(expand=True)

        # Right: camera
        right = tk.Frame(body, bg=PANEL_RIGHT, width=self.CAM_W, height=self.CAM_H)
        right.pack(side="left", fill="both", expand=True); right.pack_propagate(False)
        self.cam_lbl = tk.Label(right, bg=PANEL_RIGHT)
        self.cam_lbl.place(x=0,y=0,width=self.CAM_W,height=self.CAM_H)

        self._ov_f = tk.Frame(right, bg="", highlightthickness=0)
        self._ov_l = tk.Label(self._ov_f, text="", bg=GREEN_GOOD, fg=WHITE,
                              font=("Helvetica",22,"bold"), padx=20, pady=10,
                              wraplength=400, justify="center")
        self._ov_l.pack(); self._ov_f.place_forget()

        self._post_f = tk.Frame(right, bg=PANEL_RIGHT)
        for txt,cmd in [("↺ Try Again",self._restart),("← Back",self._go_back)]:
            tk.Button(self._post_f, text=txt, font=("Helvetica",12,"bold"),
                      bg=ACCENT, fg=WHITE, relief="flat", padx=14, pady=6,
                      cursor="hand2", command=cmd).pack(side="left", padx=6)
        if self._queue:
            tk.Button(self._post_f, text="Next →", font=("Helvetica",12,"bold"),
                      bg=BADGE_GREEN, fg=WHITE, relief="flat", padx=14, pady=6,
                      cursor="hand2", command=self._next_word).pack(side="left", padx=6)
        self._post_f.place_forget()

        bar_bg = tk.Frame(right, bg="#90aec8", height=10)
        bar_bg.place(relx=0,rely=1.0,anchor="sw",width=self.CAM_W,y=0)
        self._cbar = tk.Frame(bar_bg, bg=ACCENT, height=10)
        self._cbar.place(x=0,y=0,width=0,height=10)

        self.pred_var = tk.StringVar(value=""); self.conf_var = tk.StringVar(value="")
        pov = tk.Frame(right, bg=PANEL_RIGHT)
        pov.place(relx=0,rely=1.0,anchor="sw",x=6,y=-14)
        tk.Label(pov,textvariable=self.pred_var,font=("Helvetica",42,"bold"),
                 fg=ACCENT,bg=PANEL_RIGHT).pack(side="left")
        tk.Label(pov,textvariable=self.conf_var,font=("Helvetica",12),
                 fg=TEXT_DARK,bg=PANEL_RIGHT).pack(side="left",padx=4,pady=(16,0))

        # Status bar
        bar = tk.Frame(self, bg=HEADER_BG, height=32); bar.pack(fill="x",side="bottom")
        bar.pack_propagate(False)
        self._dots_f = tk.Frame(bar, bg=HEADER_BG); self._dots_f.pack(side="left",padx=12,pady=10)
        self._draw_dots()
        self.status_var = tk.StringVar(value="")
        self._st_lbl = tk.Label(bar, textvariable=self.status_var, bg=HEADER_BG,
                                fg=TEXT_MID, font=("Helvetica",11))
        self._st_lbl.pack(side="left",padx=16)
        tk.Button(bar, text="Quit", font=("Helvetica",11), bg=ACCENT, fg=WHITE,
                  relief="flat", padx=12, pady=0, cursor="hand2",
                  command=self._quit).pack(side="right",padx=8,pady=4)

    def _draw_dots(self):
        for w in self._dots_f.winfo_children(): w.destroy()
        n = len(self._letters)
        c = tk.Canvas(self._dots_f, width=n*16, height=12, bg=HEADER_BG, highlightthickness=0)
        c.pack()
        self._dot_canvas = c
        self._dot_items = []
        for i in range(n):
            x = i*16+6
            o = c.create_oval(x-5,1,x+5,11, fill="#c8c0a0", outline="")
            self._dot_items.append(o)
        self._update_dots()

    def _update_dots(self):
        for i,o in enumerate(self._dot_items):
            fill = BADGE_GREEN if i<self._idx else ACCENT if i==self._idx else "#c8c0a0"
            self._dot_canvas.itemconfig(o, fill=fill)

    def _load_letter(self):
        self._state = self.STATE_WAITING; self._hold = 0
        letter = self._letters[self._idx]
        self.vrm_lbl.config(image=self._get_vrm(letter))
        self._refresh_word()
        self._hide_ov()
        self._update_dots()
        self.status_var.set(f"Sign  →  {letter}  ({self._idx+1}/{len(self._letters)})")

    def _refresh_word(self):
        for w in self._word_f.winfo_children(): w.destroy()
        li = 0
        for ch in self._word:
            if ch == ' ':
                tk.Label(self._word_f,text=" ",bg=BG,font=("Helvetica",28,"bold")).pack(side="left"); continue
            if li < self._idx:   bg,fg = BADGE_GREEN, WHITE
            elif li == self._idx: bg,fg = ACCENT, WHITE
            else:                 bg,fg = CARD_BG, TEXT_MID
            f = tk.Frame(self._word_f,bg=bg,padx=5,pady=3); f.pack(side="left",padx=2)
            tk.Label(f,text=ch,bg=bg,fg=fg,font=("Helvetica",26,"bold")).pack()
            li += 1

    def _on_correct(self,conf):
        self._score+=1; self._state=self.STATE_FEEDBACK
        self._show_ov(f"{int(conf*100)}%  Great Job! 🎉",good=True)
        self._fb_id=self.master.after(1200,self._advance)

    def _on_wrong(self,conf):
        if self._state!=self.STATE_WAITING: return
        self._state=self.STATE_FEEDBACK
        self._show_ov(f"{int(conf*100)}%  Try Again.",good=False)
        self._fb_id=self.master.after(900,self._back_waiting)

    def _back_waiting(self):
        self._state=self.STATE_WAITING; self._hold=0; self._hide_ov()
        self.status_var.set(f"Sign  →  {self._letters[self._idx]}  ({self._idx+1}/{len(self._letters)})")

    def _advance(self):
        self._idx+=1
        if self._idx>=len(self._letters): self._show_done()
        else: self._load_letter()

    def _show_done(self):
        self._state=self.STATE_DONE
        pct=int(self._score/len(self._letters)*100)
        emoji="🌟 Perfect!" if pct==100 else "👏 Well done!" if pct>=70 else "💪 Keep practising!"
        self._show_ov(f'"{self._word}"\n{self._score}/{len(self._letters)} ({pct}%)\n{emoji}',
                      good=(pct>=70),big=True)
        self._refresh_word(); self.status_var.set("Word complete!")
        self._post_f.place(relx=0.5,rely=0.88,anchor="center")

    def _next_word(self):
        if not self._queue: return
        nxt = self._q_idx+1
        if nxt>=len(self._queue):
            self._go_back(); return
        self.running=False; self.cap.release(); self.destroy()
        cat,word = self._queue[nxt]
        SignItScreen(self.master,self.app,cat,word,self._queue,nxt)

    def _skip(self):
        if self._fb_id: self.master.after_cancel(self._fb_id)
        self._advance()

    def _restart(self):
        if self._fb_id: self.master.after_cancel(self._fb_id)
        self._idx=0; self._score=0; self._load_letter()

    def _toggle_pause(self):
        self._paused=not self._paused
        self.status_var.set("Paused" if self._paused else f"Sign  →  {self._letters[self._idx]}")

    def _go_back(self):
        self.running=False; self.cap.release(); self.destroy()
        self.app.go_fingerspelling_menu()

    def _quit(self):
        self.running=False; self.cap.release(); hands.close(); self.master.destroy()

    def _show_ov(self,msg,good=True,big=False):
        self._ov_l.config(text=msg,bg=GREEN_GOOD if good else RED_BAD,
                          font=("Helvetica",26 if big else 22,"bold"))
        self._ov_f.place(relx=0.5,rely=0.42,anchor="center"); self._ov_f.lift()

    def _hide_ov(self):
        self._ov_f.place_forget(); self._post_f.place_forget()

    def _set_cbar(self,conf,green=False):
        self._cbar.config(bg=GREEN_GOOD if green else ACCENT)
        self._cbar.place(x=0,y=0,width=int(self.CAM_W*conf),height=10)

    def _get_vrm(self,label):
        if label not in self._vrm_cache:
            self._vrm_cache[label]=load_vrm_image(label,(self.VRM_W,self.VRM_H)) or self._ph
        return self._vrm_cache[label]

    def _update(self):
        if not self.running: return
        if self._paused or self._state==self.STATE_DONE:
            self.master.after(80,self._update); return
        ret,frame=self.cap.read()
        if not ret: self.master.after(120,self._update); return
        frame=cv2.flip(frame,1); display=frame.copy()
        features,mp_result=extract_landmarks(frame)
        if mp_result.multi_hand_landmarks:
            for hl in mp_result.multi_hand_landmarks:
                mp_drawing.draw_landmarks(display,hl,mp_hands.HAND_CONNECTIONS,
                    mp_drawing.DrawingSpec(color=(255,255,255),thickness=2,circle_radius=3),
                    mp_drawing.DrawingSpec(color=(232,145,58), thickness=2,circle_radius=2))
        if features is not None:
            label,conf=predict(features)
            self.pred_var.set(label); self.conf_var.set(f"{conf*100:.0f}%")
            if self._state==self.STATE_WAITING:
                if label==self._letters[self._idx] and conf>=CONFIDENCE_THRESHOLD:
                    self._hold+=1; self._set_cbar(conf,green=True)
                    if self._hold>=HOLD_FRAMES: self._on_correct(conf)
                else:
                    if self._hold>0: self._hold=0; self._set_cbar(conf); self._on_wrong(conf)
                    else: self._set_cbar(conf)
        else:
            self.pred_var.set("—"); self.conf_var.set(""); self._set_cbar(0); self._hold=0
        rgb=cv2.cvtColor(display,cv2.COLOR_BGR2RGB)
        w=self.cam_lbl.winfo_width() or self.CAM_W
        h=self.cam_lbl.winfo_height() or self.VRM_H
        pil=Image.fromarray(rgb).resize((w,h),Image.BILINEAR)
        imgtk=ImageTk.PhotoImage(image=pil)
        self.cam_lbl.imgtk=imgtk; self.cam_lbl.configure(image=imgtk)
        self.master.after(15,self._update)

# ══════════════════════════════════════════════════════════════════════════════
# ALPHABET LESSON SCREEN
# ══════════════════════════════════════════════════════════════════════════════
class AlphabetScreen(tk.Frame):
    CAM_W,CAM_H = 1000,1200; VRM_W,VRM_H = 480,480; BTN_SIZE=44
    STATE_WAITING="waiting"; STATE_FEEDBACK="feedback"; STATE_COMPLETE="complete"

    def __init__(self,root,app,mode,start_at=None):
        super().__init__(root,bg=BG); self.pack(fill="both",expand=True)
        self.app=app; self._mode=mode; self._start_at=start_at
        self._vrm_cache={}; self._ph=placeholder_vrm((self.VRM_W,self.VRM_H))
        self._queue=[]; self._qi=0; self._state=self.STATE_WAITING
        self._hold=0; self._score=0; self._fb_id=None; self._paused=False
        self._build(); build_taskbar(self, app, active="alphabet"); self._init_queue()
        self.cap=cv2.VideoCapture(CAM_INDEX); self.running=True; self._upd()

    def _init_queue(self):
        if self._mode=="single" and self._start_at:
            self._queue=[self._start_at]
        else:
            self._queue=list(class_names)
            if self._mode=="shuffle": random.shuffle(self._queue)
            if self._start_at and self._start_at in self._queue:
                self._queue=self._queue[self._queue.index(self._start_at):]
        self._qi=0; self._score=0; self._load()

    def _load(self):
        self._state=self.STATE_WAITING; self._hold=0
        label=self._queue[self._qi]
        self.vrm_lbl.config(image=self._get_vrm(label))
        self.tgt_var.set(label)
        self._hide_ov()
        self.mode_var.set(f"{'📖 Lesson' if self._mode=='lesson' else '🔀 Shuffle'}  {self._qi+1}/{len(self._queue)}")
        self.st_var.set(f"Sign  →  {label}")

    def _cur(self): return self._queue[self._qi]

    def _on_correct(self,conf):
        self._score+=1; self._state=self.STATE_FEEDBACK
        self._show_ov(f"{int(conf*100)}%  Great Job! 🎉",good=True)
        self._fb_id=self.master.after(1400,self._advance)

    def _on_wrong(self,conf):
        if self._state!=self.STATE_WAITING: return
        self._state=self.STATE_FEEDBACK
        self._show_ov(f"{int(conf*100)}%  Try Again.",good=False)
        self._fb_id=self.master.after(900,self._bw)

    def _bw(self):
        self._state=self.STATE_WAITING; self._hold=0; self._hide_ov()
        self.st_var.set(f"Sign  →  {self._cur()}")

    def _advance(self):
        self._qi+=1
        if self._qi>=len(self._queue): self._done()
        else: self._load()

    def _done(self):
        if self._mode=="single": self._qi=0; self._load(); return
        self._state=self.STATE_COMPLETE
        pct=int(self._score/len(self._queue)*100)
        emoji="🌟 Amazing!" if pct==100 else "👏 Well done!" if pct>=70 else "💪 Keep practising!"
        self._show_ov(f"Round complete!\n{self._score}/{len(self._queue)} ({pct}%)\n{emoji}",
                      good=(pct>=70),big=True)
        self._post_f.place(relx=0.5,rely=0.88,anchor="center")

    def _build(self):
        def le(hdr):
            self.mode_var=tk.StringVar(value="")
            tk.Label(hdr,textvariable=self.mode_var,bg=HEADER_BG,
                     fg=TEXT_MID,font=("Helvetica",11)).pack(side="left",padx=20)
            back_btn(hdr, lambda: (setattr(self,'running',False),self.cap.release(),
                                   self.destroy(),self.app.go_alphabet_menu()))
        build_header(self,le)
        body=tk.Frame(self,bg=BG); body.pack(fill="both",expand=True,padx=16,pady=(12,4))
        lw=tk.Frame(body,bg=BG); lw.pack(side="left",fill="y")
        vf=tk.Frame(lw,bg=PANEL_LEFT,width=self.VRM_W,height=self.VRM_H); vf.pack(); vf.pack_propagate(False)
        self.vrm_lbl=tk.Label(vf,bg=PANEL_LEFT,image=self._ph); self.vrm_lbl.pack(expand=True)
        self.tgt_var=tk.StringVar(value="")
        tk.Label(lw,textvariable=self.tgt_var,bg=BG,fg=TEXT_DARK,font=("Helvetica",28,"bold")).pack(pady=(6,0))
        mid=tk.Frame(body,bg=BG,width=60); mid.pack(side="left",fill="y",padx=8); mid.pack_propagate(False)
        tk.Frame(mid,bg=BG).pack(expand=True)
        for icon,cmd,bg,fg in [("→",self._skip,BTN_BG,TEXT_DARK),("⏸",self._pause,ACCENT,WHITE),
                                ("↺",self._restart,BTN_BG,TEXT_DARK),("🔀",self._swap,BTN_BG,TEXT_DARK)]:
            b=tk.Canvas(mid,width=self.BTN_SIZE,height=self.BTN_SIZE,bg=BG,highlightthickness=0,cursor="hand2")
            r=self.BTN_SIZE//2
            b.create_oval(2,2,self.BTN_SIZE-2,self.BTN_SIZE-2,fill=bg,outline="")
            b.create_text(r,r,text=icon,fill=fg,font=("Helvetica",int(r*0.7),"bold"))
            b.bind("<Button-1>",lambda e,c=cmd:c()); b.pack(pady=5)
        tk.Frame(mid,bg=BG).pack(expand=True)
        right=tk.Frame(body,bg=PANEL_RIGHT,width=self.CAM_W,height=self.CAM_H)
        right.pack(side="left",fill="both",expand=True); right.pack_propagate(False)
        self.cam_lbl=tk.Label(right,bg=PANEL_RIGHT)
        self.cam_lbl.place(x=0,y=0,width=self.CAM_W,height=self.CAM_H)
        self._ov_f=tk.Frame(right,bg="",highlightthickness=0)
        self._ov_l=tk.Label(self._ov_f,text="",bg=GREEN_GOOD,fg=WHITE,font=("Helvetica",22,"bold"),
                            padx=20,pady=10,wraplength=360,justify="center")
        self._ov_l.pack(); self._ov_f.place_forget()
        self._post_f=tk.Frame(right,bg=PANEL_RIGHT)
        for txt,cmd in [("↺ Try Again",self._restart),("🔀 Shuffle",self._swap),("← Back",lambda:(setattr(self,'running',False),self.cap.release(),self.destroy(),self.app.go_alphabet_menu()))]:
            tk.Button(self._post_f,text=txt,font=("Helvetica",12,"bold"),bg=ACCENT,fg=WHITE,
                      relief="flat",padx=14,pady=6,cursor="hand2",command=cmd).pack(side="left",padx=6)
        self._post_f.place_forget()
        bbg=tk.Frame(right,bg="#90aec8",height=10)
        bbg.place(relx=0,rely=1.0,anchor="sw",width=self.CAM_W,y=0)
        self._cbar=tk.Frame(bbg,bg=ACCENT,height=10); self._cbar.place(x=0,y=0,width=0,height=10)
        self.pred_var=tk.StringVar(value=""); self.conf_var=tk.StringVar(value="")
        pov=tk.Frame(right,bg=PANEL_RIGHT); pov.place(relx=0,rely=1.0,anchor="sw",x=6,y=-14)
        tk.Label(pov,textvariable=self.pred_var,font=("Helvetica",42,"bold"),fg=ACCENT,bg=PANEL_RIGHT).pack(side="left")
        tk.Label(pov,textvariable=self.conf_var,font=("Helvetica",12),fg=TEXT_DARK,bg=PANEL_RIGHT).pack(side="left",padx=4,pady=(16,0))
        bar=tk.Frame(self,bg=HEADER_BG,height=32); bar.pack(fill="x",side="bottom"); bar.pack_propagate(False)
        self.st_var=tk.StringVar(value="Starting…")
        self._st_lbl=tk.Label(bar,textvariable=self.st_var,bg=HEADER_BG,fg=TEXT_MID,font=("Helvetica",11))
        self._st_lbl.pack(side="left",padx=16)
        tk.Button(bar,text="Quit",font=("Helvetica",11),bg=ACCENT,fg=WHITE,relief="flat",
                  padx=12,pady=0,cursor="hand2",command=self._quit).pack(side="right",padx=8,pady=4)

    def _get_vrm(self,l):
        if l not in self._vrm_cache: self._vrm_cache[l]=load_vrm_image(l,(self.VRM_W,self.VRM_H)) or self._ph
        return self._vrm_cache[l]
    def _show_ov(self,msg,good=True,big=False):
        self._ov_l.config(text=msg,bg=GREEN_GOOD if good else RED_BAD,font=("Helvetica",26 if big else 22,"bold"))
        self._ov_f.place(relx=0.5,rely=0.42,anchor="center"); self._ov_f.lift()
    def _hide_ov(self): self._ov_f.place_forget(); self._post_f.place_forget()
    def _set_cbar(self,conf,green=False):
        self._cbar.config(bg=GREEN_GOOD if green else ACCENT)
        self._cbar.place(x=0,y=0,width=int(self.CAM_W*conf),height=10)
    def _skip(self):
        if self._fb_id: self.master.after_cancel(self._fb_id)
        self._advance()
    def _pause(self): self._paused=not self._paused
    def _restart(self):
        if self._fb_id: self.master.after_cancel(self._fb_id)
        self._init_queue()
    def _swap(self):
        if self._fb_id: self.master.after_cancel(self._fb_id)
        self._mode="shuffle" if self._mode=="lesson" else "lesson"; self._init_queue()
    def _quit(self): self.running=False; self.cap.release(); hands.close(); self.master.destroy()

    def _upd(self):
        if not self.running: return
        if self._paused or self._state==self.STATE_COMPLETE: self.master.after(80,self._upd); return
        ret,frame=self.cap.read()
        if not ret: self.master.after(120,self._upd); return
        frame=cv2.flip(frame,1); display=frame.copy()
        features,mp_r=extract_landmarks(frame)
        if mp_r.multi_hand_landmarks:
            for hl in mp_r.multi_hand_landmarks:
                mp_drawing.draw_landmarks(display,hl,mp_hands.HAND_CONNECTIONS,
                    mp_drawing.DrawingSpec(color=(255,255,255),thickness=2,circle_radius=3),
                    mp_drawing.DrawingSpec(color=(232,145,58),thickness=2,circle_radius=2))
        if features is not None:
            label,conf=predict(features)
            self.pred_var.set(label); self.conf_var.set(f"{conf*100:.0f}%")
            if self._state==self.STATE_WAITING:
                if label==self._cur() and conf>=CONFIDENCE_THRESHOLD:
                    self._hold+=1; self._set_cbar(conf,green=True)
                    if self._hold>=HOLD_FRAMES: self._on_correct(conf)
                else:
                    if self._hold>0: self._hold=0; self._set_cbar(conf); self._on_wrong(conf)
                    else: self._set_cbar(conf)
        else:
            self.pred_var.set("—"); self.conf_var.set(""); self._set_cbar(0); self._hold=0
        rgb=cv2.cvtColor(display,cv2.COLOR_BGR2RGB)
        w=self.cam_lbl.winfo_width() or self.CAM_W
        h=self.cam_lbl.winfo_height() or self.VRM_H
        pil=Image.fromarray(rgb).resize((w,h),Image.BILINEAR)
        imgtk=ImageTk.PhotoImage(image=pil)
        self.cam_lbl.imgtk=imgtk; self.cam_lbl.configure(image=imgtk)
        self.master.after(15,self._upd)

# ══════════════════════════════════════════════════════════════════════════════
# RECOGNIZER — camera only, no VRM, just detects sign
# ══════════════════════════════════════════════════════════════════════════════
class RecognizerScreen(tk.Frame):
    CAM_W,CAM_H=1000,1200
    def __init__(self,root,app):
        super().__init__(root,bg=BG); self.pack(fill="both",expand=True)
        self.app=app; root.title("SenyaSabi — Recognizer")
        self._build()
        build_taskbar(self, app, active="recognizer")
        self.cap=cv2.VideoCapture(CAM_INDEX); self.running=True; self._upd()

    def _build(self):
        def le(hdr): back_btn(hdr,self._go_back)
        build_header(self,le)
        body=tk.Frame(self,bg=BG); body.pack(fill="both",expand=True)
        self.cam_lbl=tk.Label(body,bg=BG); self.cam_lbl.pack(expand=True)
        # Big letter overlay
        self.pred_var=tk.StringVar(value="—")
        self.conf_var=tk.StringVar(value="")
        ov=tk.Frame(body,bg=BG); ov.place(relx=0.02,rely=0.82)
        tk.Label(ov,textvariable=self.pred_var,font=("Helvetica",96,"bold"),
                 fg=ACCENT,bg=BG).pack(side="left")
        tk.Label(ov,textvariable=self.conf_var,font=("Helvetica",20),
                 fg=TEXT_DARK,bg=BG).pack(side="left",padx=10,pady=(10,0))

    def _go_back(self):
        self.running=False; self.cap.release(); self.destroy(); self.app.go_main()

    def _upd(self):
        if not self.running: return
        ret,frame=self.cap.read()
        if not ret: self.master.after(120,self._upd); return
        frame=cv2.flip(frame,1); display=frame.copy()
        features,mp_r=extract_landmarks(frame)
        if mp_r.multi_hand_landmarks:
            for hl in mp_r.multi_hand_landmarks:
                mp_drawing.draw_landmarks(display,hl,mp_hands.HAND_CONNECTIONS,
                    mp_drawing.DrawingSpec(color=(255,255,255),thickness=2,circle_radius=3),
                    mp_drawing.DrawingSpec(color=(232,145,58),thickness=2,circle_radius=2))
        if features is not None:
            label,conf=predict(features)
            self.pred_var.set(label); self.conf_var.set(f"{conf*100:.0f}%")
        else:
            self.pred_var.set("—"); self.conf_var.set("")
        sw=self.master.winfo_width() or self.CAM_W
        sh=self.master.winfo_height()-60 or self.CAM_H
        rgb=cv2.cvtColor(display,cv2.COLOR_BGR2RGB)
        pil=Image.fromarray(rgb); pil.thumbnail((sw,sh),Image.BILINEAR)
        cv2img=Image.new("RGB",(sw,sh),BG_RGB)
        cv2img.paste(pil,((sw-pil.width)//2,(sh-pil.height)//2))
        imgtk=ImageTk.PhotoImage(image=cv2img)
        self.cam_lbl.imgtk=imgtk; self.cam_lbl.configure(image=imgtk)
        self.master.after(15,self._upd)

# ══════════════════════════════════════════════════════════════════════════════
# APP CONTROLLER
# ══════════════════════════════════════════════════════════════════════════════
class App:
    def __init__(self):
        self.root=tk.Tk()
        self.root.state('zoomed')
        self.root.minsize(1024, 600)
        self._clear(); self._cur=None
        self.go_main()
        self.root.mainloop()

    def _clear(self):
        for w in self.root.winfo_children(): w.destroy()

    def go_main(self):
        self._clear(); MainMenu(self.root,self)

    def go_recognizer(self):
        self._clear(); RecognizerScreen(self.root,self)

    def go_alphabet_menu(self):
        self._clear(); AlphabetMenu(self.root,self)

    def go_lesson(self,mode,start_at=None):
        self._clear(); AlphabetScreen(self.root,self,mode,start_at)

    def go_fingerspelling_menu(self):
        self._clear(); FingerSpellingMenu(self.root,self)

    def go_categories(self,mode="sign"):
        self._clear(); CategoriesScreen(self.root,self,mode)

    def go_words_screen(self,category,mode="sign"):
        self._clear(); WordsScreen(self.root,self,category,mode)

    def go_type_it_menu(self):
        self.go_categories(mode="type")

    def go_sign_it_menu(self):
        self.go_categories(mode="sign")

    def go_word_lesson(self,category,word,mode="sign"):
        self._clear()
        if mode=="shuffle":
            # all words from all categories, random order
            all_words=[(cat,w) for cat,words in LESSONS.items() for w in words]
            random.shuffle(all_words)
            cat,w=all_words[0]
            SignItScreen(self.root,self,cat,w,all_words,0)
        elif mode=="shuffle_cat":
            words=[(category,w) for w in LESSONS[category]]
            random.shuffle(words)
            SignItScreen(self.root,self,words[0][0],words[0][1],words,0)
        elif mode=="type":
            TypeItScreen(self.root,self,category,word)
        else:
            SignItScreen(self.root,self,category,word)

    def go_megashuffle(self):
        self._clear()
        # Mix everything: alphabet letters as single-letter "words" + all lesson words
        all_items=[(None,l) for l in class_names]
        for cat,words in LESSONS.items():
            for w in words: all_items.append((cat,w))
        random.shuffle(all_items)
        cat,item=all_items[0]
        if cat is None:
            # It's a letter — use AlphabetScreen in shuffle mode starting at that letter
            AlphabetScreen(self.root,self,"single",start_at=item)
        else:
            SignItScreen(self.root,self,cat,item,all_items,0)

if __name__=="__main__":
    App()
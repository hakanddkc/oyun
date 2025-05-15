import sqlite3
import tkinter as tk
from tkinter import messagebox
import pygame, sys, random
from PIL import Image, ImageTk

from game import Game       # game.py içindeki Game sınıfımız
import scoretable           # Skor tablosu modülü

# -----------------------------------------------------
# SABİT TANIMLARI
# -----------------------------------------------------
GREY = (50, 50, 50)
YELLOW = (243, 216, 63)
BLACK = (0, 0, 0)
WHITE = (255,255,255)
RED =  (255,0,0)
MIDNIGHTBLUE = (25,25,112)
CRIMSON = (162,0,37)
STEEL_BLUE = (70, 130, 180)


# global kullanıcı bilgileri (geri butonları için)
curr_username = None
curr_user_id  = None

# -----------------------------------------------------
# PENCEREYİ TEMİZLEME YARDIMCI FONKSİYONU
# -----------------------------------------------------
def clear_window():
    for w in root.winfo_children():
        w.destroy()

# -----------------------------------------------------
# VERİTABANI İŞLEMLERİ: User / Level / Coin
# -----------------------------------------------------
def init_user_db():
    conn = sqlite3.connect("game_data.db")
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          username TEXT UNIQUE,
          password TEXT,
          coins INTEGER DEFAULT 500
        )""")
    c.execute("""
        CREATE TABLE IF NOT EXISTS user_levels (
          user_id INTEGER,
          level_number INTEGER,
          is_unlocked INTEGER DEFAULT 0,
          score INTEGER DEFAULT 0,
          PRIMARY KEY(user_id,level_number),
          FOREIGN KEY(user_id) REFERENCES users(id)
        )""")
    conn.commit()
    conn.close()

def register_user_db(username, password):
    conn = sqlite3.connect("game_data.db"); c = conn.cursor()
    c.execute("SELECT id FROM users WHERE username=?", (username,))
    if c.fetchone():
        conn.close(); return False
    c.execute("INSERT INTO users (username,password) VALUES (?,?)", (username,password))
    uid = c.lastrowid
    for lvl in range(1,11):
        c.execute("INSERT INTO user_levels VALUES (?,?,?,?)",
                  (uid, lvl, 1 if lvl==1 else 0, 0))
    conn.commit(); conn.close(); return True

def login_user(username, password):
    conn = sqlite3.connect("game_data.db"); c = conn.cursor()
    c.execute("SELECT id FROM users WHERE username=? AND password=?", (username,password))
    row = c.fetchone(); conn.close()
    return row[0] if row else None

def load_coins_db(user_id):
    conn = sqlite3.connect("game_data.db"); c = conn.cursor()
    c.execute("SELECT coins FROM users WHERE id=?", (user_id,))
    row = c.fetchone(); conn.close()
    return row[0] if row else 0

def save_coins_db(coins, user_id):
    conn = sqlite3.connect("game_data.db"); c = conn.cursor()
    c.execute("UPDATE users SET coins=? WHERE id=?", (coins, user_id))
    conn.commit(); conn.close()

def save_level_score(user_id, level, score):
    conn = sqlite3.connect("game_data.db"); c = conn.cursor()
    c.execute("SELECT score FROM user_levels WHERE user_id=? AND level_number=?", (user_id,level))
    old = c.fetchone()[0]
    if score > old:
        c.execute("UPDATE user_levels SET score=? WHERE user_id=? AND level_number=?", (score,user_id,level))
    conn.commit(); conn.close()

def unlock_next_level(user_id, current_level):
    nl = current_level + 1
    if nl <= 10:
        conn = sqlite3.connect("game_data.db"); c = conn.cursor()
        c.execute("UPDATE user_levels SET is_unlocked=1 WHERE user_id=? AND level_number=?", (user_id,nl))
        conn.commit(); conn.close()
        messagebox.showinfo("Level Açıldı", f"{nl}. seviye açıldı!")

# -----------------------------------------------------
# VERİTABANI İŞLEMLERİ: Market / Ships
# -----------------------------------------------------
def init_ships_and_user_ships_db():
    conn = sqlite3.connect("game_data.db"); c = conn.cursor()
    c.execute("""
      CREATE TABLE IF NOT EXISTS ships (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        level INTEGER, price INTEGER, image_path TEXT
      )""")
    c.execute("""
      CREATE TABLE IF NOT EXISTS user_ships (
        user_id INTEGER, ship_id INTEGER,
        is_owned INTEGER DEFAULT 0, is_equipped INTEGER DEFAULT 0,
        PRIMARY KEY(user_id,ship_id),
        FOREIGN KEY(ship_id) REFERENCES ships(id)
      )""")
    c.execute("SELECT COUNT(*) FROM ships")
    if c.fetchone()[0] == 0:
        sample = []
        for lvl in (1,2,3):
            for color in ("blue","darkgrey","green","greyblue","seagreen"):
                sample.append((lvl, lvl*100, f"Graphics/{color}_{lvl}.png"))
        c.executemany("INSERT INTO ships (level,price,image_path) VALUES (?,?,?)", sample)
    conn.commit(); conn.close()

def load_ships_from_db():
    conn = sqlite3.connect("game_data.db"); c = conn.cursor()
    c.execute("SELECT id,level,price,image_path FROM ships ORDER BY level")
    rows = c.fetchall(); conn.close(); return rows

def check_user_ownership_and_equip(user_id, ship_id):
    conn = sqlite3.connect("game_data.db"); c = conn.cursor()
    c.execute("SELECT is_owned,is_equipped FROM user_ships WHERE user_id=? AND ship_id=?", (user_id,ship_id))
    row = c.fetchone(); conn.close(); return row

def set_user_ownership(user_id, ship_id):
    conn = sqlite3.connect("game_data.db"); c = conn.cursor()
    c.execute("""
      INSERT OR REPLACE INTO user_ships
      (user_id,ship_id,is_owned,is_equipped)
      VALUES (?,?,
        1,
        COALESCE((SELECT is_equipped FROM user_ships WHERE user_id=? AND ship_id=?),0)
      )""", (user_id,ship_id,user_id,ship_id))
    conn.commit(); conn.close()

def equip_gemi(user_id, ship_id):
    conn = sqlite3.connect("game_data.db"); c = conn.cursor()
    c.execute("UPDATE user_ships SET is_equipped=0 WHERE user_id=?", (user_id,))
    c.execute("UPDATE user_ships SET is_equipped=1 WHERE user_id=? AND ship_id=?", (user_id,ship_id))
    conn.commit(); conn.close()

def get_equipped_ship_path(user_id):
    conn = sqlite3.connect("game_data.db"); c = conn.cursor()
    c.execute("SELECT ship_id FROM user_ships WHERE user_id=? AND is_equipped=1", (user_id,))
    row = c.fetchone()
    if not row: conn.close(); return None
    c.execute("SELECT image_path FROM ships WHERE id=?", (row[0],))
    r2 = c.fetchone(); conn.close()
    return r2[0] if r2 else None

# -----------------------------------------------------
# MUTE BUTTON FONKSİYONU
# -----------------------------------------------------
def create_mute_button(screen, game):
    """Ekranın sağ üstüne mute/unmute ikonu koyar ve tıklamayı kontrol eder."""
    mute_button_rect = pygame.Rect(screen.get_width() - 300, 25, 50, 50)
    icon_path = "Graphics/volume-up.png" if not game.muted else "Graphics/volume-mute.png"
    speaker_icon = pygame.image.load(icon_path)
    speaker_icon = pygame.transform.scale(speaker_icon, (30, 30))
    screen.blit(speaker_icon, mute_button_rect)
    if pygame.mouse.get_pressed()[0] and mute_button_rect.collidepoint(pygame.mouse.get_pos()):
        game.toggle_music()

# -----------------------------------------------------
# EKRANLAR
# -----------------------------------------------------
def show_login_window():
    clear_window()

    # ——— Arka plan resmini yükle ve yerleştir ———
    bg_image = ImageTk.PhotoImage(
        Image.open("Graphics/anasayfa.png").resize((700, 500), Image.LANCZOS)
    )
    bg_label = tk.Label(root, image=bg_image)
    bg_label.image = bg_image
    bg_label.place(x=0, y=0, relwidth=1, relheight=1)
    # ————————————————————————————————

    root.title("GirişYap")
    root.geometry("700x500")

    # ——— Stil Ayarları ———
    TITLE_FONT = ("Constantia", 26, "bold")
    LABEL_FONT = ("Cambria", 14)
    ENTRY_FONT = ("Cambria", 12)
    BUTTON_FONT = ("Cambria", 12, "bold")

    TITLE_BG = "#0f152a"
    TITLE_FG = "#FFD700"

    LABEL_BG = "#0f152a"
    LABEL_FG = "#FFD700"

    ENTRY_BG = "#FFF8DC"
    ENTRY_FG = "#0f152a"

    BUTTON_BG = "#FFD700"
    BUTTON_FG = "#0f152a"

    BUTTON_WIDTH = 13
    BUTTON_HEIGHT = 1

    PADDING = (5, 5)
    # —————————————————————

    # ——— Sayfa Başlığı ———
    tk.Label(
        root,
        text="Log in",
        font=TITLE_FONT,
        fg=TITLE_FG,
        bg=TITLE_BG,
        padx=10,
        pady=5
    ).pack(pady=(30, 20))
    # ——————————————————

    # ——— Kullanıcı Adı ———
    tk.Label(
        root,
        text="User name:",
        font=LABEL_FONT,
        fg=LABEL_FG,
        bg=LABEL_BG
    ).pack(pady=PADDING)

    e_user = tk.Entry(
        root,
        font=ENTRY_FONT,
        bg=ENTRY_BG,
        fg=ENTRY_FG,
        width=30
    )
    e_user.pack(pady=(5, 15))

    # ——— Şifre ———
    tk.Label(
        root,
        text="Password:",
        font=LABEL_FONT,
        fg=LABEL_FG,
        bg=LABEL_BG
    ).pack(pady=PADDING)

    e_pass = tk.Entry(
        root,
        font=ENTRY_FONT,
        bg=ENTRY_BG,
        fg=ENTRY_FG,
        show="*",
        width=30
    )
    e_pass.pack(pady=(5, 20))

    # ——— Giriş İşlevi ———
    def attempt():
        global curr_username, curr_user_id
        u, p = e_user.get().strip(), e_pass.get().strip()
        uid = login_user(u, p)
        if uid:
            curr_username, curr_user_id = u, uid
            messagebox.showinfo("Successful", f"Welcome, {u}!")
            show_main_menu_welcome()
        else:
            messagebox.showerror("Error", "The wrong username or password!")

    # ——— Butonlar ———
    tk.Button(
        root,
        text="Log in",
        command=attempt,
        font=BUTTON_FONT,
        bg=BUTTON_BG,
        fg=BUTTON_FG,
        width=BUTTON_WIDTH,
        height=BUTTON_HEIGHT
    ).pack(pady=(5, 10))

    tk.Button(
        root,
        text="Sign up",
        command=show_register_window,
        font=BUTTON_FONT,
        bg=BUTTON_BG,
        fg=BUTTON_FG,
        width=BUTTON_WIDTH,
        height=BUTTON_HEIGHT
    ).pack(pady=(5, 10))

    # ——— Back (Geri) Butonu ———
    tk.Button(
        root,
        text="Back",
        command=main,
        font=BUTTON_FONT,
        bg=BUTTON_BG,
        fg=BUTTON_FG,
        width=BUTTON_WIDTH,
        height=BUTTON_HEIGHT
    ).pack(pady=(5, 15))

def show_register_window():
    clear_window()

    # ——— Arka plan resmini yükle ve yerleştir ———
    bg_image = ImageTk.PhotoImage(
        Image.open("Graphics/anasayfa.png").resize((700, 500), Image.LANCZOS)
    )
    bg_label = tk.Label(root, image=bg_image)
    bg_label.image = bg_image
    bg_label.place(x=0, y=0, relwidth=1, relheight=1)
    # ————————————————————————————————

    root.title("Kayıt Ol")
    root.geometry("700x500")

    # ——— Stil Ayarları ———
    TITLE_FONT = ("Constantia", 26, "bold")
    LABEL_FONT = ("Cambria", 14)
    ENTRY_FONT = ("Cambria", 12)
    BUTTON_FONT = ("Cambria", 12, "bold")

    TITLE_BG = "#0f152a"
    TITLE_FG = "#FFD700"

    LABEL_BG = "#0f152a"
    LABEL_FG = "#FFD700"

    ENTRY_BG = "#FFF8DC"
    ENTRY_FG = "#0f152a"

    BUTTON_BG = "#FFD700"
    BUTTON_FG = "#0f152a"

    BUTTON_WIDTH = 13
    BUTTON_HEIGHT = 1

    PADDING = (5, 5)
    # —————————————————————

    # ——— Sayfa Başlığı ———
    tk.Label(
        root,
        text="Sign up",
        font=TITLE_FONT,
        fg=TITLE_FG,
        bg=TITLE_BG,
        padx=10,
        pady=5
    ).pack(pady=(30, 20))
    # ——————————————————

    # ——— Kullanıcı Adı ———
    tk.Label(root, text="User name:", font=LABEL_FONT, fg=LABEL_FG, bg=LABEL_BG).pack(pady=PADDING)
    e_user = tk.Entry(root, font=ENTRY_FONT, bg=ENTRY_BG, fg=ENTRY_FG, width=30)
    e_user.pack(pady=(10, 5))

    # ——— Şifre ———
    tk.Label(root, text="Password:", font=LABEL_FONT, fg=LABEL_FG, bg=LABEL_BG).pack(pady=PADDING)
    e_pass = tk.Entry(root, font=ENTRY_FONT, bg=ENTRY_BG, fg=ENTRY_FG, show="*", width=30)
    e_pass.pack(pady=(5, 5))

    # ——— Şifre (Tekrar) ———
    tk.Label(root, text="Password again:", font=LABEL_FONT, fg=LABEL_FG, bg=LABEL_BG).pack(pady=PADDING)
    e_conf = tk.Entry(root, font=ENTRY_FONT, bg=ENTRY_BG, fg=ENTRY_FG, show="*", width=30)
    e_conf.pack(pady=(5, 5))

    # ——— Buton İşlevi ———
    def attempt():
        u, p, c = e_user.get().strip(), e_pass.get().strip(), e_conf.get().strip()
        if p != c:
            messagebox.showerror("Error", "Password does not match")
            return
        if register_user_db(u, p):
            messagebox.showinfo("Successful", "Registration successful")
            show_login_window()
        else:
            messagebox.showerror("Error", "User already exists")

    # ——— Butonlar ———
    tk.Button(
        root,
        text="Sign up",
        command=attempt,
        font=BUTTON_FONT,
        bg=BUTTON_BG,
        fg=BUTTON_FG,
        width=BUTTON_WIDTH,
        height=BUTTON_HEIGHT
    ).pack(pady=(15, 15))

    tk.Button(
        root,
        text="Back",
        command=main,
        font=BUTTON_FONT,
        bg=BUTTON_BG,
        fg=BUTTON_FG,
        width=BUTTON_WIDTH,
        height=BUTTON_HEIGHT
    ).pack(pady=(5, 15))



def show_main_menu_welcome():
    clear_window()

    # ——— Menü arka plan/görseli ———
    menu_bg = ImageTk.PhotoImage(
        Image.open("Graphics/anamenuu.png").resize((700, 500), Image.LANCZOS)
    )
    menu_bg_label = tk.Label(root, image=menu_bg)
    menu_bg_label.image = menu_bg
    menu_bg_label.place(x=0, y=0, relwidth=1, relheight=1)
    # ——————————————————————————————

    root.title("AnaMenü")
    root.geometry("700x500")
    root.configure(bg="black")

    coins = load_coins_db(curr_user_id)

    # Welcome Label
    lbl_welcome = tk.Label(
        root,
        text=f"Welcome, {curr_username}!",
        fg="midnightblue",
        font=("Constantia", 18, "bold"),
        bg="yellow"
    )
    lbl_welcome.pack(pady=(25, 10))  # İlk padding üst, ikinci alt

    # Coins Label
    lbl_coins = tk.Label(
        root,
        text=f"Coins: {coins}",
        fg="midnightblue",
        font=("Cambria", 14, "bold"),
        bg="yellow"
    )
    lbl_coins.pack(pady=(5, 50))

    def refresh():
        # Welcome Label'ı güncelle
        lbl_welcome.config(text=f"Welcome, {curr_username}!")

        # Coins Label'ı güncelle
        lbl_coins.config(text=f"Coins: {load_coins_db(curr_user_id)}")

    btns = [
        ("Play", show_level_selection),
        ("Store", show_market),
        ("Inventory", show_profile),
        ("Scoreboard", show_scoreboard),
        ("Refresh", refresh),
        ("Exit", root.destroy),
    ]

    for (t, cmd) in btns:
        tk.Button(
            root,
            text=t,
            command=cmd,
            bg="yellow",
            fg="midnightblue",  # Yazı rengi
            font=("Cambria", 12, "bold"),  # Font ayarı
            width=15
        ).pack(pady=5)


def show_level_selection():
    clear_window()

    # ——— Arka plan resmini yükle ve yerleştir ———
    bg_image = ImageTk.PhotoImage(
        Image.open("Graphics/anamenuu.png").resize((700, 500), Image.LANCZOS)
    )
    bg_label = tk.Label(root, image=bg_image)
    bg_label.image = bg_image
    bg_label.place(x=0, y=0, relwidth=1, relheight=1)
    # ————————————————————————————————

    root.title("SeviyeSeç")
    root.geometry("700x500")

    # ——— Sayfa Başlığı ———
    tk.Label(
        root,
        text="Select level",
        font=("Constantia", 24, "bold"),
        fg="yellow",
        bg="black"
    ).pack(pady=(20, 15))
    # ——————————————————

    frame = tk.Frame(root, bg="black")
    frame.pack()

    conn = sqlite3.connect("game_data.db")
    c = conn.cursor()
    c.execute("SELECT level_number, is_unlocked FROM user_levels WHERE user_id=?", (curr_user_id,))
    data = c.fetchall()
    conn.close()
    unlocked = {lvl: unlocked for lvl, unlocked in data}

    for lvl in range(1, 11):
        state = "normal" if unlocked.get(lvl) else "disabled"
        bgcol = "yellow" if unlocked.get(lvl) else "darkgray"
        cmd = (lambda l=lvl: start_game(l)) if unlocked.get(lvl) else None

        btn = tk.Button(
            frame,
            text=f"Level {lvl}",
            state=state,
            bg=bgcol,
            width=12,
            command=cmd
        )
        btn.grid(row=(lvl-1)//2, column=(lvl-1)%2, padx=10, pady=10)

    tk.Button(
        root,
        text="Back",
        command=show_main_menu_welcome,
        bg="yellow",
        font=("Constantia", 10, "bold"),
        width=20
    ).pack(pady=10)

def draw_message_box(screen, message, submessage=None):
    width, height = screen.get_size()
    overlay = pygame.Surface((width, height), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 150))  # yarı saydam siyah
    screen.blit(overlay, (0, 0))

    box_w, box_h = width * 0.6, height * 0.3
    box_x, box_y = (width - box_w) / 2, (height - box_h) / 2
    pygame.draw.rect(screen, YELLOW, (box_x, box_y, box_w, box_h), border_radius=10)
    inner = pygame.Rect(box_x + 5, box_y + 5, box_w - 10, box_h - 10)
    pygame.draw.rect(screen, BLACK, inner, border_radius=8)

    font_big = pygame.font.Font("Font/monogram.ttf", 48)
    txt = font_big.render(message, True, YELLOW)
    screen.blit(txt, txt.get_rect(center=(width/2, box_y + box_h*0.35)))

    if submessage:
        font_small = pygame.font.Font("Font/monogram.ttf", 24)
        sub = font_small.render(submessage, True, YELLOW)
        screen.blit(sub, sub.get_rect(center=(width/2, box_y + box_h*0.65)))


# 1. Add this helper function near your other DB functions:
def load_global_high_score(level):
    """Returns the highest score any user has achieved on this level."""
    conn = sqlite3.connect("game_data.db")
    c = conn.cursor()
    c.execute(
        "SELECT MAX(score) FROM user_levels WHERE level_number=?",
        (level,)
    )
    row = c.fetchone()
    conn.close()
    return row[0] or 0


def load_global_high_score(level):
    """Returns the highest score any user has achieved on this level."""
    conn = sqlite3.connect("game_data.db")
    c = conn.cursor()
    c.execute(
        "SELECT MAX(score) FROM user_levels WHERE level_number=?",
        (level,)
    )
    row = c.fetchone()
    conn.close()
    return row[0] or 0


def start_game(selected_level):
    root.withdraw()
    pygame.init()
    SW, SH, OF = 750, 700, 50
    screen = pygame.display.set_mode((SW + OF, SH + 2 * OF))
    pygame.display.set_caption("Python Space Invaders")
    clock = pygame.time.Clock()
    font = pygame.font.Font("Font/monogram.ttf", 40)

    # load and scale one static background for all levels
    bg = pygame.image.load("Graphics/space_background.png").convert()
    bg = pygame.transform.scale(bg, (SW + OF, SH + 2 * OF))

    # Timed events
    SHOOT, MYST, POW = pygame.USEREVENT, pygame.USEREVENT + 1, pygame.USEREVENT + 2
    pygame.time.set_timer(SHOOT, 300)
    pygame.time.set_timer(MYST, random.randint(4000, 8000))
    pygame.time.set_timer(POW, random.randint(8000, 12000))

    path = get_equipped_ship_path(curr_user_id) or "Graphics/default_spaceship.png"
    game = Game(SW, SH, OF, selected_level, spaceship_image_path=path)
    game.coins = load_coins_db(curr_user_id)

    # Track the global high score for this level
    high_score = load_global_high_score(selected_level)

    paused = False
    exit_to_menu = False
    victory = False
    pause_rect = pygame.Rect((SW + OF) // 2 - 70, 10, 140, 50)

    while True:
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                save_coins_db(game.coins, curr_user_id)
                pygame.quit()
                sys.exit()

            # Toggle pause
            if e.type == pygame.KEYDOWN and e.key == pygame.K_p:
                paused = not paused
            # Exit to menu when paused and ESC pressed
            if game.run and paused and e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
                exit_to_menu = True
            # Pause/resume via click
            if game.run and e.type == pygame.MOUSEBUTTONDOWN and pause_rect.collidepoint(e.pos):
                paused = not paused

            # Game actions when not paused
            if game.run and not paused:
                if e.type == SHOOT:
                    game.alien_shoot_laser()
                if e.type == MYST:
                    game.create_mystery_ship()
                    pygame.time.set_timer(MYST, random.randint(4000, 8000))
                if e.type == POW:
                    game.create_powerup()

            # Clicks when game over
            if not game.run and e.type == pygame.MOUSEBUTTONDOWN:
                mp = e.pos
                b1 = pygame.Rect(SW // 2 - 100, SH // 2 + 20, 200, 40)
                b2 = pygame.Rect(SW // 2 - 100, SH // 2 + 80, 200, 40)

                if b1.collidepoint(mp):
                    if victory:
                        # Level atla, kaydet ve yeni fonksiyonu başlat
                        unlock_next_level(curr_user_id, game.level)
                        save_level_score(curr_user_id, selected_level, game.score)
                        save_coins_db(game.coins, curr_user_id)
                        pygame.quit()
                        return start_game(selected_level + 1)
                    else:
                        # Aynı seviyeyi yeniden oyna
                        game.reset()

                if b2.collidepoint(mp):
                    exit_to_menu = True

        if exit_to_menu:
            break

        # Update game logic
        if not paused and game.run:
            game.spaceship_group.update()
            game.move_aliens()
            game.alien_lasers_group.update()
            game.mystery_ship_group.update()
            game.powerups_group.update()
            game.update_powerup_status()
            game.check_for_collisions()
            if game.lives <= 0:
                game.run = False
                victory = False
            if not game.aliens_group:
                game.run = False
                victory = True

        # Draw background
        screen.blit(bg, (0, 0))
        pygame.draw.rect(screen, YELLOW, (10, 10, 780, 780), 2)
        pygame.draw.line(screen, YELLOW, (25, 730), (775, 730), 3)

        if game.run:
            # Current score (top-left)
            score_surf = font.render(f"SCORE: {game.score}", True, YELLOW)
            screen.blit(score_surf, (20, 20))

            # User coins (below score)
            coin_surf = font.render(f"COINS: {game.coins}", True, YELLOW)
            screen.blit(coin_surf, (20, 20 + score_surf.get_height() + 10))

            # Global high score (top-right)
            high_surf = font.render(f"HIGH: {high_score}", True, YELLOW)
            hs_x = screen.get_width() - high_surf.get_width() - 60
            screen.blit(high_surf, (hs_x, 20))

            # Pause button
            pygame.draw.rect(screen, YELLOW, pause_rect)
            lbl = "PAUSE" if not paused else "RESUME"
            screen.blit(font.render(lbl, True, BLACK),
                        (pause_rect.x + 10, pause_rect.y + 10))
            create_mute_button(screen, game)

            # Draw sprites
            game.spaceship_group.draw(screen)
            game.spaceship_group.sprite.lasers_group.draw(screen)
            for obs in game.obstacles:
                obs.blocks_group.draw(screen)
            game.aliens_group.draw(screen)
            game.alien_lasers_group.draw(screen)
            game.mystery_ship_group.draw(screen)
            game.powerups_group.draw(screen)

            # Paused overlay with exit hint
            if paused:
                draw_message_box(screen,
                                 "PAUSED",
                                 "Press P to Resume or ESC to Exit")

        else:
            # End-of-level overlay
            overlay = pygame.Surface((SW + OF, SH + 2 * OF), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180))
            screen.blit(overlay, (0, 0))
            big = pygame.font.Font("Font/monogram.ttf", 60)
            title = "LEVEL COMPLETE!" if victory else "GAME OVER"
            color = (0, 255, 0) if victory else (255, 0, 0)
            msg = big.render(title, True, color)
            screen.blit(msg,
                        (SW // 2 - msg.get_width() // 2, SH // 2 - 60))

            b1 = pygame.Rect(SW // 2 - 100, SH // 2 + 20, 200, 40)
            b2 = pygame.Rect(SW // 2 - 100, SH // 2 + 80, 200, 40)
            pygame.draw.rect(screen, YELLOW, b1)
            pygame.draw.rect(screen, YELLOW, b2)
            sf = pygame.font.Font("Font/monogram.ttf", 40)
            nl = "Next Level" if victory else "Play Again"
            screen.blit(sf.render(nl, True, BLACK), (b1.x + 20, b1.y + 5))
            screen.blit(sf.render("Exit", True, BLACK), (b2.x + 70, b2.y + 5))

        pygame.display.update()
        clock.tick(60)

    # Save and return to menu
    save_level_score(curr_user_id, selected_level, game.score)
    save_coins_db(game.coins, curr_user_id)
    pygame.quit()
    root.deiconify()
    show_main_menu_welcome()

def show_market():
    clear_window()

    # Pencere başlığı / boyutu
    root.title("Market")
    root.geometry("800x600")

    # ——— Tam ekran Canvas ve arka plan resmi ———
    canvas = tk.Canvas(root, width=800, height=600, highlightthickness=0)
    canvas.pack(fill="both", expand=True)

    bg_img = ImageTk.PhotoImage(
        Image.open("Graphics/anamenuu.png").resize((800, 600), Image.LANCZOS)
    )
    canvas.bg_img = bg_img
    canvas.create_image(0, 0, anchor="nw", image=bg_img)
    # ——————————————————————————————————————

    # ——— Başlık ve Geri butonu ———
    canvas.create_text(
        400, 40,
        text="Space Store",
        font=("Constantia", 24, "bold"),
        fill="yellow"
    )
    back_btn = tk.Button(
        root, text="← back",
        bg="yellow", fg="black",
        font=("Constantia", 10, "bold"),
        command=show_main_menu_welcome
    )
    canvas.create_window(10, 10, anchor="nw", window=back_btn)
    # ————————————————————————————

    # ——— Coins göstergesi ———
    coins = load_coins_db(curr_user_id)
    coins_text = canvas.create_text(
        400, 80,
        text=f"Coins :  {coins}",
        font=("Cambria", 14, "bold"),
        fill="yellow"
    )
    # ——————————————————————

    # Veritabanından gemileri oku ve seviyelere göre grupla
    init_ships_and_user_ships_db()
    ships = load_ships_from_db()
    from collections import defaultdict
    by_lvl = defaultdict(list)
    for sid, lvl, price, imgpath in ships:
        by_lvl[lvl].append((sid, price, imgpath))

    # ——— Gemileri çiz ———
    start_y = 120
    x_spacing = 150

    for lvl in sorted(by_lvl):
        # Seviye başlığı
        canvas.create_text(
            400, start_y,
            text=f" {lvl}. Level",
            font=("Cambria", 14, "bold"),
            fill="yellow"
        )
        y = start_y + 20
        x = 60

        for sid, price, imgpath in by_lvl[lvl]:
            # Gemi resmi
            try:
                img = Image.open(imgpath).resize((80, 80), Image.LANCZOS)
            except:
                img = Image.new("RGB", (80, 80), (60, 60, 60))
            photo = ImageTk.PhotoImage(img)
            canvas.ship_images = getattr(canvas, "ship_images", []) + [photo]
            canvas.create_image(x, y, anchor="nw", image=photo)

            # Fiyat etiketi
            canvas.create_rectangle(x, y+85, x+80, y+105, fill="midnightblue", outline="")
            canvas.create_text(
                x+40, y+95,
                text=f"{price} Coin",
                font=("Cambria", 10),
                fill="white"
            )

            # Butonları ekle
            info = check_user_ownership_and_equip(curr_user_id, sid)
            if not info or info[0] == 0:
                btn = tk.Button(
                    root, text="Buy",
                    bg="yellow",
                    command=lambda s=sid, p=price: (
                        buy_gemi(s, p, lambda: canvas.itemconfigure(coins_text, text=f"Coins: {load_coins_db(curr_user_id)}")),
                        show_market()
                    )
                )
            else:
                if info[1] == 1:
                    btn = tk.Button(root, text="Current", bg="yellow", state="disabled")
                else:
                    btn = tk.Button(
                        root, text="Select",
                        bg="yellow",
                        command=lambda s=sid: select_gemi(s)
                    )

            canvas.create_window(x+40, y+125, window=btn)
            x += x_spacing

        start_y += 180
    # ——————————————————


def buy_gemi(ship_id, price, update_ui):
    """
    Satın alma işlemi.
    update_ui: ya bir Label widget’ı, ya da bir callable (örneğin lambda) olabilir.
    """
    coins = load_coins_db(curr_user_id)
    if coins >= price:
        save_coins_db(coins - price, curr_user_id)
        set_user_ownership(curr_user_id, ship_id)
        messagebox.showinfo("Successful", f"Ship purchased, remaining coin: {coins - price}")
        # Eğer bir callable verdiysek onu çağır, değilse Label.config ile text güncelle
        if callable(update_ui):
            update_ui()
        else:
            update_ui.config(text=f"Coins: {coins - price}")
        show_market()   # market ekranını yenile
    else:
        messagebox.showwarning("Insufficient", "Your coin balance is insufficient.")

def select_gemi(ship_id):
    equip_gemi(curr_user_id, ship_id)
    messagebox.showinfo("Selected","The ship was selected")
    show_market()

def show_profile():
    clear_window()
    root.title("profilSayfası")
    root.geometry("700x500")

    # ——— Tam ekran Canvas ve arka plan resmi ———
    canvas = tk.Canvas(root, width=700, height=500, highlightthickness=0)
    canvas.pack(fill="both", expand=True)

    bg_img = ImageTk.PhotoImage(
        Image.open("Graphics/anamenuu.png").resize((700, 500), Image.LANCZOS)
    )
    canvas.bg_img = bg_img
    canvas.create_image(0, 0, anchor="nw", image=bg_img)
    # ——————————————————————————————————————

    # ——— Başlık ———
    canvas.create_text(
        350, 50,
        text="Inventory",
        font=("Constantia", 24, "bold"),
        fill="yellow"
    )
    # ——————————

    # Kullanıcı adını ve coin bilgisini oku
    conn = sqlite3.connect("game_data.db")
    c = conn.cursor()
    c.execute("SELECT username, coins FROM users WHERE id=?", (curr_user_id,))
    u, cns = c.fetchone()
    conn.close()

    # ——— Kullanıcı bilgileri ———
    canvas.create_text(
        350, 100,
        text=f"User :   {u}                         Coins :   {cns}",
        font=("Cambria", 14),
        fill="yellow"
    )
    # ——————————

    # ——— Sahip olunan gemileri veritabanından çek ———
    conn = sqlite3.connect("game_data.db")
    c = conn.cursor()
    c.execute("""
        SELECT s.image_path
        FROM ships s
        JOIN user_ships us ON s.id = us.ship_id
        WHERE us.user_id=? AND us.is_owned=1
    """, (curr_user_id,))
    owned = c.fetchall()
    conn.close()

    # ——— Gemi resimlerini göster ———
    x_start, y_start = 50, 130
    spacing = 100
    canvas.profile_images = []

    for idx, (img_path,) in enumerate(owned):
        try:
            img = Image.open(img_path).resize((80, 80), Image.LANCZOS)
        except:
            img = Image.new("RGB", (80, 80), (80, 80, 80))
        photo = ImageTk.PhotoImage(img)
        canvas.profile_images.append(photo)
        x = x_start + (idx % 6) * spacing
        y = y_start + (idx // 6) * spacing
        canvas.create_image(x, y, anchor="nw", image=photo)

    # ——— Geri butonu ———
    back_btn = tk.Button(
        root,
        text="← Back",
        bg="yellow",
        fg="black",
        font=("Constantia", 10, "bold"),
        command=show_main_menu_welcome
    )
    canvas.create_window(10, 10, anchor="nw", window=back_btn)
    # —————————————————

def show_scoreboard():
    clear_window()
    root.title("SkorTablosu")
    root.geometry("700x500")

    # ——— Tam ekran Canvas ve arka plan resmi ———
    canvas = tk.Canvas(root, width=700, height=500, highlightthickness=0)
    canvas.pack(fill="both", expand=True)

    bg_img = ImageTk.PhotoImage(
        Image.open("Graphics/anamenuu.png").resize((700, 500), Image.LANCZOS)
    )
    canvas.bg_img = bg_img
    canvas.create_image(0, 0, anchor="nw", image=bg_img)
    # ——————————————————————————————————————

    # ——— Başlık ———
    # Arkasına siyah bir kutucuk çizip üzerine sarı başlık yazıyoruz
    #canvas.create_rectangle(150, 20, 550, 70, fill="black", outline="")
    canvas.create_text(
        350, 45,
        text="Scoreboard",
        font=("Constantia", 24, "bold"),
        fill="yellow"
    )
    # ——————————

    # ——— Skor tablosunu yerleştireceğimiz çerçeve ———
    table_frame = tk.Frame(root, bg="black")
    # Canvas üzerinde ortalanmış şekilde pencereye ekliyoruz
    canvas.create_window(350, 280, window=table_frame, width=600, height=360)
    try:
        scoretable.show_scoretable(table_frame)
    except Exception as e:
        messagebox.showerror("Hata", str(e))
    # ———————————————————————————————

    # ——— Geri butonu ———
    back_btn = tk.Button(
        root,
        text="← Back",
        bg="yellow",
        fg="black",
        font=("Constantia", 10, "bold"),
        command=show_main_menu_welcome
    )
    canvas.create_window(10, 10, anchor="nw", window=back_btn)
    # ——————————————————


# -----------------------------------------------------
# UYGULAMA BAŞLANGICI
# -----------------------------------------------------
def main():
    init_user_db()
    clear_window()

    # ——— Arka plan resmini yükle ve yerleştir ———
    bg_image = ImageTk.PhotoImage(
        Image.open("Graphics/anasayfa.png").resize((700, 500), Image.LANCZOS)
    )
    bg_label = tk.Label(root, image=bg_image)
    bg_label.image = bg_image
    bg_label.place(x=0, y=0, relwidth=1, relheight=1)
    # ————————————————————————————————

    root.title("AnaSayfa")
    root.geometry("700x500")

    # ——— Renk ve font ayarları ———
    TITLE_BG = "#0f152a"  # koyu uzay-laciverti
    TITLE_FG = "#FFD700"  # parlak sarı
    BUTTON_BG = "#FFD700" # buton arkaplanı - parlak sarı
    BUTTON_FG = "#0f152a" # buton yazı rengi - koyu lacivert
    FONT_TITLE = ("Constantia", 24, "bold")
    FONT_BUTTON = ("Cambria", 13, "bold")
    PADDING = (10, 15)
    # ————————————————————————————

    # ——— Başlık etiketi ———
    title_lbl = tk.Label(
        root,
        text="Welcome to the Spaceship",
        font=FONT_TITLE,
        fg=TITLE_FG,
        bg=TITLE_BG,
        padx=5,
        pady=5,
    )
    title_lbl.pack(pady=(30, 60))
    # ————————————————————

    # ——— Butonlar ———
    buttons = [
        ("Log in", show_login_window),
        ("Sign up", show_register_window),
        ("Exit", root.destroy),
    ]

    for text, command in buttons:
        tk.Button(
            root,
            text=text,
            command=command,
            bg=BUTTON_BG,
            fg=BUTTON_FG,
            font=FONT_BUTTON,
            width=18
        ).pack(pady=PADDING)


if __name__=="__main__":
    root = tk.Tk()
    main()
    root.mainloop()

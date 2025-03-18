import sqlite3
import tkinter as tk
from tkinter import messagebox
import pygame, sys, random
from game import Game  # game.py içindeki Game sınıfınız

# Renk tanımları
GREY = (50, 50, 50)
YELLOW = (243, 216, 63)
BLACK = (0, 0, 0)

# -----------------------------------------------------
# VERİTABANI İŞLEMLERİ
# -----------------------------------------------------
def init_user_db():
    conn = sqlite3.connect("game_data.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT,
            coins INTEGER DEFAULT 500
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_levels (
            user_id INTEGER,
            level_number INTEGER,
            is_unlocked INTEGER DEFAULT 0,
            PRIMARY KEY (user_id, level_number),
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)
    conn.commit()
    conn.close()

def register_user_db(username, password):
    conn = sqlite3.connect("game_data.db")
    cursor = conn.cursor()
    # Aynı kullanıcı var mı kontrol et
    cursor.execute("SELECT id FROM users WHERE username=?", (username,))
    if cursor.fetchone() is not None:
        conn.close()
        return False  # Kullanıcı zaten mevcut.
    cursor.execute("INSERT INTO users (username, password, coins) VALUES (?, ?, ?)", (username, password, 500))
    user_id = cursor.lastrowid
    for lvl in range(1, 11):
        is_unlocked = 1 if lvl == 1 else 0
        cursor.execute("INSERT INTO user_levels (user_id, level_number, is_unlocked) VALUES (?, ?, ?)",
                       (user_id, lvl, is_unlocked))
    conn.commit()
    conn.close()
    return True

def login_user(username, password):
    conn = sqlite3.connect("game_data.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users WHERE username=? AND password=?", (username, password))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result is not None else None

def unlock_next_level(user_id, current_level):
    next_level = current_level + 1
    if next_level <= 10:
        conn = sqlite3.connect("game_data.db")
        cursor = conn.cursor()
        cursor.execute("UPDATE user_levels SET is_unlocked=1 WHERE user_id=? AND level_number=?", (user_id, next_level))
        conn.commit()
        conn.close()
        messagebox.showinfo("Level Açıldı", f"{next_level}. seviye açıldı!")

def get_levels_for_user(user_id):
    conn = sqlite3.connect("game_data.db")
    cursor = conn.cursor()
    cursor.execute("SELECT level_number, is_unlocked FROM user_levels WHERE user_id=?", (user_id,))
    levels = cursor.fetchall()
    conn.close()
    return levels

def load_coins_db(user_id):
    conn = sqlite3.connect("game_data.db")
    cursor = conn.cursor()
    cursor.execute("SELECT coins FROM users WHERE id=?", (user_id,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result is not None else 0

def save_coins_db(coins, user_id):
    conn = sqlite3.connect("game_data.db")
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET coins=? WHERE id=?", (coins, user_id))
    conn.commit()
    conn.close()

# -----------------------------------------------------
# YENİ EKLENDİ: SEÇİLEN GEMİNİN YOLUNU BULMA
# -----------------------------------------------------
def get_equipped_ship_path(user_id):
    """
    user_ships tablosunda is_equipped=1 olan geminin ships tablosundaki
    image_path değerini döndürür. Yoksa None.
    """
    conn = sqlite3.connect("game_data.db")
    cursor = conn.cursor()

    # user_ships içinde is_equipped=1 olan gemi hangisi?
    cursor.execute("""
        SELECT ship_id FROM user_ships
        WHERE user_id=? AND is_equipped=1
    """, (user_id,))
    row = cursor.fetchone()
    if row is None:
        conn.close()
        return None  # Seçilen gemi yok

    ship_id = row[0]
    # ships tablosundan image_path'i çek
    cursor.execute("""
        SELECT image_path FROM ships
        WHERE id=?
    """, (ship_id,))
    row2 = cursor.fetchone()
    conn.close()

    if row2 is None:
        return None
    return row2[0]  # image_path

# -----------------------------------------------------
# GİRİŞ / KAYIT EKRANLARI
# -----------------------------------------------------
def show_login_window(master):
    login_win = tk.Toplevel(master)
    login_win.title("Giriş Yap")
    login_win.geometry("700x500")
    login_win.configure(bg="black")

    tk.Label(login_win, text="Kullanıcı Adı:", fg="yellow", bg="black", font=("Arial", 12)).pack(pady=5)
    username_entry = tk.Entry(login_win, font=("Arial", 12))
    username_entry.pack(pady=5)

    tk.Label(login_win, text="Şifre:", fg="yellow", bg="black", font=("Arial", 12)).pack(pady=5)
    password_entry = tk.Entry(login_win, show="*", font=("Arial", 12))
    password_entry.pack(pady=5)

    def attempt_login():
        username = username_entry.get().strip()
        password = password_entry.get().strip()
        user_id = login_user(username, password)
        if user_id is not None:
            messagebox.showinfo("Başarılı", f"Hoşgeldiniz, {username}!")
            login_win.destroy()
            show_main_menu_welcome(username, user_id)
        else:
            messagebox.showerror("Hata", "Kullanıcı adı veya şifre yanlış!")

    login_btn = tk.Button(login_win, text="Giriş Yap", font=("Arial", 12),
                          fg="black", bg="yellow", command=attempt_login)
    login_btn.pack(pady=10)

    exit_btn = tk.Button(login_win, text="Çıkış", font=("Arial", 12),
                         fg="black", bg="yellow", command=login_win.destroy)
    exit_btn.pack(pady=10)

def show_register_window(master):
    reg_win = tk.Toplevel(master)
    reg_win.title("Kayıt Ol")
    reg_win.geometry("700x500")
    reg_win.configure(bg="black")

    tk.Label(reg_win, text="Kullanıcı Adı:", fg="yellow", bg="black", font=("Arial", 12)).pack(pady=5)
    username_entry = tk.Entry(reg_win, font=("Arial", 12))
    username_entry.pack(pady=5)

    tk.Label(reg_win, text="Şifre:", fg="yellow", bg="black", font=("Arial", 12)).pack(pady=5)
    password_entry = tk.Entry(reg_win, show="*", font=("Arial", 12))
    password_entry.pack(pady=5)

    tk.Label(reg_win, text="Şifre Tekrar:", fg="yellow", bg="black", font=("Arial", 12)).pack(pady=5)
    confirm_entry = tk.Entry(reg_win, show="*", font=("Arial", 12))
    confirm_entry.pack(pady=5)

    def attempt_register():
        username = username_entry.get().strip()
        password = password_entry.get().strip()
        confirm = confirm_entry.get().strip()
        if password != confirm:
            messagebox.showerror("Hata", "Şifreler eşleşmiyor!")
            return
        if register_user_db(username, password):
            messagebox.showinfo("Başarılı", "Kayıt başarılı, şimdi giriş yapabilirsiniz.")
            reg_win.destroy()
        else:
            messagebox.showerror("Hata", "Kullanıcı adı zaten mevcut!")

    reg_btn = tk.Button(reg_win, text="Kayıt Ol", font=("Arial", 12),
                        fg="black", bg="yellow", command=attempt_register)
    reg_btn.pack(pady=10)

    exit_btn = tk.Button(reg_win, text="Çıkış", font=("Arial", 12),
                         fg="black", bg="yellow", command=reg_win.destroy)
    exit_btn.pack(pady=10)

# Veritabanına kayıt fonksiyonuydu (isim çakışması sebebiyle rename edildi).
def register_user(username, password):
    try:
        conn = sqlite3.connect("game_data.db")
        cursor = conn.cursor()
        cursor.execute("INSERT INTO users (username, password, coins) VALUES (?, ?, ?)", (username, password, 500))
        user_id = cursor.lastrowid
        for lvl in range(1, 11):
            is_unlocked = 1 if lvl == 1 else 0
            cursor.execute("INSERT INTO user_levels (user_id, level_number, is_unlocked) VALUES (?, ?, ?)",
                           (user_id, lvl, is_unlocked))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        return False

# -----------------------------------------------------
# ANA MENÜ (Hoşgeldiniz)
# -----------------------------------------------------
def show_main_menu_welcome(username, user_id):
    root.deiconify()
    root.geometry("700x500")
    for widget in root.winfo_children():
        widget.destroy()
    root.configure(bg="black")

    coins = load_coins_db(user_id)
    welcome_label = tk.Label(root, text=f"Hoşgeldiniz, {username}!\nCoins: {coins}",
                             font=("Arial", 18, "bold"), fg="yellow", bg="black")
    welcome_label.pack(pady=20)

    def refresh_coins():
        new_coins = load_coins_db(user_id)
        welcome_label.config(text=f"Hoşgeldiniz, {username}!\nCoins: {new_coins}")

    start_game_btn = tk.Button(root, text="Oyuna Başla", font=("Arial", 14), fg="black", bg="yellow",
                               command=lambda: show_level_selection(user_id, username))
    start_game_btn.pack(pady=10)

    market_btn = tk.Button(root, text="Market", font=("Arial", 14), fg="black", bg="yellow",
                           command=lambda: show_market(root, user_id))
    market_btn.pack(pady=10)

    profile_btn = tk.Button(root, text="Profil", font=("Arial", 14), fg="black", bg="yellow",
                            command=show_profile)
    profile_btn.pack(pady=10)

    scoreboard_btn = tk.Button(root, text="Skor Tablosu", font=("Arial", 14), fg="black", bg="yellow",
                               command=show_scoreboard)
    scoreboard_btn.pack(pady=10)

    refresh_btn = tk.Button(root, text="Yenile", font=("Arial", 14), fg="black", bg="yellow",
                            command=refresh_coins)
    refresh_btn.pack(pady=10)

    exit_btn = tk.Button(root, text="Çıkış", font=("Arial", 14), fg="black", bg="yellow",
                         command=root.destroy)
    exit_btn.pack(pady=10)

def show_profile():
    profile_win = tk.Toplevel(root)
    profile_win.title("Profil")
    profile_win.geometry("700x500")
    profile_win.configure(bg="black")
    label = tk.Label(profile_win, text="Profil (Placeholder)", font=("Arial", 16), fg="yellow", bg="black")
    label.pack(pady=20)

def show_scoreboard():
    scoreboard_win = tk.Toplevel(root)
    scoreboard_win.title("Skor Tablosu")
    scoreboard_win.geometry("700x500")
    scoreboard_win.configure(bg="black")
    label = tk.Label(scoreboard_win, text="Skor Tablosu (Placeholder)", font=("Arial", 16), fg="yellow", bg="black")
    label.pack(pady=20)

def show_market(master, user_id):
    try:
        import market
        market.show_market(master, user_id)
    except ImportError as e:
        print("Market modülü bulunamadı:", e)
        market_win = tk.Toplevel(master)
        market_win.title("Market")
        market_win.geometry("700x500")
        market_win.configure(bg="black")
        label = tk.Label(market_win, text="Market (Placeholder)", font=("Arial", 16), fg="yellow", bg="black")
        label.pack(pady=20)

# -----------------------------------------------------
# SEVİYE SEÇİMİ
# -----------------------------------------------------
def show_level_selection(user_id, username):
    level_win = tk.Toplevel(root)
    level_win.title("Seviye Seç")
    level_win.geometry("700x500")
    level_win.configure(bg="black")

    title_label = tk.Label(level_win, text="LEVEL SEÇ", font=("Arial", 18, "bold"), fg="yellow", bg="black")
    title_label.grid(row=0, column=0, columnspan=2, pady=20)

    level_frame = tk.Frame(level_win, bg="black")
    level_frame.grid(row=1, column=0, columnspan=2)

    conn = sqlite3.connect("game_data.db")
    cursor = conn.cursor()
    cursor.execute("SELECT level_number, is_unlocked FROM user_levels WHERE user_id=?", (user_id,))
    levels_data = cursor.fetchall()
    conn.close()

    level_dict = {lvl: unlocked for (lvl, unlocked) in levels_data}

    row, col = 0, 0
    for level in range(1, 11):
        is_unlocked = level_dict.get(level, 0)
        if is_unlocked == 1:
            btn = tk.Button(level_frame, text=f"Level {level}", font=("Arial", 14),
                            fg="black", bg="yellow",
                            command=lambda lvl=level: start_game(lvl, level_win, user_id, username))
        else:
            btn = tk.Button(level_frame, text=f"Level {level} (Locked)", font=("Arial", 14),
                            fg="gray", bg="darkgray", state=tk.DISABLED)
        btn.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")
        col += 1
        if col > 1:
            col = 0
            row += 1

# -----------------------------------------------------
# OYUN BAŞLATMA
# -----------------------------------------------------
def start_game(selected_level, win, user_id, username):
    if win != root:
        win.destroy()
    else:
        root.withdraw()
    pygame.init()

    SCREEN_WIDTH = 750
    SCREEN_HEIGHT = 550
    OFFSET = 50

    font = pygame.font.Font("Font/monogram.ttf", 40)
    score_text_surface = font.render("SCORE", False, YELLOW)
    highscore_text_surface = font.render("HIGH-SCORE", False, YELLOW)

    screen = pygame.display.set_mode((SCREEN_WIDTH + OFFSET, SCREEN_HEIGHT + 2 * OFFSET))
    pygame.display.set_caption("Python Space Invaders")
    clock = pygame.time.Clock()

    # --- YENİ EKLENDİ: Ekipli gemi yolunu al, yoksa varsayılan ata
    equipped_path = get_equipped_ship_path(user_id)
    if equipped_path is None:
        equipped_path = "Graphics/default_spaceship.png"  # Varsayılan gemi resminiz

    # Game sınıfı yapıcısını, spaceship_image_path parametresiyle çağırıyoruz.
    game = Game(SCREEN_WIDTH, SCREEN_HEIGHT, OFFSET, selected_level, spaceship_image_path=equipped_path)

    # Kullanıcının coin bakiyesi
    game.coins = load_coins_db(user_id)

    paused = False
    victory = False
    exit_to_menu = False

    pause_button_width = 140
    pause_button_height = 50
    pause_button_x = (SCREEN_WIDTH + OFFSET) // 2 - (pause_button_width // 2)
    pause_button_y = 10
    pause_button_rect = pygame.Rect(pause_button_x, pause_button_y, pause_button_width, pause_button_height)

    SHOOT_LASER = pygame.USEREVENT
    pygame.time.set_timer(SHOOT_LASER, 300)

    MYSTERYSHIP = pygame.USEREVENT + 1
    pygame.time.set_timer(MYSTERYSHIP, random.randint(4000, 8000))

    POWERUP_EVENT = pygame.USEREVENT + 2
    pygame.time.set_timer(POWERUP_EVENT, random.randint(8000, 12000))

    pause_box_width = 400
    pause_box_height = 150
    pause_box_x = (SCREEN_WIDTH + OFFSET) // 2 - pause_box_width // 2
    pause_box_y = (SCREEN_HEIGHT + 2 * OFFSET) // 2 - pause_box_height // 2

    button_width = 180
    button_height = 40
    button_x = pause_box_x + (pause_box_width - button_width) // 2

    resume_y = pause_box_y + 60
    exit_y = pause_box_y + 110

    resume_rect = pygame.Rect(button_x, resume_y, button_width, button_height)
    exit_rect = pygame.Rect(button_x, exit_y, button_width, button_height)

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                save_coins_db(game.coins, user_id)
                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_p:
                    paused = not paused

            if game.run:
                if event.type == pygame.MOUSEBUTTONDOWN:
                    mouse_pos = pygame.mouse.get_pos()
                    if pause_button_rect.collidepoint(mouse_pos):
                        paused = not paused

                if not paused:
                    if event.type == SHOOT_LASER:
                        game.alien_shoot_laser()
                    if event.type == MYSTERYSHIP:
                        game.create_mystery_ship()
                        pygame.time.set_timer(MYSTERYSHIP, random.randint(4000, 8000))
                    if event.type == POWERUP_EVENT:
                        game.create_powerup()
                else:
                    if event.type == pygame.MOUSEBUTTONDOWN:
                        mouse_pos = pygame.mouse.get_pos()
                        if resume_rect.collidepoint(mouse_pos):
                            paused = False
                        elif exit_rect.collidepoint(mouse_pos):
                            exit_to_menu = True
                            break

            if not game.run:
                if event.type == pygame.MOUSEBUTTONDOWN:
                    mouse_pos = pygame.mouse.get_pos()
                    box_width = 500
                    box_height = 250
                    box_x = (SCREEN_WIDTH + OFFSET) // 2 - box_width // 2
                    box_y = (SCREEN_HEIGHT + 2 * OFFSET) // 2 - box_height // 2
                    button_width = 200
                    button_height = 40
                    button_x = box_x + (box_width - button_width) // 2
                    button1_y = box_y + 120
                    button2_y = box_y + 170
                    button1_rect = pygame.Rect(button_x, button1_y, button_width, button_height)
                    button2_rect = pygame.Rect(button_x, button2_y, button_width, button_height)

                    if button1_rect.collidepoint(mouse_pos):
                        if victory and not game.defeat:
                            victory = False
                            if game.level < 10:
                                conn = sqlite3.connect("game_data.db")
                                cursor = conn.cursor()
                                cursor.execute("UPDATE user_levels SET is_unlocked=1 WHERE user_id=? AND level_number=?",
                                               (user_id, game.level + 1))
                                conn.commit()
                                conn.close()
                            game.next_level()
                        else:
                            game.reset()
                    elif button2_rect.collidepoint(mouse_pos):
                        exit_to_menu = True
                        break

        if exit_to_menu:
            break

        if not paused and game.run:
            game.spaceship_group.update()
            game.move_aliens()
            game.alien_lasers_group.update()
            game.mystery_ship_group.update()
            game.powerups_group.update()
            game.update_powerup_status()
            game.check_for_collisions()

            if game.lives <= 0:
                game.defeat = True
                game.run = False
                victory = False

            if len(game.aliens_group) == 0 and game.lives > 0:
                game.run = False
                victory = True

        screen.fill(GREY)
        pygame.draw.rect(screen, YELLOW, (10, 10, 780, 780), 2, 0, 60, 60, 60, 60)
        pygame.draw.line(screen, YELLOW, (25, 730), (775, 730), 3)

        if game.run:
            level_text = font.render(f"LEVEL {game.level}", True, YELLOW)
            screen.blit(level_text, (570, 740))

            pygame.draw.rect(screen, YELLOW, pause_button_rect)
            pause_button_label = "RESUME" if paused else "PAUSE"
            pause_button_text = font.render(pause_button_label, True, (50, 50, 50))
            screen.blit(pause_button_text, pause_button_text.get_rect(center=pause_button_rect.center))

            game.powerups_group.draw(screen)
            screen.blit(score_text_surface, (50, 15))
            formatted_score = str(game.score).zfill(5)
            score_surface = font.render(formatted_score, False, YELLOW)
            screen.blit(score_surface, (50, 40))

            screen.blit(highscore_text_surface, (550, 15))
            formatted_highscore = str(game.highscore).zfill(5)
            highscore_surface = font.render(formatted_highscore, False, YELLOW)
            screen.blit(highscore_surface, (550, 40))

            coins_text = font.render(f"Coins: {game.coins}", True, YELLOW)
            screen.blit(coins_text, (50, 80))

            if game.has_shield:
                shield_text = font.render("Shield Active", True, YELLOW)
                screen.blit(shield_text, (50, 100))
            elif game.has_double_shot:
                double_shot_text = font.render("Double Shot Active", True, YELLOW)
                screen.blit(double_shot_text, (50, 100))

            game.spaceship_group.draw(screen)
            game.spaceship_group.sprite.lasers_group.draw(screen)
            for obstacle in game.obstacles:
                obstacle.blocks_group.draw(screen)
            game.aliens_group.draw(screen)
            game.alien_lasers_group.draw(screen)
            game.mystery_ship_group.draw(screen)

            if paused:
                pause_overlay = pygame.Surface((SCREEN_WIDTH + OFFSET, SCREEN_HEIGHT + 2 * OFFSET))
                pause_overlay.set_alpha(150)
                pause_overlay.fill(BLACK)
                screen.blit(pause_overlay, (0, 0))

                pygame.draw.rect(screen, BLACK, (pause_box_x, pause_box_y, pause_box_width, pause_box_height))
                pygame.draw.rect(screen, YELLOW, (pause_box_x, pause_box_y, pause_box_width, pause_box_height), 4)

                paused_text = font.render("PAUSED", True, YELLOW)
                paused_rect = paused_text.get_rect(center=(pause_box_x + pause_box_width // 2, pause_box_y + 30))
                screen.blit(paused_text, paused_rect)

                pygame.draw.rect(screen, YELLOW, resume_rect)
                resume_text = font.render("Resume", True, (50, 50, 50))
                screen.blit(resume_text, resume_text.get_rect(center=resume_rect.center))

                pygame.draw.rect(screen, YELLOW, exit_rect)
                exit_text = font.render("Exit", True, (50, 50, 50))
                screen.blit(exit_text, exit_text.get_rect(center=exit_rect.center))

        else:
            overlay = pygame.Surface((SCREEN_WIDTH + OFFSET, SCREEN_HEIGHT + 2 * OFFSET))
            overlay.set_alpha(180)
            overlay.fill(BLACK)
            screen.blit(overlay, (0, 0))

            box_width = 500
            box_height = 250
            box_x = (SCREEN_WIDTH + OFFSET) // 2 - box_width // 2
            box_y = (SCREEN_HEIGHT + 2 * OFFSET) // 2 - box_height // 2
            message_box_rect = pygame.Rect(box_x, box_y, box_width, box_height)
            pygame.draw.rect(screen, BLACK, message_box_rect)
            pygame.draw.rect(screen, YELLOW, message_box_rect, 4)

            big_font = pygame.font.Font("Font/monogram.ttf", 60)
            if victory:
                msg_text = big_font.render("LEVEL COMPLETE!", True, (0, 255, 0))
            else:
                msg_text = big_font.render("GAME OVER", True, (255, 0, 0))
            msg_rect = msg_text.get_rect(center=(box_x + box_width // 2, box_y + 60))
            screen.blit(msg_text, msg_rect)

            button_width = 200
            button_height = 40
            button_x = box_x + (box_width - button_width) // 2
            button1_y = box_y + 120
            button2_y = box_y + 170
            button1_rect = pygame.Rect(button_x, button1_y, button_width, button_height)
            button2_rect = pygame.Rect(button_x, button2_y, button_width, button_height)

            pygame.draw.rect(screen, YELLOW, button1_rect)
            pygame.draw.rect(screen, YELLOW, button2_rect)
            smaller_font = pygame.font.Font("Font/monogram.ttf", 40)

            if victory:
                button1_text = smaller_font.render("Next Level", True, (50, 50, 50))
            else:
                button1_text = smaller_font.render("Play Again", True, (50, 50, 50))
            button2_text = smaller_font.render("Exit", True, (50, 50, 50))

            screen.blit(button1_text, button1_text.get_rect(center=button1_rect.center))
            screen.blit(button2_text, button2_text.get_rect(center=button2_rect.center))

        pygame.display.update()
        clock.tick(60)

    save_coins_db(game.coins, user_id)
    pygame.quit()
    root.deiconify()
    show_main_menu_welcome(username, user_id)

def show_main_menu():
    # Eski menü fonksiyonu, isterseniz silebilirsiniz.
    menu_win = tk.Toplevel(root)
    menu_win.title("Ana Menü")
    menu_win.geometry("700x500")
    menu_win.configure(bg="black")

    title_label = tk.Label(menu_win, text="ANA MENÜ", font=("Arial", 18, "bold"), fg="yellow", bg="black")
    title_label.pack(pady=20)

    market_btn = tk.Button(menu_win, text="Market", font=("Arial", 14), fg="black", bg="yellow",
                           command=lambda: show_market(root, 1))
    market_btn.pack(pady=10)

    play_btn = tk.Button(menu_win, text="Oyuna Başla", font=("Arial", 14), fg="black", bg="yellow",
                         command=lambda: start_game(1, menu_win, 1, "UserX"))
    play_btn.pack(pady=10)

    level_btn = tk.Button(menu_win, text="Seviye Seç", font=("Arial", 14), fg="black", bg="yellow",
                          command=lambda: show_level_selection(1, "UserX"))
    level_btn.pack(pady=10)

    score_btn = tk.Button(menu_win, text="Skor Tablosu", font=("Arial", 14), fg="black", bg="yellow",
                          command=show_scoreboard)
    score_btn.pack(pady=10)

# -----------------------------------------------------
# UYGULAMANIN ANA GİRİŞ NOKTASI
# -----------------------------------------------------
def main():
    init_user_db()
    root.title("Giriş / Kayıt")
    root.geometry("700x500")
    root.configure(bg="black")

    info_label = tk.Label(root, text="Lütfen giriş yapın ya da kayıt olun.",
                          font=("Arial", 16, "bold"), fg="yellow", bg="black")
    info_label.pack(pady=10)

    login_button = tk.Button(root, text="Giriş Yap", font=("Arial", 14),
                             fg="black", bg="yellow",
                             command=lambda: show_login_window(root))
    login_button.pack(pady=10)

    register_button = tk.Button(root, text="Kayıt Ol", font=("Arial", 14),
                                fg="black", bg="yellow",
                                command=lambda: show_register_window(root))
    register_button.pack(pady=10)

    exit_button = tk.Button(root, text="Çıkış", font=("Arial", 14),
                            fg="black", bg="yellow", command=root.destroy)
    exit_button.pack(pady=10)

    root.mainloop()

if __name__ == "__main__":
    root = tk.Tk()
    main()

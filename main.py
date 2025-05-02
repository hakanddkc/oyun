import sqlite3
import tkinter as tk
from tkinter import messagebox
import pygame, sys, random
from game import Game          # game.py içindeki Game sınıfınız
from profil import show_profile  # Profil ekranı fonksiyonunu profil.py'den import ettik
import scoretable              # Skor tablosu için modül

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
            score INTEGER DEFAULT 0,
            PRIMARY KEY (user_id, level_number),
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)
    conn.commit()
    conn.close()

def register_user_db(username, password):
    conn = sqlite3.connect("game_data.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users WHERE username=?", (username,))
    if cursor.fetchone():
        conn.close()
        return False
    cursor.execute(
        "INSERT INTO users (username, password, coins) VALUES (?, ?, ?)",
        (username, password, 500)
    )
    user_id = cursor.lastrowid
    for lvl in range(1, 11):
        is_unlocked = 1 if lvl == 1 else 0
        cursor.execute(
            "INSERT INTO user_levels (user_id, level_number, is_unlocked, score) VALUES (?, ?, ?, ?)",
            (user_id, lvl, is_unlocked, 0)
        )
    conn.commit()
    conn.close()
    return True

def login_user(username, password):
    conn = sqlite3.connect("game_data.db")
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id FROM users WHERE username=? AND password=?",
        (username, password)
    )
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else None

def unlock_next_level(user_id, current_level):
    next_level = current_level + 1
    if next_level <= 10:
        conn = sqlite3.connect("game_data.db")
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE user_levels SET is_unlocked=1 WHERE user_id=? AND level_number=?",
            (user_id, next_level)
        )
        conn.commit()
        conn.close()
        messagebox.showinfo("Level Açıldı", f"{next_level}. seviye açıldı!")

def get_levels_for_user(user_id):
    conn = sqlite3.connect("game_data.db")
    cursor = conn.cursor()
    cursor.execute(
        "SELECT level_number, is_unlocked FROM user_levels WHERE user_id=?",
        (user_id,)
    )
    levels = cursor.fetchall()
    conn.close()
    return levels

def load_coins_db(user_id):
    conn = sqlite3.connect("game_data.db")
    cursor = conn.cursor()
    cursor.execute("SELECT coins FROM users WHERE id=?", (user_id,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else 0

def save_coins_db(coins, user_id):
    conn = sqlite3.connect("game_data.db")
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET coins=? WHERE id=?", (coins, user_id))
    conn.commit()
    conn.close()

def save_level_score(user_id, level_number, score):
    """
    Oynanan level için elde edilen skoru db'ye yazar.
    Eski skordan yüksekse günceller.
    """
    conn = sqlite3.connect("game_data.db")
    cursor = conn.cursor()
    cursor.execute(
        "SELECT score FROM user_levels WHERE user_id=? AND level_number=?",
        (user_id, level_number)
    )
    old = cursor.fetchone()[0]
    if score > old:
        cursor.execute(
            "UPDATE user_levels SET score=? WHERE user_id=? AND level_number=?",
            (score, user_id, level_number)
        )
    conn.commit()
    conn.close()

# -----------------------------------------------------
# SEÇİLEN GEMİNİN YOLUNU BULMA
# -----------------------------------------------------
def get_equipped_ship_path(user_id):
    conn = sqlite3.connect("game_data.db")
    cursor = conn.cursor()
    cursor.execute("""
        SELECT ship_id FROM user_ships
        WHERE user_id=? AND is_equipped=1
    """, (user_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return None
    ship_id = row[0]
    cursor.execute("SELECT image_path FROM ships WHERE id=?", (ship_id,))
    row2 = cursor.fetchone()
    conn.close()
    return row2[0] if row2 else None

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
        if user_id:
            messagebox.showinfo("Başarılı", f"Hoşgeldiniz, {username}!")
            login_win.destroy()
            show_main_menu_welcome(username, user_id)
        else:
            messagebox.showerror("Hata", "Kullanıcı adı veya şifre yanlış!")

    tk.Button(login_win, text="Giriş Yap", font=("Arial", 12),
              fg="black", bg="yellow", command=attempt_login).pack(pady=10)
    tk.Button(login_win, text="Çıkış", font=("Arial", 12),
              fg="black", bg="yellow", command=login_win.destroy).pack(pady=10)

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

    tk.Button(reg_win, text="Kayıt Ol", font=("Arial", 12),
              fg="black", bg="yellow", command=attempt_register).pack(pady=10)
    tk.Button(reg_win, text="Çıkış", font=("Arial", 12),
              fg="black", bg="yellow", command=reg_win.destroy).pack(pady=10)

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

    tk.Button(root, text="Oyuna Başla", font=("Arial", 14), fg="black", bg="yellow",
              command=lambda: show_level_selection(user_id, username)).pack(pady=10)
    tk.Button(root, text="Market", font=("Arial", 14), fg="black", bg="yellow",
              command=lambda: show_market(root, user_id)).pack(pady=10)
    tk.Button(root, text="Profil", font=("Arial", 14), fg="black", bg="yellow",
              command=lambda: show_profile(root, user_id)).pack(pady=10)
    tk.Button(root, text="Skor Tablosu", font=("Arial", 14), fg="black", bg="yellow",
              command=show_scoreboard).pack(pady=10)
    tk.Button(root, text="Yenile", font=("Arial", 14), fg="black", bg="yellow",
              command=refresh_coins).pack(pady=10)
    tk.Button(root, text="Çıkış", font=("Arial", 14), fg="black", bg="yellow",
              command=root.destroy).pack(pady=10)

def show_scoreboard():
    try:
        scoretable.show_scoretable(root)
    except Exception as e:
        messagebox.showerror("Hata", f"Skor tablosu yüklenemedi:\n{e}")

def show_market(master, user_id):
    try:
        import market
        market.show_market(master, user_id)
    except ImportError as e:
        messagebox.showerror("Hata", f"Market modülü bulunamadı:\n{e}")

# -----------------------------------------------------
# SEVİYE SEÇİMİ
# -----------------------------------------------------
def show_level_selection(user_id, username):
    level_win = tk.Toplevel(root)
    level_win.title("Seviye Seç")
    level_win.geometry("700x500")
    level_win.configure(bg="black")

    tk.Label(level_win, text="LEVEL SEÇ", font=("Arial", 18, "bold"), fg="yellow", bg="black")\
      .grid(row=0, column=0, columnspan=2, pady=20)

    level_frame = tk.Frame(level_win, bg="black")
    level_frame.grid(row=1, column=0, columnspan=2)

    conn = sqlite3.connect("game_data.db")
    cursor = conn.cursor()
    cursor.execute("SELECT level_number, is_unlocked FROM user_levels WHERE user_id=?", (user_id,))
    levels_data = cursor.fetchall()
    conn.close()

    level_dict = {lvl: unlocked for (lvl, unlocked) in levels_data}
    row = col = 0
    for level in range(1, 11):
        if level_dict.get(level, 0):
            btn = tk.Button(level_frame, text=f"Level {level}", font=("Arial", 14),
                            fg="black", bg="yellow",
                            command=lambda lvl=level: start_game(lvl, level_win, user_id, username))
        else:
            btn = tk.Button(level_frame, text=f"Level {level} (Locked)", font=("Arial", 14),
                            fg="gray", bg="darkgray", state=tk.DISABLED)
        btn.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")
        col = (col + 1) % 2
        if col == 0:
            row += 1

# -----------------------------------------------------
# OYUN BAŞLATMA
# -----------------------------------------------------
def start_game(selected_level, win, user_id, username):
    if win is not root:
        win.destroy()
    else:
        root.withdraw()
    pygame.init()

    SCREEN_WIDTH, SCREEN_HEIGHT, OFFSET = 750, 700, 50
    font = pygame.font.Font("Font/monogram.ttf", 40)
    score_surf = font.render("SCORE", False, YELLOW)
    highscore_surf = font.render("HIGH-SCORE", False, YELLOW)

    screen = pygame.display.set_mode((SCREEN_WIDTH + OFFSET, SCREEN_HEIGHT + 2 * OFFSET))
    pygame.display.set_caption("Python Space Invaders")
    clock = pygame.time.Clock()

    equipped_path = get_equipped_ship_path(user_id) or "Graphics/default_spaceship.png"
    game = Game(SCREEN_WIDTH, SCREEN_HEIGHT, OFFSET, selected_level, spaceship_image_path=equipped_path)
    game.coins = load_coins_db(user_id)

    paused = victory = exit_to_menu = False
    SHOOT_LASER = pygame.USEREVENT
    MYSTERYSHIP = pygame.USEREVENT + 1
    POWERUP_EVENT = pygame.USEREVENT + 2

    pygame.time.set_timer(SHOOT_LASER, 300)
    pygame.time.set_timer(MYSTERYSHIP, random.randint(4000, 8000))
    pygame.time.set_timer(POWERUP_EVENT, random.randint(8000, 12000))

    pause_button_rect = pygame.Rect((SCREEN_WIDTH+OFFSET)//2-70, 10, 140, 50)
    pause_box = {'x': (SCREEN_WIDTH+OFFSET)//2-200, 'y': (SCREEN_HEIGHT+2*OFFSET)//2-75, 'w':400, 'h':150}
    btn_dims = {'w':180, 'h':40}
    resume_rect = pygame.Rect(pause_box['x']+(pause_box['w']-btn_dims['w'])//2, pause_box['y']+60, btn_dims['w'], btn_dims['h'])
    exit_rect   = pygame.Rect(pause_box['x']+(pause_box['w']-btn_dims['w'])//2, pause_box['y']+110, btn_dims['w'], btn_dims['h'])

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                save_coins_db(game.coins, user_id)
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_p:
                paused = not paused

            if game.run:
                if event.type == pygame.MOUSEBUTTONDOWN and pause_button_rect.collidepoint(pygame.mouse.get_pos()):
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
                        mp = pygame.mouse.get_pos()
                        if resume_rect.collidepoint(mp):
                            paused = False
                        elif exit_rect.collidepoint(mp):
                            exit_to_menu = True
                            break

            if not game.run and event.type == pygame.MOUSEBUTTONDOWN:
                mp = pygame.mouse.get_pos()
                box = {'x': (SCREEN_WIDTH+OFFSET)//2-250, 'y': (SCREEN_HEIGHT+2*OFFSET)//2-125, 'w':500, 'h':250}
                btn1 = pygame.Rect(box['x']+(box['w']-200)//2, box['y']+120, 200, 40)
                btn2 = pygame.Rect(box['x']+(box['w']-200)//2, box['y']+170, 200, 40)
                if btn1.collidepoint(mp):
                    if victory and not game.defeat:
                        victory = False
                        if game.level < 10:
                            conn = sqlite3.connect("game_data.db")
                            c = conn.cursor()
                            c.execute(
                                "UPDATE user_levels SET is_unlocked=1 WHERE user_id=? AND level_number=?",
                                (user_id, game.level + 1)
                            )
                            conn.commit()
                            conn.close()
                        game.next_level()
                    else:
                        game.reset()
                elif btn2.collidepoint(mp):
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
            if not game.aliens_group:
                game.run = False
                victory = True

        screen.fill(GREY)
        pygame.draw.rect(screen, YELLOW, (10,10,780,780), 2, 0,60,60,60,60)
        pygame.draw.line(screen, YELLOW,(25,730),(775,730),3)

        if game.run:
            screen.blit(font.render(f"LEVEL {game.level}", True, YELLOW),(570,740))
            pygame.draw.rect(screen, YELLOW, pause_button_rect)
            screen.blit(font.render("RESUME" if paused else "PAUSE", True, BLACK),
                        font.render("RESUME" if paused else "PAUSE", True, BLACK).get_rect(center=pause_button_rect.center))
            game.powerups_group.draw(screen)
            screen.blit(score_surf,(50,15))
            screen.blit(font.render(str(game.score).zfill(5), False, YELLOW),(50,40))
            screen.blit(highscore_surf,(550,15))
            screen.blit(font.render(str(game.highscore).zfill(5), False, YELLOW),(550,40))
            screen.blit(font.render(f"Coins: {game.coins}", True, YELLOW),(50,80))

            if game.has_shield:
                screen.blit(font.render("Shield Active", True, YELLOW),(50,100))
            elif game.has_double_shot:
                screen.blit(font.render("Double Shot Active", True, YELLOW),(50,100))

            game.spaceship_group.draw(screen)
            game.spaceship_group.sprite.lasers_group.draw(screen)
            for obs in game.obstacles:
                obs.blocks_group.draw(screen)
            game.aliens_group.draw(screen)
            game.alien_lasers_group.draw(screen)
            game.mystery_ship_group.draw(screen)

            if paused:
                overlay = pygame.Surface((SCREEN_WIDTH+OFFSET, SCREEN_HEIGHT+2*OFFSET))
                overlay.set_alpha(150); overlay.fill(BLACK)
                screen.blit(overlay,(0,0))
                pygame.draw.rect(screen, BLACK, (pause_box['x'], pause_box['y'], pause_box['w'], pause_box['h']))
                pygame.draw.rect(screen, YELLOW, (pause_box['x'], pause_box['y'], pause_box['w'], pause_box['h']),4)
                screen.blit(font.render("PAUSED", True, YELLOW),
                            font.render("PAUSED", True, YELLOW).get_rect(center=(pause_box['x']+pause_box['w']//2, pause_box['y']+30)))
                pygame.draw.rect(screen, YELLOW, resume_rect)
                screen.blit(font.render("Resume", True, BLACK),
                            font.render("Resume", True, BLACK).get_rect(center=resume_rect.center))
                pygame.draw.rect(screen, YELLOW, exit_rect)
                screen.blit(font.render("Exit", True, BLACK),
                            font.render("Exit", True, BLACK).get_rect(center=exit_rect.center))

        else:
            overlay = pygame.Surface((SCREEN_WIDTH+OFFSET, SCREEN_HEIGHT+2*OFFSET))
            overlay.set_alpha(180); overlay.fill(BLACK)
            screen.blit(overlay,(0,0))
            box = {'x': (SCREEN_WIDTH+OFFSET)//2-250,'y':(SCREEN_HEIGHT+2*OFFSET)//2-125,'w':500,'h':250}
            pygame.draw.rect(screen, BLACK,(box['x'],box['y'],box['w'],box['h']))
            pygame.draw.rect(screen, YELLOW,(box['x'],box['y'],box['w'],box['h']),4)
            big = pygame.font.Font("Font/monogram.ttf",60)
            msg = big.render("LEVEL COMPLETE!" if victory else "GAME OVER", True,
                             (0,255,0) if victory else (255,0,0))
            screen.blit(msg, msg.get_rect(center=(box['x']+box['w']//2, box['y']+60)))
            b1 = pygame.Rect(box['x']+(box['w']-200)//2,box['y']+120,200,40)
            b2 = pygame.Rect(box['x']+(box['w']-200)//2,box['y']+170,200,40)
            pygame.draw.rect(screen,YELLOW,b1); pygame.draw.rect(screen,YELLOW,b2)
            sf = pygame.font.Font("Font/monogram.ttf",40)
            screen.blit(sf.render("Next Level" if victory else "Play Again", True, BLACK),
                        sf.render("Next Level" if victory else "Play Again", True, BLACK).get_rect(center=b1.center))
            screen.blit(sf.render("Exit", True, BLACK),
                        sf.render("Exit", True, BLACK).get_rect(center=b2.center))

        pygame.display.update()
        clock.tick(60)

    # Oyun döngüsü bittiğinde skoru kaydet ve çıkış yap
    save_level_score(user_id, selected_level, game.score)
    save_coins_db(game.coins, user_id)
    pygame.quit()
    root.deiconify()
    show_main_menu_welcome(username, user_id)

def show_main_menu():
    menu_win = tk.Toplevel(root)
    menu_win.title("Ana Menü")
    menu_win.geometry("700x500")
    menu_win.configure(bg="black")

    tk.Label(menu_win, text="ANA MENÜ", font=("Arial", 18, "bold"), fg="yellow", bg="black")\
      .pack(pady=20)
    tk.Button(menu_win, text="Market", font=("Arial", 14), fg="black", bg="yellow",
              command=lambda: show_market(root, 1)).pack(pady=10)
    tk.Button(menu_win, text="Oyuna Başla", font=("Arial", 14), fg="black", bg="yellow",
              command=lambda: start_game(1, menu_win, 1, "UserX")).pack(pady=10)
    tk.Button(menu_win, text="Seviye Seç", font=("Arial", 14), fg="black", bg="yellow",
              command=lambda: show_level_selection(1, "UserX")).pack(pady=10)
    tk.Button(menu_win, text="Skor Tablosu", font=("Arial", 14), fg="black", bg="yellow",
              command=show_scoreboard).pack(pady=10)

def main():
    init_user_db()
    root.title("Giriş / Kayıt")
    root.geometry("700x500")
    root.configure(bg="black")

    tk.Label(root, text="Lütfen giriş yapın ya da kayıt olun.",
             font=("Arial", 16, "bold"), fg="yellow", bg="black")\
      .pack(pady=10)
    tk.Button(root, text="Giriş Yap", font=("Arial", 14),
              fg="black", bg="yellow", command=lambda: show_login_window(root))\
      .pack(pady=10)
    tk.Button(root, text="Kayıt Ol", font=("Arial", 14),
              fg="black", bg="yellow", command=lambda: show_register_window(root))\
      .pack(pady=10)
    tk.Button(root, text="Çıkış", font=("Arial", 14),
              fg="black", bg="yellow", command=root.destroy)\
      .pack(pady=10)

    root.mainloop()

if __name__ == "__main__":
    root = tk.Tk()
    main()

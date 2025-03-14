import sqlite3
import tkinter as tk
from tkinter import messagebox
import pygame, sys, random


# -------------------- Veritabanı İşlemleri --------------------
def init_user_db():
    """
    Veritabanını başlatır ve 'users' ile 'user_levels' tablolarını oluşturur.
    'user_levels' tablosu, her kullanıcı için 10 seviyenin kilit durumunu tutar.
    """
    conn = sqlite3.connect("game_data.db")
    cursor = conn.cursor()

    # Kullanıcı tablosu: (id, username, password)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT
        )
    """)

    # user_levels tablosu: (user_id, level_number, is_unlocked)
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


def register_user(username, password):
    """
    Kullanıcıyı veritabanına kaydeder. Başarılıysa True, aksi halde False döner.
    Kayıt sonrası user_levels tablosuna 10 adet level eklenir;
    Level 1 açık (is_unlocked=1), diğerleri kapalı (is_unlocked=0).
    """
    try:
        conn = sqlite3.connect("game_data.db")
        cursor = conn.cursor()
        cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
        user_id = cursor.lastrowid  # Yeni eklenen kullanıcının ID'si

        # 10 seviye ekleyelim: Level 1 kilitsiz, diğerleri kilitli.
        for lvl in range(1, 11):
            is_unlocked = 1 if lvl == 1 else 0
            cursor.execute("INSERT INTO user_levels (user_id, level_number, is_unlocked) VALUES (?, ?, ?)",
                           (user_id, lvl, is_unlocked))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        return False


def login_user(username, password):
    """
    Girilen bilgilerin doğruluğunu kontrol eder.
    Doğruysa user_id (int) döner, yanlışsa None.
    """
    conn = sqlite3.connect("game_data.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users WHERE username=? AND password=?", (username, password))
    result = cursor.fetchone()
    conn.close()
    if result is not None:
        return result[0]
    else:
        return None


def get_levels_for_user(user_id):
    """
    Kullanıcının seviye bilgilerini döndürür.
    [(level_number, is_unlocked), ...]
    """
    conn = sqlite3.connect("game_data.db")
    cursor = conn.cursor()
    cursor.execute("SELECT level_number, is_unlocked FROM user_levels WHERE user_id=?", (user_id,))
    levels = cursor.fetchall()
    conn.close()
    return levels


def unlock_next_level(user_id, current_level):
    """
    Mevcut seviye tamamlanınca bir sonraki leveli açar (is_unlocked=1).
    """
    next_level = current_level + 1
    if next_level <= 10:
        conn = sqlite3.connect("game_data.db")
        cursor = conn.cursor()
        cursor.execute("UPDATE user_levels SET is_unlocked=1 WHERE user_id=? AND level_number=?",
                       (user_id, next_level))
        conn.commit()
        conn.close()
        messagebox.showinfo("Level Açıldı", f"{next_level}. level kilidi açıldı!")


# -------------------- Giriş / Kayıt Ekranları --------------------
def show_login_window(master):
    login_win = tk.Toplevel(master)
    login_win.title("Giriş Yap")
    login_win.geometry("300x200")
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

    login_btn = tk.Button(login_win, text="Giriş Yap", font=("Arial", 12), fg="black", bg="yellow",
                          command=attempt_login)
    login_btn.pack(pady=10)


def show_register_window(master):
    reg_win = tk.Toplevel(master)
    reg_win.title("Kayıt Ol")
    reg_win.geometry("300x250")
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
        if register_user(username, password):
            messagebox.showinfo("Başarılı", "Kayıt başarılı, şimdi giriş yapabilirsiniz.")
            reg_win.destroy()
        else:
            messagebox.showerror("Hata", "Kullanıcı adı zaten mevcut!")

    reg_btn = tk.Button(reg_win, text="Kayıt Ol", font=("Arial", 12), fg="black", bg="yellow", command=attempt_register)
    reg_btn.pack(pady=10)


# -------------------- Ana Menü --------------------
def show_main_menu_welcome(username, user_id):
    root.deiconify()
    for widget in root.winfo_children():
        widget.destroy()

    welcome_label = tk.Label(root, text=f"Hoşgeldiniz, {username}!", font=("Arial", 18, "bold"), fg="yellow",
                             bg="black")
    welcome_label.pack(pady=20)

    # Butonlar: Oyuna Başla, Market, Profil, Skor Tablosu
    start_game_btn = tk.Button(root, text="Oyuna Başla", font=("Arial", 14), fg="black", bg="yellow",
                               command=lambda: show_level_selection(user_id))
    start_game_btn.pack(pady=10)

    market_btn = tk.Button(root, text="Market", font=("Arial", 14), fg="black", bg="yellow",
                           command=lambda: show_market(root))
    market_btn.pack(pady=10)

    profile_btn = tk.Button(root, text="Profil", font=("Arial", 14), fg="black", bg="yellow",
                            command=show_profile)
    profile_btn.pack(pady=10)

    scoreboard_btn = tk.Button(root, text="Skor Tablosu", font=("Arial", 14), fg="black", bg="yellow",
                               command=show_scoreboard)
    scoreboard_btn.pack(pady=10)


def show_profile():
    profile_win = tk.Toplevel(root)
    profile_win.title("Profil")
    profile_win.geometry("400x300")
    profile_win.configure(bg="black")
    label = tk.Label(profile_win, text="Profil (Placeholder)", font=("Arial", 16), fg="yellow", bg="black")
    label.pack(pady=20)


def show_scoreboard():
    scoreboard_win = tk.Toplevel(root)
    scoreboard_win.title("Skor Tablosu")
    scoreboard_win.geometry("400x300")
    scoreboard_win.configure(bg="black")
    label = tk.Label(scoreboard_win, text="Skor Tablosu (Placeholder)", font=("Arial", 16), fg="yellow", bg="black")
    label.pack(pady=20)


def show_market(master):
    try:
        import market
        market.show_market(master)
    except ImportError as e:
        print("Market modülü bulunamadı:", e)
        market_win = tk.Toplevel(master)
        market_win.title("Market")
        market_win.geometry("400x300")
        market_win.configure(bg="black")
        label = tk.Label(market_win, text="Market (Placeholder)", font=("Arial", 16), fg="yellow", bg="black")
        label.pack(pady=20)


# -------------------- Seviye Seçimi --------------------
def show_level_selection(user_id):
    level_win = tk.Toplevel(root)
    level_win.title("Seviye Seç")
    level_win.geometry("400x500")
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
                            command=lambda lvl=level: start_game_placeholder(lvl, user_id))
        else:
            btn = tk.Button(level_frame, text=f"Level {level} (Locked)", font=("Arial", 14),
                            fg="gray", bg="darkgray", state=tk.DISABLED)
        btn.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")
        col += 1
        if col > 1:
            col = 0
            row += 1


def start_game_placeholder(level, user_id):
    messagebox.showinfo("Level Seçildi", f"Kullanıcı ID {user_id} => Level {level} başlıyor...")
    # Gerçek oyunu başlatmak için kod buraya entegre edilebilir.
    # Örneğin, Game sınıfınızın start() metodunu çağırabilirsiniz.
    # unlock_next_level(user_id, level)


def unlock_next_level(user_id, current_level):
    next_level = current_level + 1
    if next_level <= 10:
        conn = sqlite3.connect("game_data.db")
        cursor = conn.cursor()
        cursor.execute("UPDATE user_levels SET is_unlocked=1 WHERE user_id=? AND level_number=?",
                       (user_id, next_level))
        conn.commit()
        conn.close()
        messagebox.showinfo("Level Açıldı", f"{next_level}. level kilidi açıldı!")


# -------------------- Ana Program --------------------
def main():
    init_user_db()
    root.title("Giriş / Kayıt")
    root.geometry("300x200")
    root.configure(bg="black")

    login_button = tk.Button(root, text="Giriş Yap", font=("Arial", 14), fg="black", bg="yellow",
                             command=lambda: show_login_window(root))
    login_button.pack(pady=20)

    register_button = tk.Button(root, text="Kayıt Ol", font=("Arial", 14), fg="black", bg="yellow",
                                command=lambda: show_register_window(root))
    register_button.pack(pady=20)

    root.mainloop()


# Ana pencere
root = tk.Tk()
if __name__ == "__main__":
    main()

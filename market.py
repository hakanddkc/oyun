import tkinter as tk
import sqlite3
from PIL import Image, ImageTk
from tkinter import messagebox
from collections import defaultdict

# -----------------------------------------------------
# VERİTABANI İŞLEMLERİ
# -----------------------------------------------------

def init_ships_and_user_ships_db():
    """
    Market ile ilgili tabloları (ships, user_ships) oluşturur.
    Eğer tablo boşsa örnek kayıtlar ekler.
    """
    conn = sqlite3.connect("game_data.db")
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ships (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            level INTEGER,
            price INTEGER,
            image_path TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_ships (
            user_id INTEGER,
            ship_id INTEGER,
            is_owned INTEGER DEFAULT 0,
            is_equipped INTEGER DEFAULT 0,
            PRIMARY KEY (user_id, ship_id),
            FOREIGN KEY (ship_id) REFERENCES ships(id)
        )
    """)

    cursor.execute("SELECT COUNT(*) FROM ships")
    if cursor.fetchone()[0] == 0:
        sample = []
        for lvl in (1, 2, 3):
            for color in ("blue", "darkgrey", "green", "greyblue", "seagreen"):
                price = lvl * 100
                path = f"Graphics/{color}_{lvl}.png"
                sample.append((lvl, price, path))
        cursor.executemany(
            "INSERT INTO ships (level, price, image_path) VALUES (?, ?, ?)",
            sample
        )

    conn.commit()
    conn.close()


def load_ships_from_db():
    """Tüm gemileri id, level, price, image_path ile listeleme."""
    conn = sqlite3.connect("game_data.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, level, price, image_path FROM ships ORDER BY level")
    rows = cursor.fetchall()
    conn.close()
    return rows


def check_user_ownership_and_equip(user_id, ship_id):
    """(is_owned, is_equipped) ya da None döner."""
    conn = sqlite3.connect("game_data.db")
    cursor = conn.cursor()
    cursor.execute(
        "SELECT is_owned, is_equipped FROM user_ships WHERE user_id=? AND ship_id=?",
        (user_id, ship_id)
    )
    row = cursor.fetchone()
    conn.close()
    return row


def set_user_ownership(user_id, ship_id, is_owned=1):
    """Satın alma durumunu ekleme/güncelleme."""
    conn = sqlite3.connect("game_data.db")
    cursor = conn.cursor()
    cursor.execute(
        "INSERT OR REPLACE INTO user_ships (user_id, ship_id, is_owned, is_equipped)"
        " VALUES (?, ?, ?, COALESCE((SELECT is_equipped FROM user_ships WHERE user_id=? AND ship_id=?),0))",
        (user_id, ship_id, is_owned, user_id, ship_id)
    )
    conn.commit()
    conn.close()


def equip_gemi(user_id, ship_id):
    """Tüm gemilerin is_equipped=0, ilgili geminin is_equipped=1."""
    conn = sqlite3.connect("game_data.db")
    cursor = conn.cursor()
    cursor.execute("UPDATE user_ships SET is_equipped=0 WHERE user_id=?", (user_id,))
    cursor.execute(
        "UPDATE user_ships SET is_equipped=1 WHERE user_id=? AND ship_id=?", (user_id, ship_id)
    )
    conn.commit()
    conn.close()


def load_coins_db(user_id):
    """Kullanıcının coin bakiyesini çeker."""
    conn = sqlite3.connect("game_data.db")
    cursor = conn.cursor()
    cursor.execute("SELECT coins FROM users WHERE id=?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else 0


def save_coins_db(coins, user_id):
    """Coin bakiyesini günceller."""
    conn = sqlite3.connect("game_data.db")
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET coins=? WHERE id=?", (coins, user_id))
    conn.commit()
    conn.close()


def buy_gemi(ship_id, price, coins_label, user_id, market_win):
    """Satın alma işlemi. Coin yeterliyse satın al ve yenile."""
    coins = load_coins_db(user_id)
    if coins >= price:
        save_coins_db(coins-price, user_id)
        set_user_ownership(user_id, ship_id, 1)
        coins_label.config(text=f"Coins: {coins-price}")
        messagebox.showinfo("Başarılı", f"Gemi satın alındı. Kalan coin: {coins-price}")
        market_win.destroy()
        show_market(market_win.master, user_id)
    else:
        messagebox.showwarning("Yetersiz Bakiye", "Coin bakiyeniz yetersiz.")


def select_gemi(ship_id, user_id, market_win):
    """Gemi seçme (equip) işlemi."""
    equip_gemi(user_id, ship_id)
    messagebox.showinfo("Seçildi", "Gemi başarıyla seçildi.")
    market_win.destroy()
    show_market(market_win.master, user_id)


def show_market(master, user_id=1):
    init_ships_and_user_ships_db()

    market_win = tk.Toplevel(master)
    market_win.title("Market - Gemi Seçimi")
    market_win.geometry("800x600")
    market_win.configure(bg="black")

    # Geri butonu sol üst
    back_btn = tk.Button(
        market_win,
        text="← Geri",
        font=("Arial", 12),
        fg="black",
        bg="yellow",
        command=market_win.destroy
    )
    back_btn.pack(anchor="nw", padx=10, pady=10)

    # Coin göstergesi
    coins = load_coins_db(user_id)
    coins_label = tk.Label(
        market_win,
        text=f"Coins: {coins}",
        font=("Arial", 14),
        fg="yellow",
        bg="black"
    )
    coins_label.pack()

    # Kaydırılabilir içerik
    main_frame = tk.Frame(market_win, bg="black")
    main_frame.pack(fill="both", expand=True, padx=20, pady=10)

    canvas = tk.Canvas(main_frame, bg="black", highlightthickness=0)
    scrollbar = tk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
    canvas.configure(yscrollcommand=scrollbar.set)
    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    content = tk.Frame(canvas, bg="black")
    canvas.create_window((0,0), window=content, anchor="nw")
    content.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

    ships = load_ships_from_db()
    by_level = defaultdict(list)
    for sid, lvl, pr, ip in ships:
        by_level[lvl].append((sid, pr, ip))

    for lvl in sorted(by_level):
        lvl_lbl = tk.Label(
            content,
            text=f"Level {lvl} Gemileri",
            font=("Arial", 16, "bold"),
            fg="yellow",
            bg="black"
        )
        lvl_lbl.pack(pady=10, anchor="center")

        row_frame = tk.Frame(content, bg="black")
        row_frame.pack(pady=5, anchor="center")

        for sid, price, img_path in by_level[lvl]:
            frm = tk.Frame(row_frame, bg="black", highlightthickness=1, highlightbackground="yellow")
            frm.pack(side="left", padx=15)

            try:
                img = Image.open(img_path)
                img = img.resize((80, 80), Image.LANCZOS)
            except:
                img = Image.new("RGB", (80, 80), (100, 100, 100))
            photo = ImageTk.PhotoImage(img)
            lbl_img = tk.Label(frm, image=photo, bg="black")
            lbl_img.photo = photo
            lbl_img.pack(pady=5)

            tk.Label(
                frm,
                text=f"{price} Coins",
                font=("Arial", 10),
                fg="white",
                bg="black"
            ).pack()

            info = check_user_ownership_and_equip(user_id, sid)
            if not info or info[0] == 0:
                btn = tk.Button(
                    frm,
                    text="Buy",
                    font=("Arial", 10),
                    fg="black",
                    bg="yellow",
                    command=lambda sid=sid, pr=price: buy_gemi(sid, pr, coins_label, user_id, market_win)
                )
            else:
                if info[1] == 1:
                    btn = tk.Button(
                        frm,
                        text="Current",
                        font=("Arial", 10),
                        fg="black",
                        bg="yellow",
                        command=lambda: messagebox.showinfo("Info", "Bu gemi zaten aktif!")
                    )
                else:
                    btn = tk.Button(
                        frm,
                        text="Select",
                        font=("Arial", 10),
                        fg="black",
                        bg="yellow",
                        command=lambda sid=sid: select_gemi(sid, user_id, market_win)
                    )
            btn.pack(pady=5)

    market_win.mainloop()


# Doğrudan çalıştırıldığında test
if __name__ == "__main__":
    root = tk.Tk()
    root.title("Market Test")
    root.geometry("800x600")
    root.configure(bg="black")
    tk.Button(
        root,
        text="Market'e Git",
        font=("Arial", 14),
        fg="black",
        bg="yellow",
        command=lambda: show_market(root, user_id=1)
    ).pack(pady=20)
    root.mainloop()
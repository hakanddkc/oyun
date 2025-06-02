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
    - ships tablosunu health ve shots sütunlarıyla birlikte oluşturur (varsa migrate eder).
    - user_ships tablosunu oluşturur.
    - Eğer ships tablosu boşsa sample data ekler.
    """
    conn = sqlite3.connect("game_data.db")
    c = conn.cursor()

    # Mevcut şemayı al
    c.execute("PRAGMA table_info(ships);")
    cols = [col[1] for col in c.fetchall()]

    if not cols:
        # Tablo yoksa baştan oluştur
        c.execute("""
            CREATE TABLE ships (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                level INTEGER,
                price INTEGER,
                image_path TEXT,
                health INTEGER NOT NULL DEFAULT 3,
                shots INTEGER NOT NULL DEFAULT 1
            )
        """)
    else:
        # Var ve sütun eksikse, ekle
        if "health" not in cols:
            c.execute("ALTER TABLE ships ADD COLUMN health INTEGER NOT NULL DEFAULT 3;")
        if "shots" not in cols:
            c.execute("ALTER TABLE ships ADD COLUMN shots INTEGER NOT NULL DEFAULT 1;")

    # user_ships tablosu
    c.execute("""
        CREATE TABLE IF NOT EXISTS user_ships (
            user_id INTEGER,
            ship_id INTEGER,
            is_owned INTEGER DEFAULT 0,
            is_equipped INTEGER DEFAULT 0,
            PRIMARY KEY(user_id,ship_id),
            FOREIGN KEY(ship_id) REFERENCES ships(id)
        )
    """)

    # sample veri ekle (tablo boşsa)
    c.execute("SELECT COUNT(*) FROM ships;")
    if c.fetchone()[0] == 0:
        sample = []
        for lvl in (1, 2, 3):
            h, s = (3, 1) if lvl == 1 else ((4, 2) if lvl == 2 else (5, 3))
            for color in ("blue", "darkgrey", "green", "greyblue", "seagreen"):
                sample.append((lvl, lvl * 100, f"Graphics/{color}_{lvl}.png", h, s))
        c.executemany(
            "INSERT INTO ships (level,price,image_path,health,shots) VALUES (?,?,?,?,?);",
            sample
        )

    conn.commit()
    conn.close()

def load_ships_from_db():
    """
    (id, level, price, image_path, health, shots) formatında tüm gemileri döner.
    """
    conn = sqlite3.connect("game_data.db")
    c = conn.cursor()
    c.execute("""
        SELECT id, level, price, image_path, health, shots
        FROM ships
        ORDER BY level, id
    """)
    rows = c.fetchall()
    conn.close()
    return rows

def check_user_ownership_and_equip(user_id, ship_id):
    conn = sqlite3.connect("game_data.db")
    c = conn.cursor()
    c.execute(
        "SELECT is_owned, is_equipped FROM user_ships WHERE user_id=? AND ship_id=?",
        (user_id, ship_id)
    )
    row = c.fetchone()
    conn.close()
    return row

def set_user_ownership(user_id, ship_id, is_owned=1):
    conn = sqlite3.connect("game_data.db")
    c = conn.cursor()
    c.execute(
        "INSERT OR REPLACE INTO user_ships (user_id, ship_id, is_owned, is_equipped) "
        "VALUES (?, ?, ?, COALESCE((SELECT is_equipped FROM user_ships WHERE user_id=? AND ship_id=?), 0))",
        (user_id, ship_id, is_owned, user_id, ship_id)
    )
    conn.commit()
    conn.close()

def equip_gemi(user_id, ship_id):
    conn = sqlite3.connect("game_data.db")
    c = conn.cursor()
    c.execute("UPDATE user_ships SET is_equipped=0 WHERE user_id=?", (user_id,))
    c.execute("UPDATE user_ships SET is_equipped=1 WHERE user_id=? AND ship_id=?", (user_id, ship_id))
    conn.commit()
    conn.close()

def load_coins_db(user_id):
    conn = sqlite3.connect("game_data.db")
    c = conn.cursor()
    c.execute("SELECT coins FROM users WHERE id=?", (user_id,))
    row = c.fetchone()
    conn.close()
    return row[0] if row else 0

def save_coins_db(coins, user_id):
    conn = sqlite3.connect("game_data.db")
    c = conn.cursor()
    c.execute("UPDATE users SET coins=? WHERE id=?", (coins, user_id))
    conn.commit()
    conn.close()

def buy_gemi(ship_id, price, coins_label, user_id, market_win):
    coins = load_coins_db(user_id)
    if coins >= price:
        save_coins_db(coins - price, user_id)
        set_user_ownership(user_id, ship_id, 1)
        coins_label.config(text=f"Coins: {coins - price}")
        messagebox.showinfo("Başarılı", f"Gemi satın alındı.\nKalan coin: {coins - price}")
        market_win.destroy()
        show_market(market_win.master, user_id)
    else:
        messagebox.showwarning("Yetersiz Bakiye", "Coin bakiyeniz yetersiz.")

def select_gemi(ship_id, user_id, market_win):
    equip_gemi(user_id, ship_id)
    messagebox.showinfo("Seçildi", "Gemi başarıyla seçildi.")
    market_win.destroy()
    show_market(market_win.master, user_id)

# -----------------------------------------------------
# MARKET ARAYÜZÜ
# -----------------------------------------------------
def show_market(master, user_id=1):
    init_ships_and_user_ships_db()

    market_win = tk.Toplevel(master)
    market_win.title("Market - Gemi Seçimi")
    market_win.geometry("800x600")
    market_win.resizable(False, False)
    market_win.configure(bg="black")

    # Arka plan
    bg_img = ImageTk.PhotoImage(
        Image.open("Graphics/anasayfa.png").resize((800, 600), Image.LANCZOS)
    )
    bg_label = tk.Label(market_win, image=bg_img)
    bg_label.image = bg_img
    bg_label.place(x=0, y=0, relwidth=1, relheight=1)

    # Başlık ve geri butonu
    title = tk.Label(market_win, text="🛒 Space Store",
                     font=("Constantia", 26, "bold"), fg="yellow", bg="black")
    title.pack(pady=(20, 10))
    back_btn = tk.Button(market_win, text="← Geri", font=("Arial", 12, "bold"),
                         fg="black", bg="yellow", command=market_win.destroy)
    back_btn.place(x=10, y=10)

    # Coin göstergesi
    coins = load_coins_db(user_id)
    coins_label = tk.Label(market_win, text=f"Coins: {coins}",
                           font=("Cambria", 16, "bold"), fg="yellow", bg="black")
    coins_label.pack()

    # Scrollable canvas & oklar
    outer = tk.Frame(market_win, bg="black")
    outer.pack(fill="both", expand=True, padx=20, pady=10)

    canvas = tk.Canvas(outer, bg="black", highlightthickness=0, width=720, height=500)
    canvas.pack(side="left", fill="both", expand=True)

    controls = tk.Frame(outer, bg="black")
    controls.pack(side="right", fill="y")

    up_btn = tk.Button(controls, text="▲", font=("Arial", 12, "bold"),
                       fg="black", bg="yellow", command=lambda: canvas.yview_scroll(-3, "units"))
    up_btn.pack(fill="x")
    scrollbar = tk.Scrollbar(controls, orient="vertical", command=canvas.yview)
    scrollbar.pack(fill="y", expand=True)
    down_btn = tk.Button(controls, text="▼", font=("Arial", 12, "bold"),
                         fg="black", bg="yellow", command=lambda: canvas.yview_scroll(3, "units"))
    down_btn.pack(fill="x")

    canvas.configure(yscrollcommand=scrollbar.set)
    canvas.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

    content = tk.Frame(canvas, bg="black")
    canvas.create_window((0, 0), window=content, anchor="nw")

    # Gemileri yükle ve grupla
    ships = load_ships_from_db()
    by_level = defaultdict(list)
    for sid, lvl, price, imgpath, health, shots in ships:
        by_level[lvl].append((sid, price, imgpath, health, shots))

    for lvl in sorted(by_level):
        lvl_lbl = tk.Label(content, text=f"{lvl}. LEVEL GEMİLER",
                           font=("Cambria", 18, "bold"), fg="yellow", bg="black")
        lvl_lbl.pack(pady=(15, 5))
        row = tk.Frame(content, bg="black")
        row.pack(pady=5)
        for sid, price, imgpath, health, shots in by_level[lvl]:
            sf = tk.Frame(row, bg="black", bd=1, relief="solid")
            sf.pack(side="left", padx=10)

            # Gemi resmi
            try:
                im = Image.open(imgpath).resize((80, 80), Image.LANCZOS)
            except:
                im = Image.new("RGB", (80, 80), (60, 60, 60))
            ph = ImageTk.PhotoImage(im)
            lbl = tk.Label(sf, image=ph, bg="black")
            lbl.image = ph
            lbl.pack(pady=(8, 4))

            price_lbl = tk.Label(sf, text=f"{price} Coin",
                                 font=("Cambria", 12), fg="white", bg="midnightblue", width=10)
            price_lbl.pack(pady=(0, 6))

            stats_lbl = tk.Label(sf, text=f"❤ {health}   🔫 {shots}",
                                 font=("Cambria", 10), fg="lightgreen", bg="black")
            stats_lbl.pack(pady=(0, 6))

            info = check_user_ownership_and_equip(user_id, sid)
            if not info or info[0] == 0:
                btn = tk.Button(sf, text="Buy", font=("Arial", 10, "bold"),
                                fg="black", bg="yellow",
                                command=lambda s=sid, p=price: buy_gemi(s, p, coins_label, user_id, market_win))
            else:
                if info[1] == 1:
                    btn = tk.Button(sf, text="Current", font=("Arial", 10, "bold"),
                                    fg="black", bg="yellow", state="disabled")
                else:
                    btn = tk.Button(sf, text="Select", font=("Arial", 10, "bold"),
                                    fg="black", bg="yellow",
                                    command=lambda s=sid: select_gemi(s, user_id, market_win))
            btn.pack(pady=(0, 8))

    market_win.mainloop()

# Örnek çalıştırma
if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()
    show_market(root, user_id=1)
    root.mainloop()

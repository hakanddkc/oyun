# market.py

import tkinter as tk
import os
import sqlite3
from PIL import Image, ImageTk
from PIL.Image import Resampling
from tkinter import messagebox
from collections import defaultdict

def init_ships_and_user_ships_db():
    """
    Market ile ilgili tabloları (ships, user_ships) oluşturur.
    Tablo boşsa örnek veriler ekler (Level 1,2,3,4 gemileri).
    """
    conn = sqlite3.connect("game_data.db")
    cursor = conn.cursor()

    # ships tablosu
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ships (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            level INTEGER,
            price INTEGER,
            image_path TEXT
        )
    """)

    # user_ships tablosu (sahiplik ve ekip bilgisi)
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
    count = cursor.fetchone()[0]
    if count == 0:
        # Örnek gemiler: Level 4 -> anagemi.png ekleniyor
        sample_data = [
            (1, 100, "Graphics/gemi111.PNG"),
            (1, 100, "Graphics/gemi21.PNG"),
            (2, 200, "Graphics/gemi12.PNG"),
            (2, 200, "Graphics/gemi22.PNG"),
            (3, 300, "Graphics/gemi13.PNG"),
            (3, 300, "Graphics/gemi23.PNG"),
            (4, 400, "Graphics/anagemi.png")  # DİKKAT: Yeni gemi
        ]
        for (lvl, price, path) in sample_data:
            cursor.execute("""
                INSERT INTO ships (level, price, image_path)
                VALUES (?, ?, ?)
            """, (lvl, price, path))
        print("ships tablosuna örnek kayıtlar eklendi.")

    conn.commit()
    conn.close()

def load_ships_from_db():
    """
    ships tablosundaki tüm gemileri (id, level, price, image_path) döndürür.
    """
    conn = sqlite3.connect("game_data.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, level, price, image_path FROM ships ORDER BY level")
    rows = cursor.fetchall()
    conn.close()
    return rows

def check_user_ownership_and_equip(user_id, ship_id):
    """
    user_ships tablosunda user_id, ship_id kaydını bulup
    (is_owned, is_equipped) döndürür, yoksa None.
    """
    conn = sqlite3.connect("game_data.db")
    cursor = conn.cursor()
    cursor.execute("""
        SELECT is_owned, is_equipped
        FROM user_ships
        WHERE user_id=? AND ship_id=?
    """, (user_id, ship_id))
    row = cursor.fetchone()
    conn.close()

    if row is not None:
        return (row[0], row[1])
    else:
        return None

def set_user_ownership(user_id, ship_id, is_owned=1):
    """
    user_ships tablosunda (user_id, ship_id) kaydı ekler/günceller,
    is_owned=1 => satın alındı.
    """
    conn = sqlite3.connect("game_data.db")
    cursor = conn.cursor()

    cursor.execute("""
        SELECT is_owned
        FROM user_ships
        WHERE user_id=? AND ship_id=?
    """, (user_id, ship_id))
    existing = cursor.fetchone()

    if existing is None:
        # Insert
        cursor.execute("""
            INSERT INTO user_ships (user_id, ship_id, is_owned)
            VALUES (?, ?, ?)
        """, (user_id, ship_id, is_owned))
    else:
        # Update
        cursor.execute("""
            UPDATE user_ships
            SET is_owned=?
            WHERE user_id=? AND ship_id=?
        """, (is_owned, user_id, ship_id))

    conn.commit()
    conn.close()

def equip_gemi(user_id, ship_id):
    """
    user_ships'te user_id'ye ait tüm gemilerde is_equipped=0 yapar,
    sonra sadece bu gemide is_equipped=1.
    """
    conn = sqlite3.connect("game_data.db")
    cursor = conn.cursor()

    # Tüm gemilerde devre dışı
    cursor.execute("""
        UPDATE user_ships
        SET is_equipped=0
        WHERE user_id=?
    """, (user_id,))

    # Bu gemiyi aktif
    cursor.execute("""
        UPDATE user_ships
        SET is_equipped=1
        WHERE user_id=? AND ship_id=?
    """, (user_id, ship_id))

    conn.commit()
    conn.close()

def load_coins_db(user_id=1):
    """
    Kullanıcının coin değerini okur.
    """
    conn = sqlite3.connect("game_data.db")
    cursor = conn.cursor()
    cursor.execute("SELECT coins FROM users WHERE id=?", (user_id,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else 500

def save_coins_db(coins, user_id=1):
    """
    Kullanıcının coin değerini yazar.
    """
    conn = sqlite3.connect("game_data.db")
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET coins=? WHERE id=?", (coins, user_id))
    conn.commit()
    conn.close()

def show_market(master, user_id=1):
    """
    Market ekranını açar.
    - “Buy” => satın al (is_owned=1),
    - “Select” => equip gemi (is_equipped=1),
    - “Current” => bu gemi zaten aktif.
    """
    init_ships_and_user_ships_db()

    market_win = tk.Toplevel(master)
    market_win.title("Market - Gemi Seçimi")
    market_win.geometry("800x600")
    market_win.configure(bg="black")

    current_coins = load_coins_db(user_id)
    coins_label = tk.Label(market_win, text=f"Coins: {current_coins}",
                           font=("Arial", 14), fg="yellow", bg="black")
    coins_label.pack(pady=5)

    title = tk.Label(market_win, text="Market - Gemi Seçimi",
                     font=("Arial", 18, "bold"), fg="yellow", bg="black")
    title.pack(pady=10)

    main_frame = tk.Frame(market_win, bg="black")
    main_frame.pack(fill="both", expand=True)

    canvas = tk.Canvas(main_frame, bg="black", highlightthickness=0)
    canvas.pack(side="left", fill="both", expand=True)

    scrollbar = tk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
    scrollbar.pack(side="right", fill="y")
    canvas.configure(yscrollcommand=scrollbar.set)

    content_frame = tk.Frame(canvas, bg="black")
    canvas.create_window((0, 0), window=content_frame, anchor="nw")

    def on_configure(event):
        canvas.configure(scrollregion=canvas.bbox("all"))
    content_frame.bind("<Configure>", on_configure)

    # ships tablosundaki gemileri al
    all_ships = load_ships_from_db()
    # Level bazında grupla
    ships_by_level = defaultdict(list)
    for (ship_id, lvl, price, img_path) in all_ships:
        ships_by_level[lvl].append((ship_id, price, img_path))

    row_counter = 0

    for level_num in sorted(ships_by_level.keys()):
        level_label = tk.Label(
            content_frame,
            text=f"Level {level_num} Gemileri",
            font=("Arial", 16, "bold"), fg="yellow", bg="black"
        )
        level_label.grid(row=row_counter, column=0, pady=5, sticky="w")
        row_counter += 1

        level_frame = tk.Frame(content_frame, bg="black")
        level_frame.grid(row=row_counter, column=0, pady=5, sticky="w")
        row_counter += 1

        col_counter = 0
        row_in_level = 0

        for (ship_id, price, img_path) in ships_by_level[level_num]:
            gem_frame = tk.Frame(level_frame, bg="black",
                                 highlightthickness=1, highlightcolor="yellow", highlightbackground="yellow")
            gem_frame.grid(row=row_in_level, column=col_counter, padx=5, pady=5, sticky="n")

            # Resmi yükle
            try:
                from PIL import ImageDraw
                img = Image.open(img_path)
                img = img.resize((80, 80), Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(img)
            except Exception as e:
                print(f"Hata: {e} - {img_path}")
                placeholder_img = Image.new("RGB", (80, 80), (100, 100, 100))
                d = ImageDraw.Draw(placeholder_img)
                d.text((10, 30), "N/A", fill=(255, 0, 0))
                photo = ImageTk.PhotoImage(placeholder_img)

            img_label = tk.Label(gem_frame, image=photo, bg="black")
            img_label.photo = photo
            img_label.pack(pady=5)

            price_label = tk.Label(gem_frame, text=f"{price} Coins",
                                   font=("Arial", 10), fg="white", bg="black")
            price_label.pack()

            # Kullanıcının sahiplik / equip durumuna bak
            ownership_info = check_user_ownership_and_equip(user_id, ship_id)
            if ownership_info is None:
                btn_text = "Buy"
                btn_command = lambda sid=ship_id, pr=price: buy_gemi(
                    sid, pr, coins_label, user_id, market_win
                )
            else:
                is_owned, is_equipped = ownership_info
                if is_owned == 0:
                    btn_text = "Buy"
                    btn_command = lambda sid=ship_id, pr=price: buy_gemi(
                        sid, pr, coins_label, user_id, market_win
                    )
                else:
                    if is_equipped == 1:
                        btn_text = "Current"
                        btn_command = lambda: messagebox.showinfo(
                            "Bilgi", "Bu gemi zaten aktif kullanılıyor!"
                        )
                    else:
                        btn_text = "Select"
                        btn_command = lambda sid=ship_id, p=img_path: select_gemi(
                            sid, p, user_id, market_win
                        )

            buy_btn = tk.Button(
                gem_frame,
                text=btn_text,
                font=("Arial", 12),
                fg="black",
                bg="yellow",
                command=btn_command
            )
            buy_btn.pack(pady=5)

            col_counter += 1
            if col_counter >= 4:
                col_counter = 0
                row_in_level += 1

def buy_gemi(ship_id, price, coins_label, user_id, market_window):
    """
    Kullanıcı yeterli coine sahipse gemiyi satın alır, marketi yeniler.
    """
    current_coins = load_coins_db(user_id)
    if current_coins >= price:
        new_coins = current_coins - price
        save_coins_db(new_coins, user_id)
        set_user_ownership(user_id, ship_id, 1)
        coins_label.config(text=f"Coins: {new_coins}")
        messagebox.showinfo("Satın Alındı", f"Gemi satın alındı.\nYeni bakiye: {new_coins} Coins")

        market_window.destroy()
        show_market(market_window.master, user_id)
    else:
        messagebox.showinfo("Yetersiz Bakiye", "Bu gemiyi satın alacak kadar coin yok.")

def select_gemi(ship_id, img_path, user_id, market_window):
    """
    Gemi equip (is_equipped=1).
    """
    equip_gemi(user_id, ship_id)
    messagebox.showinfo("Gemi Seçildi", f"{img_path} gemisi şu anki geminiz olarak ayarlandı!")

    market_window.destroy()
    show_market(market_window.master, user_id)

if __name__ == "__main__":
    root = tk.Tk()
    root.title("Market Test")
    root.geometry("400x200")
    root.config(bg="black")

    init_ships_and_user_ships_db()

    test_btn = tk.Button(
        root, text="Market'e Git", font=("Arial", 14),
        fg="black", bg="yellow",
        command=lambda: show_market(root, user_id=1)
    )
    test_btn.pack(pady=20)

    root.mainloop()

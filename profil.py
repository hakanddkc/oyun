import tkinter as tk
from tkinter import messagebox
import sqlite3
from PIL import Image, ImageTk  # Görselleri göstermek için PIL kullanıyoruz

# Helper fonksiyonlar

def load_highscore(user_id):
    """Veritabanından ilgili kullanıcının en yüksek skorunu çeker."""
    conn = sqlite3.connect("game_data.db")
    cursor = conn.cursor()
    cursor.execute("SELECT MAX(score) FROM user_levels WHERE user_id=?", (user_id,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result and result[0] is not None else 0


def show_profile(master, user_id):
    profile_win = tk.Toplevel(master)
    profile_win.title("Profil")
    profile_win.geometry("700x500")
    profile_win.configure(bg="black")

    # Veritabanından kullanıcı bilgilerini çekiyoruz
    conn = sqlite3.connect("game_data.db")
    cursor = conn.cursor()

    # Kullanıcı adı ve coin bilgilerini alıyoruz
    cursor.execute("SELECT username, coins FROM users WHERE id=?", (user_id,))
    user_data = cursor.fetchone()

    conn.close()

    if not user_data:
        messagebox.showerror("Hata", "Profil bilgileri alınamadı.")
        return

    username, coins = user_data


    # Kullanıcının sahip olduğu gemileri alıyoruz
    conn = sqlite3.connect("game_data.db")
    cursor = conn.cursor()
    cursor.execute("SELECT ship_id FROM user_ships WHERE user_id=?", (user_id,))
    user_ships = cursor.fetchall()
    conn.close()

    ship_images = []
    for (ship_id,) in user_ships:
        try:
            conn = sqlite3.connect("game_data.db")
            cursor = conn.cursor()
            cursor.execute("SELECT image_path FROM ships WHERE id=?", (ship_id,))
            row = cursor.fetchone()
            conn.close()
            if row:
                ship_images.append(row[0])
        except:
            continue

    # Profil bilgilerini ekrana yazdırıyoruz
    profile_label = tk.Label(profile_win,
        text=f"Kullanıcı Adı: {username}\nCoins: {coins}",
        font=("Arial", 16), fg="yellow", bg="black")
    profile_label.pack(pady=10)

    # Gemiler
    if ship_images:
        ships_label = tk.Label(profile_win, text="Sahip Olduğun Gemiler:",
                               font=("Arial", 14), fg="yellow", bg="black")
        ships_label.pack(pady=5)

        ship_frame = tk.Frame(profile_win, bg="black")
        ship_frame.pack(pady=10)

        for idx, path in enumerate(ship_images):
            try:
                img = Image.open(path)
                img = img.resize((100, 100))
                img_tk = ImageTk.PhotoImage(img)
                lbl = tk.Label(ship_frame, image=img_tk, bg="black")
                lbl.image = img_tk
                lbl.grid(row=0, column=idx, padx=5)
            except Exception as e:
                print(f"Gemi görseli yüklenemedi: {e}")
    else:
        no_ships_label = tk.Label(profile_win, text="Henüz gemi almadınız.",
                                   font=("Arial", 14), fg="yellow", bg="black")
        no_ships_label.pack(pady=10)

    exit_btn = tk.Button(profile_win, text="Geri Dön", font=("Arial", 12),
                         fg="black", bg="yellow", command=profile_win.destroy)
    exit_btn.pack(pady=10)
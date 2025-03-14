import tkinter as tk
import os
from PIL import Image, ImageTk
from PIL.Image import Resampling
from tkinter import messagebox

# Coin yönetimi (dosya tabanlı)
def load_coins():
    try:
        with open("coins.txt", "r") as file:
            coins = int(file.read().strip())
            return coins
    except Exception:
        return 500  # Varsayılan başlangıç parası

def save_coins(coins):
    with open("coins.txt", "w") as file:
        file.write(str(coins))

def show_market(master):
    """
    Market ekranını açar.
    master: Ana Tkinter penceresi veya root.
    """
    market_win = tk.Toplevel(master)
    market_win.title("Market - Gemi Seçimi")
    market_win.geometry("800x600")
    market_win.configure(bg="black")

    # Coin bilgisi label'ı (veritabanı yerine coins.txt kullanıyoruz)
    current_coins = load_coins()
    coins_label = tk.Label(market_win, text=f"Coins: {current_coins}", font=("Arial", 14), fg="yellow", bg="black")
    coins_label.pack(pady=5)

    title = tk.Label(market_win, text="Market - Gemi Seçimi", font=("Arial", 18, "bold"), fg="yellow", bg="black")
    title.pack(pady=10)

    # Ana frame: canvas + scrollbar (dikey kaydırma)
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

    # Her level için gemi listelerini manuel olarak belirliyoruz.
    # Her gemi için (dosya yolu, fiyat) tuple'ı kullanıyoruz.
    level_images = {
        1: [
            ("Graphics/gemi111.PNG", 100), ("Graphics/gemi21.PNG", 100), ("Graphics/gemi31.PNG", 100), ("Graphics/gemi41.PNG", 100),
            ("Graphics/gemi51.PNG", 100), ("Graphics/gemi61.PNG", 100), ("Graphics/gemi71.PNG", 100), ("Graphics/gemi81.PNG", 100),
            ("Graphics/gemi91.PNG", 100), ("Graphics/gemi101.PNG", 100)
        ],
        2: [
            ("Graphics/gemi12.PNG", 200), ("Graphics/gemi22.PNG", 200), ("Graphics/gemi32.PNG", 200), ("Graphics/gemi42.PNG", 200),
            ("Graphics/gemi52.PNG", 200), ("Graphics/gemi62.PNG", 200), ("Graphics/gemi72.PNG", 200), ("Graphics/gemi82.PNG", 200),
            ("Graphics/gemi92.PNG", 200), ("Graphics/gemi102.PNG", 200)
        ],
        3: [
            ("Graphics/gemi13.PNG", 300), ("Graphics/gemi23.PNG", 300), ("Graphics/gemi33.PNG", 300), ("Graphics/gemi43.PNG", 300),
            ("Graphics/gemi53.PNG", 300), ("Graphics/gemi63.PNG", 300), ("Graphics/gemi73.PNG", 300), ("Graphics/gemi83.PNG", 300),
            ("Graphics/gemi93.PNG", 300), ("Graphics/gemi103.PNG", 300)
        ]
    }

    # Her level için bölüm oluşturuluyor.
    for level_num in sorted(level_images.keys()):
        level_label = tk.Label(content_frame, text=f"Level {level_num} Gemileri",
                               font=("Arial", 16, "bold"), fg="yellow", bg="black")
        level_label.pack(pady=5)

        frame = tk.Frame(content_frame, bg="black")
        frame.pack(pady=10)

        col_counter = 0
        row_counter = 0
        # Her satıra 5 gemi sığacak şekilde düzenliyoruz.
        for (img_path, price) in level_images[level_num]:
            try:
                img = Image.open(img_path)
                img = img.resize((80, 80), Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(img)
            except Exception as e:
                print(f"Hata: {e} - {img_path}")
                from PIL import ImageDraw
                placeholder_img = Image.new("RGB", (80, 80), (100, 100, 100))
                d = ImageDraw.Draw(placeholder_img)
                d.text((10, 30), "N/A", fill=(255, 0, 0))
                photo = ImageTk.PhotoImage(placeholder_img)

            img_label = tk.Label(frame, image=photo, bg="black")
            img_label.photo = photo
            img_label.grid(row=row_counter*3, column=col_counter, padx=5, pady=5)

            # Fiyat label'ı
            price_label = tk.Label(frame, text=f"{price} Coins", font=("Arial", 10), fg="white", bg="black")
            price_label.grid(row=row_counter*3 + 1, column=col_counter, padx=5, pady=2)

            # Başlangıçta gemi henüz satın alınmamışsa "Buy" butonu; satın alındıysa "Select" butonu.
            buy_btn = tk.Button(frame, text="Buy", font=("Arial", 12), fg="black", bg="yellow")
            buy_btn.grid(row=row_counter*3 + 2, column=col_counter, padx=5, pady=5)
            buy_btn.config(command=lambda b=buy_btn, p=img_path, pr=price: buy_gemi(p, pr, coins_label, b))

            col_counter += 1
            if col_counter >= 5:
                col_counter = 0
                row_counter += 1

def buy_gemi(img_path, price, coins_label, button_widget):
    current_coins = load_coins()
    if current_coins >= price:
        current_coins -= price
        save_coins(current_coins)
        coins_label.config(text=f"Coins: {current_coins}")
        print(f"Gemi satın alındı: {img_path} - Fiyat: {price}")
        # Buton metnini "Buy" yerine "Select" olarak değiştir ve komutu gemiyi seçmeye yönlendir.
        button_widget.config(text="Select", command=lambda: select_gemi(img_path))
    else:
        print("Yeterli paranız yok!")
        messagebox.showinfo("Yetersiz Para", "Yeterli paranız yok!")

def select_gemi(img_path):
    print(f"Spaceship seçildi: {img_path}")
    messagebox.showinfo("Gemi Seçildi", f"{img_path} gemisi seçildi!")
    # Burada gemi seçimini oyunda kullanmak üzere kaydedebilir veya işlem yapabilirsiniz.

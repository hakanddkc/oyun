import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox


def show_scoretable(master):
    """
    Veritabanından her kullanıcının en yüksek skorunu çeker
    ve verilen master widget içinde listeler.
    """
    # Eğer master'ın içi doluysa temizle
    for w in master.winfo_children():
        w.destroy()

    master.configure(bg="black")

    # Başlık
    header = tk.Label(
        master,
        text="🏆 User's Highest Scores 🏆",
        font=("Cambria", 16, "bold"),
        fg="yellow",
        bg="black"
    )
    header.pack(pady=(10, 5))

    # Treeview oluşturma
    columns = ("Users", "Highest Scores")
    tree = ttk.Treeview(
        master,
        columns=columns,
        show="headings",
        height=15
    )
    for col in columns:
        tree.heading(col, text=col)
        tree.column(col, anchor="center")
    tree.pack(fill="both", expand=True, padx=20, pady=5)

    def load_scores():
        # Varolan satırları temizle
        for row in tree.get_children():
            tree.delete(row)

        try:
            conn = sqlite3.connect("game_data.db")
            cursor = conn.cursor()
            cursor.execute("""
                SELECT u.username,
                       MAX(ul.score) AS best_score
                FROM user_levels ul
                JOIN users u ON ul.user_id = u.id
                GROUP BY ul.user_id
                ORDER BY best_score DESC
            """)
            rows = cursor.fetchall()
        except Exception as e:
            messagebox.showerror("Veritabanı Hatası", f"Veri alınırken hata:\n{e}")
            return
        finally:
            conn.close()

        # Treeview'a ekle
        for username, best in rows:
            tree.insert("", "end", values=(username, best or 0))

    # Butonlar
    btn_frame = tk.Frame(master, bg="black")
    btn_frame.pack(pady=(5, 10))

    refresh_btn = tk.Button(
        btn_frame,
        text="Yenile",
        font=("Arial", 12),
        fg="black",
        bg="yellow",
        command=load_scores
    )
    refresh_btn.pack(side="left", padx=10)

    close_btn = tk.Button(
        btn_frame,
        text="Geri",
        font=("Arial", 12),
        fg="black",
        bg="yellow",
        command=lambda: master.master.show_main_menu_welcome()
    )
    close_btn.pack(side="left", padx=10)

    # İlk yükleme
    load_scores()

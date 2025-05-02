# scoretable.py
import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox

def show_scoretable(master):
    """
    Veritabanından her kullanıcının en yüksek skorunu çeker
    ve bir Treeview içinde listeler.
    """
    score_win = tk.Toplevel(master)
    score_win.title("Skor Tablosu")
    score_win.geometry("500x400")
    score_win.configure(bg="black")

    # Başlık
    header = tk.Label(
        score_win,
        text="🏆 Kullanıcıların En Yüksek Skorları 🏆",
        font=("Arial", 16, "bold"),
        fg="yellow",
        bg="black"
    )
    header.pack(pady=(10, 5))

    # Treeview oluşturma
    columns = ("Kullanıcı", "En Yüksek Skor")
    tree = ttk.Treeview(
        score_win,
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
    btn_frame = tk.Frame(score_win, bg="black")
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
        text="Kapat",
        font=("Arial", 12),
        fg="black",
        bg="yellow",
        command=score_win.destroy
    )
    close_btn.pack(side="left", padx=10)

    # İlk yükleme
    load_scores()

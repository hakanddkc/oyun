import sqlite3

# Veritabanına bağlan
conn = sqlite3.connect("game_data.db")
cursor = conn.cursor()

# Örnek: id'si 1, 2 ve 3 olan gemilerin price değerini güncelle
cursor.execute("UPDATE ships SET price = ? WHERE id = ?", (300, 1))
cursor.execute("UPDATE ships SET price = ? WHERE id = ?", (1000, 2))
cursor.execute("UPDATE ships SET price = ? WHERE id = ?", (1000, 3))
cursor.execute("UPDATE ships SET price = ? WHERE id = ?", (1000, 4))
cursor.execute("UPDATE ships SET price = ? WHERE id = ?", (1000, 5))
cursor.execute("UPDATE ships SET price = ? WHERE id = ?", (2000, 6))
cursor.execute("UPDATE ships SET price = ? WHERE id = ?", (2000, 7))
cursor.execute("UPDATE ships SET price = ? WHERE id = ?", (2000, 8))
cursor.execute("UPDATE ships SET price = ? WHERE id = ?", (2000, 9))
cursor.execute("UPDATE ships SET price = ? WHERE id = ?", (2000, 10))
cursor.execute("UPDATE ships SET price = ? WHERE id = ?", (3000, 11))
cursor.execute("UPDATE ships SET price = ? WHERE id = ?", (3000, 12))
cursor.execute("UPDATE ships SET price = ? WHERE id = ?", (3000, 13))
cursor.execute("UPDATE ships SET price = ? WHERE id = ?", (3000, 14))
cursor.execute("UPDATE ships SET price = ? WHERE id = ?", (3000, 15))

# Değişiklikleri kaydet
conn.commit()

# Bağlantıyı kapat
conn.close()

print("Fiyatlar başarıyla güncellendi.")

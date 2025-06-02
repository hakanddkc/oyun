import sqlite3

def get_equipped_ship_stats(user_id):
    with sqlite3.connect("data.db") as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT path, health, shots FROM user_ships
            JOIN ships ON ships.id = user_ships.ship_id
            WHERE user_ships.user_id = ? AND user_ships.equipped = 1
        """, (user_id,))
        return cursor.fetchone()

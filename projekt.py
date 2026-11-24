import matplotlib
import tkinter as tk
import sqlite3
import threading

#nazwa bazy danych
database_name = "school.db"

# Połączenie z bazą danych
conn = sqlite3.connect("database.db")

cursor = conn.cursor()

cursor.execute("""    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT UNIQUE,
        age INTEGER
    )"""
)

conn.commit()

cursor.execute("""
    CREATE TABLE IF NOT EXISTS wydatki (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        kwota D
    
""")





win = tk.Tk()


































win.mainloop()
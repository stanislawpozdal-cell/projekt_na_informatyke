import matplotlib
import sys

from PySide6.QtCore import QUrl, QObject
from PySide6.QtWebChannel import QWebChannel
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWidgets import QApplication, QWidget, QPushButton, QVBoxLayout
import sqlite3
from pathlib import Path
from PySide6.QtCore import QObject, Slot, QUrl
from datetime import date








class Backend(QObject):

    def __init__(self,):
        super().__init__()
        self.conn = sqlite3.connect("wydatki.db")
        self.cursor = self.conn.cursor()
        self.cursor.execute("""    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT UNIQUE,
        age INTEGER
        )""")
        self.conn.commit()
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS wydatki (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        kwota DOUBLE NOT NULL,
        data DATE NOT NULL)""")

    @Slot(str,int,result=bool)
    def del_data(self,tabela, id):
        print(tabela, id)
        dozwolone_tabele = ["wydatki"]

        if tabela  in dozwolone_tabele:
            self.cursor.execute(f"DELETE FROM {tabela} WHERE id={id}")
            self.conn.commit()
            return True
        else:
            return False

    @Slot(str, result="QVariantList")
    def return_data(self, tabela):
        dozwolone_tabele = ["wydatki"]

        if tabela not in dozwolone_tabele:
            return []

        self.cursor.execute(f"SELECT * FROM {tabela} ORDER BY data DESC, id DESC")

        wyniki = self.cursor.fetchall()

        return [list(row) for row in wyniki]

    @Slot(str,float,result=bool)
    def dodaj_wydatek(self,name, kwota):
        print(name, kwota)
        teraz = date.today()
        self.cursor.execute("""
            INSERT INTO wydatki (name, kwota, data)
            VALUES (?, ?, ?)
        """, (f"{name}", kwota, teraz.isoformat()))
        self.conn.commit()
        return True
    @Slot()
    def test(self):
        print("wywołanie funkcji")


#ustawienia okna

app = QApplication(sys.argv)
backend = Backend()


print(backend.return_data("wydatki"))

okno = QWebEngineView()
channel = QWebChannel()
channel.registerObject("backend",backend)
okno.page().setWebChannel(channel)
okno.setWindowTitle("Aplikacja do wydatków")
okno.resize(1000, 700)
sciezka = Path(__file__).parent / "index.html"
okno.load(QUrl.fromLocalFile(sciezka.resolve()))
okno.show()


sys.exit(app.exec())




































import matplotlib.pyplot as plt
import sys

import numpy as np
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
        self.conn.commit()

        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS przychody(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        kwota DOUBLE NOT NULL,
        podatek DECIMAL ,
        data DATE NOT NULL)""")
        self.conn.commit()

        self.folder_path = Path("wykresy")
        self.folder_path.mkdir(parents=True, exist_ok=True)
        

    @Slot(str,int,result=bool)
    def del_data(self,tabela, id):
        print(tabela, id)
        dozwolone_tabele = ["wydatki","przychody"]

        if tabela  in dozwolone_tabele:
            self.cursor.execute(f"DELETE FROM {tabela} WHERE id={id}")
            self.conn.commit()
            return True
        else:
            return False
    @Slot(str,float,float,result=bool)
    def dodaj_przychod(self,name,kwota,podatek):
        print(name,kwota,podatek)
        try:
            self.cursor.execute("""
            INSERT INTO przychody (name,kwota,podatek,data)
            VALUES (?,?,?,?)""",(name,kwota,podatek,date.today().isoformat()))
            self.conn.commit()
            return True
        except:
            return False

    @Slot(str, str, str, result="QVariantList")
    def filtruj(self, data_od, data_do, typ):

        if typ not in ["wydatki", "przychody"]:
            return []

        self.cursor.execute(
            f"""
            SELECT * FROM {typ}
            WHERE data >= ? AND data <= ?
            ORDER BY data DESC
            """,
            (data_od, data_do)
        )

        return [list(x) for x in self.cursor.fetchall()]


    @Slot(str, result="QVariantList")
    def return_data(self, tabela):
        dozwolone_tabele = ["wydatki","przychody"]

        if tabela not in dozwolone_tabele:
            return []

        self.cursor.execute(f"SELECT * FROM {tabela} ORDER BY data DESC, id DESC")

        wyniki = self.cursor.fetchall()
        print(wyniki)



        return [list(row) for row  in wyniki]

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

    def oblicz(self, rok, tabela):
        buffer = []

        if tabela not in ["wydatki", "przychody"]:
            return []

        for i in range(1, 13):
            self.cursor.execute(f"""
                SELECT * FROM {tabela}
                WHERE strftime('%Y', data) = ?
                AND strftime('%m', data) = ?
                ORDER BY data DESC
            """, (str(rok), str(i).zfill(2)))

            buffer.append(sum(x[2] for x in self.cursor.fetchall()))

        return buffer




    @Slot(int,result=bool)
    def generuj_wykres_slupkowy(self,rok):
        print(rok)
        miesiace_d = {1:"Styczeń",2:"Luty",3:"Marzeć",4:"Kwiecień",5:"Maj",6:"Czerwiec",7:"Lipiec",8:"Sierpień",9:"Wrzesień",10:"Październik",11:"Listopad",12:"Grudzień"}
        miesiace = list(miesiace_d.values())
        wydatki = self.oblicz(rok,'wydatki')
        przychody = self.oblicz(rok,'przychody')
        x = np.arange(len(miesiace))
        szerokosc = 0.35

        plt.figure(figsize=(10, 5))

        slupki =plt.bar(x - szerokosc / 2, wydatki, szerokosc, label="Wydatki")
        slupki1 =plt.bar(x + szerokosc / 2, przychody, szerokosc, label="Przychody")

        plt.bar_label(slupki, fmt="%.0f zł", padding=3)
        plt.bar_label(slupki1, fmt="%.0f zł", padding=3)

        plt.xticks(x, miesiace)
        plt.ylabel("Kwota (zł)")
        plt.title("Porównanie przychodów i wydatków")
        plt.legend()

        plt.tight_layout()
        plt.savefig("./wykresy/wykres.png", dpi=150, bbox_inches="tight")
        plt.close()

        return True





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




































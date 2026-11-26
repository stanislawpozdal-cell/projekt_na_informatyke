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
import os
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import hashlib



def generuj_klucz(haslo, salt):
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,  # AES-256 = 32 bajty
        salt=salt,
        iterations=1_200_000
    )

    return kdf.derive(haslo.encode("utf-8"))




class Backend(QObject):

    def __init__(self,okno):
        super().__init__()
        self.okno = okno
        self.haslo = ""
        self.conn = sqlite3.connect("wydatki.db")
        self.cursor = self.conn.cursor()
        self.cursor.execute("""CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE,
        password TEXT
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

    @Slot()
    def load_register_page(self):
        print("Loading register page")
        register_page = Path(__file__).parent / "register.html"
        self.okno.load(QUrl.fromLocalFile(register_page.resolve()))

    @Slot()
    def load_index_page(self):
        print("Loading index page")
        index_page = Path(__file__).parent / "index.html"
        self.okno.load(QUrl.fromLocalFile(index_page.resolve()))


    @Slot(str,str, result=bool)
    def parse_password(self,login,password):
        try:
            self.cursor.execute("""
            SELECT * FROM users WHERE email = ?""",(login,))
            user = self.cursor.fetchone()
            if user[2] == hashlib.sha256(password.encode()).hexdigest():
                print(True)
                self.haslo = password
                return True
            else:
                print(False)
                return False
        except Exception as e:
            print(e)
            return False

    @Slot(str,str,result=bool)
    def register_user(self, email, password):
        try:
            self.cursor.execute("""
            INSERT INTO users (email, password) VALUES (?, ?)""",
                            (email, hashlib.sha256(password.encode("utf-8")).hexdigest()))
            self.conn.commit()
            return True
        except Exception as e :
            print(e)
            return False




        

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

    def oblicz(self, rok, tabela,miesiac=None):
        buffer = []

        if tabela not in ["wydatki", "przychody"]:
            return []
        if miesiac is None:

            for i in range(1, 13):
                self.cursor.execute(f"""
                    SELECT * FROM {tabela}
                    WHERE strftime('%Y', data) = ?
                    AND strftime('%m', data) = ?
                    ORDER BY data DESC
                """, (str(rok), str(i).zfill(2)))

                buffer.append(sum(x[2] for x in self.cursor.fetchall()))

            return buffer
        else:
            self.cursor.execute(f"""
                                SELECT * FROM {tabela}
                                WHERE strftime('%Y', data) = ?
                                AND strftime('%m', data) = ?
                                ORDER BY data DESC
                            """, (str(rok), str(miesiac).zfill(2)))

            return [sum(x[2] for x in self.cursor.fetchall())][0]




    @Slot(int,result=bool)
    def generuj_wykres_slupkowy_rok(self,rok):
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


    @Slot(int, int, result=bool)
    def generuj_wykres_slupkowy_miesiac(self, rok, miesiac):
        try:
            miesiace_d = {
                1: "Styczeń", 2: "Luty", 3: "Marzec",
                4: "Kwiecień", 5: "Maj", 6: "Czerwiec",
                7: "Lipiec", 8: "Sierpień", 9: "Wrzesień",
                10: "Październik", 11: "Listopad", 12: "Grudzień"
            }

            if miesiac not in miesiace_d:
                return False

            # Pobranie sum z bazy danych
            wydatki = self.oblicz(rok, "wydatki", miesiac)
            przychody = self.oblicz(rok, "przychody", miesiac)

            # Pojedyncze wartości
            x = np.arange(2)
            wartosci = [wydatki, przychody]
            etykiety = ["Wydatki", "Przychody"]

            plt.figure(figsize=(8, 5))

            slupki = plt.bar(x, wartosci, width=0.5)

            # Wartości nad słupkami
            plt.bar_label(slupki, fmt="%.2f zł", padding=5)

            plt.xticks(x, etykiety)
            plt.ylabel("Kwota (zł)")
            plt.title(f"Przychody i wydatki – {miesiace_d[miesiac]} {rok}")

            plt.grid(axis="y", alpha=0.3)
            plt.tight_layout()

            plt.savefig("./wykresy/wykres.png", dpi=150, bbox_inches="tight")
            plt.close()

            return True

        except Exception as e:
            print("Błąd generowania wykresu:", e)
            plt.close("all")
            return False


#ustawienia okna

app = QApplication(sys.argv)





okno = QWebEngineView()
backend = Backend(okno)
channel = QWebChannel()
channel.registerObject("backend",backend)
okno.page().setWebChannel(channel)
okno.setWindowTitle("Aplikacja do wydatków")
okno.resize(1000, 700)
sciezka = Path(__file__).parent / "index.html"
logowanie = Path(__file__).parent / "logowanie.html"
okno.load(QUrl.fromLocalFile(logowanie.resolve()))
okno.show()


sys.exit(app.exec())




































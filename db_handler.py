import sqlite3
import os

SHOW_PRINTS = False
SQLITE_DB_NAME = "energywatch.db"
TABLE_PRICE_CHANGES = "PriceChanges"

def create_db_with_table():
    cwd = os.getcwd()
    if "energywatch.db" not in os.listdir(cwd):
        print("CREATE SQLite DB")
        try:
            sqlite_connection = sqlite3.connect(SQLITE_DB_NAME)
            cursor = sqlite_connection.cursor()
            print("     Erfolgreich mit DB verbunden")
            sql_query = f"""CREATE TABLE {TABLE_PRICE_CHANGES} (
                                Id INTEGER PRIMARY KEY AUTOINCREMENT, -- Auto-incrementing primary key
                                City NVARCHAR(255) NOT NULL,
                                Provider NVARCHAR(255) NOT NULL,
                                Tariff NVARCHAR(255) NOT NULL,
                                Date NVARCHAR(255) NOT NULL,
                                Price NUMERIC(18,2) NOT NULL,
                                PriceBefore NUMERIC(18,2) NOT NULL,
                                Difference NUMERIC(18,2) NOT NULL,
                                Trend NVARCHAR(255) NOT NULL
                            );
                            """
            cursor.execute(sql_query)
            sqlite_connection.commit()
            cursor.close()

        except:
            print("     Verbindung fehlerhaft")
        finally:
            if sqlite_connection:
                sqlite_connection.close()
                print("     SQL Verbindung geschlossen")
    else:
        print("Found SQLite DB")

def post_price_change_to_local_sqlite_db(price_change):
    try:
        if SHOW_PRINTS : print("            POST PriceChange to DB")
        sqlite_connection = sqlite3.connect(SQLITE_DB_NAME)
        cursor = sqlite_connection.cursor()
        
        if SHOW_PRINTS : print("             Erfolgreich mit DB verbunden", end = " > ")
        sql_query = f"""INSERT INTO {TABLE_PRICE_CHANGES} (Id, City, Provider, Tariff, Date, Price, PriceBefore, Difference, Trend)
        VALUES (?,?,?,?,?,?,?,?,?);"""
        
        # Verwende den Decimal-Wert direkt im SQL-Query
        cursor.execute(sql_query, (None, price_change.city, price_change.provider, price_change.tariff, price_change.date, price_change.price, price_change.price_before, price_change.difference, price_change.trend))

        sqlite_connection.commit()
        if SHOW_PRINTS : print("Datenbank-Eintrag erfolgt", end = " > ")
        cursor.close()

    except Exception as e:
        if SHOW_PRINTS : print("Verbindung fehlerhaft:", e, end = " > ")
    finally:
        if sqlite_connection:
            sqlite_connection.close()
            if SHOW_PRINTS : print("SQL Verbindung geschlossen")

def get_latest_price_data_by_provider_tariff_from_sqlite_db(provider, tariff, city) -> dict:
    try:
        sqlite_connection = sqlite3.connect(SQLITE_DB_NAME)
        sqlite_connection.row_factory = sqlite3.Row
        cursor = sqlite_connection.cursor()
        sql_query = f"""SELECT * FROM {TABLE_PRICE_CHANGES}
                        WHERE Provider=? AND Tariff=? AND City=?
                        ORDER BY Date ASC"""
        cursor.execute(sql_query, (provider, tariff, city))
        results = cursor.fetchall()
        cursor.close()

        if len(results) > 0:
            last_entry = dict(results[-1])
            data = {
                "date": last_entry["Date"],
                "price_old": last_entry["Price"],
            }
            return data

        return None
        
    except Exception as e:
        if SHOW_PRINTS : print("Verbindung fehlerhaft:", e)
    finally:
        if sqlite_connection:
            sqlite_connection.close()

create_db_with_table()
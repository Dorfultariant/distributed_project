import sqlite3 as sq
from datetime import datetime as dt
import os

dbFile = "main.db"
dbInitFile = "db_init.sql"

db = None
cur = None

def initConnection():
    global db
    global cur
    db = sq.connect(dbFile)
    cur = db.cursor()
    cur.execute("PRAGMA foreign_keys = ON;")
    return True


def initDB():
    if os.path.isfile(dbFile):
        initConnection()
        return True
    initConnection()
    try:
        f = open(dbInitFile, "r")
        command = ""
        for l in f.readlines():
            command += l
        cur.executescript(command)
        cur.execute('''INSERT INTO User1 VALUES ('0', 'Admin', 'Admin', '1234')''')
        
        
        db.commit()
    except FileNotFoundError:
        print(f"'{dbInitFile}' file not found. Abort!")
        print(f"Include '{dbInitFile}' file in the same folder as databaser.py")
        return False

    except sq.Error as e:
        print("Hmm, something went sideways. Abort!")
        print(e)
        return False
    return True


    


def main():
    if not initDB(): return -1
    print ("hello there")
    return

main()

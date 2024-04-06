import sqlite3 as sq
import threading as thread
from datetime import datetime as dt
import os


dbFile = "main.db"
dbInitFile = "db_init.sql"
createData = "createData.sql"


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
        db.commit()
    except FileNotFoundError:
        print(f"'{dbInitFile}' file not found. Abort!")
        print(f"Include '{dbInitFile}' file in the same folder as server.py")
        return False

    except sq.Error as e:
        print("Hmm, something went sideways. Abort!")
        print(e)
        return False
    
    
    return True

def createAdminUser():
    
    try:
        with open(createData, "r") as f:
            command = f.read()
            
            print("executing admin")   
            cur.executescript(command)
            db.commit()
            print("admin created")
        
    except FileNotFoundError:
        print(f"'{createData}' file not found. Abort!")
        print(f"Include '{createData}' file in the same folder as server.py")
        return False

    except sq.Error as e:
        print("Hmm, something went sideways. Abort!")
        print(e)
        return False
    
    
    return True
    


def main():
    if not initDB(): return -1
    print ("Database created succesfully")
    createAdminUser()
    db.close()
    return


main()

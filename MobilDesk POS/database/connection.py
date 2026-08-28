import sqlite3
import os
from pathlib import Path

APP_DATA_DIR = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local")) / "MobilDesk"
APP_DATA_DIR.mkdir(parents=True, exist_ok=True)
DATABASE = APP_DATA_DIR / "mobildesk.db"



def get_connection():

    connection = sqlite3.connect(
        DATABASE,
        timeout=10
    )


    connection.row_factory = sqlite3.Row


    connection.execute(
        "PRAGMA foreign_keys = ON"
    )


    return connection

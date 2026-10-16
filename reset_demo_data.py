"""Optional one-time cleanup for an existing database containing old demo records.

Run from the MealMitra project folder: python reset_demo_data.py
A backup is created first. Type YES to confirm. This removes all donation/activity
records and only the known demo accounts; the admin account and other registered users
are retained. Make a backup and use only if you really want to clear existing records.
"""
import os
import shutil
import sqlite3
import sys
from datetime import datetime

BASE = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(BASE, "instance", "database.db")
DEMO_EMAILS = (
    "donor@mealmitra.com", "volunteer@mealmitra.com", "ngo@mealmitra.com",
    "imran@demo.com", "priya@demo.com", "hope@demo.com", "seva@demo.com",
)

if not os.path.exists(DB):
    sys.exit("No database found. Start the app once first, then run this script if needed.")
if input("This clears ALL donations and related activity. Type YES to continue: ").strip() != "YES":
    sys.exit("Cancelled. Nothing was changed.")

backup = DB.replace(".db", f"_backup_{datetime.now():%Y%m%d_%H%M%S}.db")
shutil.copy2(DB, backup)
conn = sqlite3.connect(DB)
try:
    conn.execute("PRAGMA foreign_keys = ON")
    for table in ("ngo_distributions", "pickup_verification", "volunteer_assignments",
                  "food_analysis", "notifications", "donations"):
        conn.execute(f"DELETE FROM {table}")
    placeholders = ",".join("?" for _ in DEMO_EMAILS)
    conn.execute(f"DELETE FROM users WHERE email IN ({placeholders})", DEMO_EMAILS)
    conn.execute("DELETE FROM sqlite_sequence WHERE name IN ('ngo_distributions','pickup_verification',"
                 "'volunteer_assignments','food_analysis','notifications','donations')")
    conn.commit()
finally:
    conn.close()

for folder in ("static/uploads", "static/qrcodes"):
    path = os.path.join(BASE, folder)
    if os.path.isdir(path):
        for name in os.listdir(path):
            full = os.path.join(path, name)
            if os.path.isfile(full):
                try:
                    os.remove(full)
                except OSError:
                    pass
print(f"Cleanup complete. Database backup: {os.path.basename(backup)}")

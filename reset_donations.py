"""OPTIONAL clean-up for databases that still contain old demo donations.

    python reset_donations.py

Makes a backup copy of instance/database.db, then deletes ALL donations (and their analysis, assignments,
QR records, distributions and notifications) and restarts the donation numbering. User accounts are kept.
"""
import glob
import os
import shutil
import sqlite3
import sys
from datetime import datetime

BASE = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(BASE, "instance", "database.db")

if not os.path.exists(DB):
    sys.exit("No database found yet. Run 'python app.py' once first.")
if input("This deletes ALL donations (users are kept). Type YES to continue: ").strip() != "YES":
    sys.exit("Cancelled. Nothing was changed.")

backup = DB.replace(".db", f"_backup_{datetime.now():%Y%m%d_%H%M%S}.db")
shutil.copy(DB, backup)
conn = sqlite3.connect(DB)
for table in ("ngo_distributions", "pickup_verification", "volunteer_assignments", "food_analysis", "notifications",
              "donations"):
    conn.execute(f"DELETE FROM {table}")
conn.execute("DELETE FROM sqlite_sequence WHERE name IN ('ngo_distributions','pickup_verification',"
             "'volunteer_assignments','food_analysis','notifications','donations')")
conn.commit()
conn.close()
for pattern in ("static/uploads/donation_*", "static/qrcodes/qr_donation_*.png"):
    for path in glob.glob(os.path.join(BASE, pattern)):
        os.remove(path)
print(f"Done. Backup saved as {os.path.basename(backup)}. Donation numbers now start again from 1.")

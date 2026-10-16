"""MealMitra. Start with:  python app.py"""
import secrets
import sqlite3
from datetime import datetime

from flask import Flask, flash, g, redirect, render_template, request, session, url_for
from markupsafe import Markup

from config import Config
from models import models as db
from models.seed import seed_demo
from routes.helpers import is_expired
from routes import admin, auth, common, donor, ngo, public, volunteer
from services import photos
from services.notification_service import unread_count

NAV = {
    "donor": [("donor.dashboard", "Dashboard", "speedometer2"), ("donor.donate", "Donate Food", "plus-circle"),
              ("donor.my_donations", "My Donations", "box-seam"), ("donor.pickup_status", "Pickup Status", "truck"),
              ("common.notifications", "Notifications", "bell"), ("donor.history", "History", "clock-history"),
              ("common.profile", "Profile", "person")],
    "volunteer": [("volunteer.dashboard", "Dashboard", "speedometer2"),
                  ("volunteer.available", "Available Donations", "search-heart"),
                  ("volunteer.pickups", "My Pickups", "truck"), ("volunteer.history", "Pickup History", "clock-history"),
                  ("common.notifications", "Notifications", "bell"), ("common.profile", "Profile", "person")],
    "ngo": [("ngo.dashboard", "Dashboard", "speedometer2"), ("ngo.available", "Available Donations", "search-heart"),
            ("ngo.received", "Received Donations", "box-seam"), ("ngo.distribution", "Distribution", "people"),
            ("ngo.history", "History", "clock-history"), ("common.notifications", "Notifications", "bell"),
            ("common.profile", "Profile", "person")],
    "admin": [("admin.dashboard", "Overview", "speedometer2"), ("admin.donations", "Donation Management", "box-seam"),
              ("admin.volunteers", "Volunteers", "bicycle"), ("admin.ngos", "NGOs", "building"),
              ("admin.tracking", "Food Rescue Tracking", "diagram-3"), ("admin.reports", "Reports & Analytics", "bar-chart"),
              ("admin.users", "User Management", "people"), ("admin.assignments", "Assignments & Pickups", "truck"),
              ("admin.distributions", "Distributions", "heart"),
              ("common.notifications", "Notifications", "bell"), ("common.profile", "Profile", "person")],
}


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    db.init_db(app)
    missing = photos.missing_photos(app.static_folder)
    if missing:
        print(f"[MealMitra] {len(missing)} real photo(s) not added yet - run 'python photo_tool.py' for the checklist.")
    with app.app_context():
        seed_demo(app)

    for blueprint in (public.bp, auth.bp, common.bp, donor.bp, volunteer.bp, ngo.bp, admin.bp):
        app.register_blueprint(blueprint)

    @app.before_request
    def load_user_and_check_csrf():
        g.user = None
        if session.get("user_id"):
            g.user = db.query("SELECT * FROM users WHERE id=?", (session["user_id"],), one=True)
            if g.user is None or not g.user["is_active"]:
                session.clear()
                g.user = None
        if request.method == "POST":
            sent = request.form.get("csrf_token", "")
            if not sent or sent != session.get("csrf_token"):
                flash("Your session expired. Please try again.", "warning")
                return redirect(request.referrer or url_for("public.index"))

    def csrf_token():
        if "csrf_token" not in session:
            session["csrf_token"] = secrets.token_hex(16)
        return session["csrf_token"]

    def img_url(d):
        """The donor's own uploaded photo. If none was uploaded, a neutral placeholder (never a fake food photo)."""
        rel = d["image"] if d["image"] else photos.PLACEHOLDER
        return url_for("static", filename=photos.photo_or_placeholder(app.static_folder, rel))

    def photo_exists(rel):
        return photos.photo_exists(app.static_folder, rel)

    @app.context_processor
    def inject():
        user = g.get("user")
        return {
            "csrf_token": csrf_token,
            "csrf_field": lambda: Markup(f'<input type="hidden" name="csrf_token" value="{csrf_token()}">'),
            "img_url": img_url,
            "photo_exists": photo_exists,
            "current_user": user,
            "unread_count": unread_count(user["id"]) if user else 0,
            "nav_items": NAV.get(user["role"], []) if user else [],
            "STATUS_FLOW": db.STATUS_FLOW,
        }

    @app.template_filter("slug")
    def slug(value):
        return (value or "").lower().replace(" ", "-")

    @app.template_filter("dt")
    def fmt_dt(value):
        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M"):
            try:
                return datetime.strptime(value, fmt).strftime("%d %b, %I:%M %p")
            except (ValueError, TypeError):
                pass
        return value or "-"

    @app.template_filter("place")
    def place(d):
        """Short location text: 'Area, City' (falls back to the full address for older records)."""
        if d["area"] and d["city"]:
            return f"{d['area']}, {d['city']}"
        return d["location"] or "-"

    @app.template_filter("time_left")
    def time_left(deadline):
        """'3h 20m left' / 'Pickup window closed' from the pickup deadline stored with the donation."""
        for fmt in ("%Y-%m-%d %H:%M", "%Y-%m-%d %H:%M:%S"):
            try:
                secs = (datetime.strptime(deadline, fmt) - datetime.now()).total_seconds()
                break
            except (ValueError, TypeError):
                secs = None
        if secs is None:
            return "-"
        if secs <= 0:
            return "Pickup window closed"
        hours, minutes = int(secs // 3600), int(secs % 3600 // 60)
        return (f"{hours // 24}d {hours % 24}h left" if hours >= 24 else f"{hours}h {minutes}m left" if hours else f"{minutes}m left")

    @app.template_filter("window_pct")
    def window_pct(d):
        """How much of the cooked -> pickup-deadline window is still left (0-100), for the availability bar."""
        try:
            start = datetime.strptime(d["cooked_at"], "%Y-%m-%d %H:%M")
            end = datetime.strptime(d["pickup_deadline"], "%Y-%m-%d %H:%M")
            total = (end - start).total_seconds()
            left = (end - datetime.now()).total_seconds()
            return max(0, min(100, round(left * 100 / total))) if total > 0 else 0
        except (ValueError, TypeError, KeyError):
            return 0

    @app.template_filter("expired")
    def expired(deadline):
        """True when the pickup deadline (date and time) has passed."""
        return is_expired(deadline)

    @app.template_filter("qty")
    def fmt_qty(value):
        return f"{value:g}"

    def error_page(code, title, text):
        return render_template("error.html", code=code, title=title, text=text), code

    @app.errorhandler(403)
    def forbidden(e):
        return error_page(403, "Unauthorized", "You do not have permission to open this page.")

    @app.errorhandler(404)
    def not_found(e):
        return error_page(404, "Page not found", "That page or donation does not exist.")

    @app.errorhandler(413)
    def too_large(e):
        return error_page(413, "Image too large", "Uploaded files must be 5 MB or smaller. Go back and choose a smaller image.")

    @app.errorhandler(sqlite3.Error)
    def database_error(e):
        app.logger.exception(e)
        return error_page(500, "Database problem", "Something went wrong while saving data. Please try again.")

    @app.errorhandler(500)
    def server_error(e):
        return error_page(500, "Something went wrong", "An unexpected error occurred. Please try again.")

    return app


app = create_app()

if __name__ == "__main__":
    # Open http://127.0.0.1:5000 in your browser.
    app.run(debug=True)

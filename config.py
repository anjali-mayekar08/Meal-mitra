"""Central configuration. Secrets come from environment variables, never hard-coded."""
import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    # Used to sign session cookies. Set SECRET_KEY in your environment for real deployments.
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-only-change-this-secret")
    DATABASE = os.path.join(BASE_DIR, "instance", "database.db")
    UPLOAD_FOLDER = os.path.join(BASE_DIR, "static", "uploads")
    QR_FOLDER = os.path.join(BASE_DIR, "static", "qrcodes")
    FOOD_IMAGE_FOLDER = os.path.join(BASE_DIR, "static", "images", "foods")
    IMAGE_FOLDER = os.path.join(BASE_DIR, "static", "images")
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024          # 5 MB upload limit
    ALLOWED_IMAGE_EXTENSIONS = {"jpg", "jpeg", "png"}
    # When True, the verification page shows a hint with the code (handy for demos / viva).
    DEMO_MODE = os.environ.get("DEMO_MODE", "1") == "1"

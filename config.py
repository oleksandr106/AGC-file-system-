import os

# ============================================
# KONFIGURACE DMS SYSTÉMU
# ============================================
# Hodnoty lze přepsat environment proměnnými.

# Bezpečnostní nastavení
SECRET_KEY = os.getenv("DMS_SECRET_KEY", "super-secret-key-change-in-production-2027")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("DMS_TOKEN_EXPIRE", "60"))

# Databáze
SQLALCHEMY_DATABASE_URL = os.getenv("DMS_DATABASE_URL", "mysql+pymysql://dms:dms_password@mariadb:3306/dms_db")

# Adresáře pro soubory
UPLOAD_DIR = os.getenv("DMS_UPLOAD_DIR", "uploads")
BACKUP_DIR = os.getenv("DMS_BACKUP_DIR", "backups")

# CORS — seznam povolených originů (čárkou oddělené)
ALLOWED_ORIGINS = os.getenv("DMS_CORS_ORIGINS", "*").split(",")

# Validace souborů
ALLOWED_EXTENSIONS = {".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx", ".txt", ".csv", ".png", ".jpg", ".jpeg"}
MAX_FILE_SIZE_MB = int(os.getenv("DMS_MAX_FILE_SIZE_MB", "50"))

# Výchozí admin účet (pouze pro init_db.py)
DEFAULT_ADMIN_USERNAME = "admin"
DEFAULT_ADMIN_PASSWORD = "admin123"

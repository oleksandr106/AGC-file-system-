"""
Inicializační skript pro DMS databázi.
Spustit jednorázově: python init_db.py
Vytvoří tabulky, výchozího admin uživatele a výchozí kategorie dokumentů.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from passlib.context import CryptContext

from models import Base, User, Document
from config import (
    SQLALCHEMY_DATABASE_URL,
    DEFAULT_ADMIN_USERNAME,
    DEFAULT_ADMIN_PASSWORD,
)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Výchozí kategorie dokumentů odpovídající původním úložištím z prezentace AGC
DEFAULT_CATEGORIES = [
    {
        "title": "__kategorie_rizena_dokumentace",
        "category": "Řízená dokumentace",
        "description": "Návodky, bezpečnostní pokyny, směrnice – původně síťové disky",
    },
    {
        "title": "__kategorie_vyrobni_dokumentace",
        "category": "Výrobní dokumentace",
        "description": "Technologické postupy, výrobní specifikace – původně SharePoint",
    },
    {
        "title": "__kategorie_skoleni_a_podklady",
        "category": "Školení a podklady",
        "description": "Prezentace, tréninkové materiály, plány – původně systém Riscon",
    },
]


def init_database():
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
    )
    Base.metadata.create_all(bind=engine)

    Session = sessionmaker(bind=engine)
    db = Session()

    try:
        # --- Vytvoření výchozího admin účtu ---
        admin = db.query(User).filter(User.username == DEFAULT_ADMIN_USERNAME).first()
        if not admin:
            admin = User(
                username=DEFAULT_ADMIN_USERNAME,
                hashed_password=pwd_context.hash(DEFAULT_ADMIN_PASSWORD),
                role="admin",
            )
            db.add(admin)
            db.commit()
            print(f"✅ Admin účet '{DEFAULT_ADMIN_USERNAME}' vytvořen s heslem: {DEFAULT_ADMIN_PASSWORD}")
        else:
            print(f"ℹ️  Admin účet '{DEFAULT_ADMIN_USERNAME}' již existuje, přeskakuji.")

        # --- Vytvoření výchozích kategorií ---
        for cat_info in DEFAULT_CATEGORIES:
            existing = db.query(Document).filter(Document.category == cat_info["category"]).first()
            if not existing:
                print(f"✅ Kategorie '{cat_info['category']}' zaregistrována ({cat_info['description']}).")
            else:
                print(f"ℹ️  Kategorie '{cat_info['category']}' již existuje, přeskakuji.")

    finally:
        db.close()

    print("✅ Databáze inicializována.")


if __name__ == "__main__":
    init_database()


import os
import shutil
import logging
import subprocess
from datetime import datetime, timedelta
from typing import Optional

from fastapi import FastAPI, File, UploadFile, Form, Depends, HTTPException, status, Query
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker, Session
from PyPDF2 import PdfReader
from passlib.context import CryptContext
from jose import JWTError, jwt
import clamd

# Rozšířená extrakce textu – DOCX a XLSX
try:
    from docx import Document as DocxDocument
except ImportError:
    DocxDocument = None

try:
    from openpyxl import load_workbook
except ImportError:
    load_workbook = None

try:
    from pptx import Presentation
except ImportError:
    Presentation = None

from fpdf import FPDF

from models import Base, Document, DocumentVersion, User, Comment
from config import (
    SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES,
    SQLALCHEMY_DATABASE_URL, UPLOAD_DIR, BACKUP_DIR,
    ALLOWED_ORIGINS, ALLOWED_EXTENSIONS, MAX_FILE_SIZE_MB,
    DEFAULT_ADMIN_USERNAME, DEFAULT_ADMIN_PASSWORD,
)

# ============================================
# CLAMAV ANTIVIRUS INITIALIZATION
# ============================================
try:
    clamav_host = os.getenv("CLAMAV_HOST", "127.0.0.1")
    clam_network = clamd.ClamdNetworkSocket(clamav_host, 3310, timeout=15.0)
    clam_network.ping()
    CLAMAV_AVAILABLE = True
except Exception as e:
    CLAMAV_AVAILABLE = False
    print(f"Warning: ClamAV is not available at {os.getenv('CLAMAV_HOST', '127.0.0.1')}:3310 - {e}")

# ============================================
# LOGGING
# ============================================
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("dms")

# ============================================
# DATABÁZE
# ============================================
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base.metadata.create_all(bind=engine)

# ============================================
# INICIALIZACE ADMIN ÚČTU (pro jednoduchost prototypu)
# ============================================
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/token")

import hashlib

db_init = SessionLocal()
try:
    admin_user = db_init.query(User).filter(User.username == DEFAULT_ADMIN_USERNAME).first()
    
    # Nasimulovat client-side SHA-256 hash z frontendu, než ho zašifrujeme bcryptem
    frontend_hash = hashlib.sha256(DEFAULT_ADMIN_PASSWORD.encode()).hexdigest()
    
    if not admin_user:
        admin_user = User(
            username=DEFAULT_ADMIN_USERNAME,
            hashed_password=pwd_context.hash(frontend_hash),
            role="admin",
        )
        db_init.add(admin_user)
        db_init.commit()
        logger.info(f"Admin účet '{DEFAULT_ADMIN_USERNAME}' vytvořen (s novým hashováním).")
    else:
        # Vynucená aktualizace hesla na nové hashování (aby se šlo přihlásit po úpravě frontendu)
        admin_user.hashed_password = pwd_context.hash(frontend_hash)
        db_init.commit()
        logger.info(f"Admin účet '{DEFAULT_ADMIN_USERNAME}' aktualizován (přechod na client-side hashing).")
finally:
    db_init.close()

# ============================================
# FASTAPI APP
# ============================================
app = FastAPI(title="AGC Technowizz 2027 — DMS")

# Složky pro data
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(BACKUP_DIR, exist_ok=True)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def add_security_headers(request, call_next):
    response = await call_next(request)
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; font-src 'self' data:; img-src 'self' data:; frame-src 'self' data: blob:;"
    return response


# ============================================
# POMOCNÉ FUNKCE
# ============================================
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Nelze ověřit přihlašovací údaje",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise credentials_exception
    return user


def require_admin(current_user: User = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Nedostatečná oprávnění. Tuto akci může provést pouze administrátor.",
        )
    return current_user


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire, "role": data.get("role", "user")})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def validate_file_extension(filename: str):
    ext = os.path.splitext(filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Nepodporovaný typ souboru '{ext}'. Povolené: {', '.join(sorted(ALLOWED_EXTENSIONS))}",
        )
    return ext


# Platné stavy dokumentu
VALID_STATUSES = {"DRAFT", "PENDING_APPROVAL", "APPROVED", "ARCHIVED"}


def extract_text_from_file(file_path: str, file_extension: str) -> str:
    """
    Univerzální extrakce textu ze souborů pro fulltextové vyhledávání.
    Podporuje: .pdf, .docx, .xlsx / .xls
    """
    extracted_text = ""
    ext = file_extension.lower()

    if ext == ".pdf":
        try:
            reader = PdfReader(file_path)
            for page in reader.pages:
                text = page.extract_text()
                if text:
                    extracted_text += text + " "
        except Exception as e:
            logger.warning(f"Nelze extrahovat text z PDF '{file_path}': {e}")

    elif ext == ".docx":
        if DocxDocument is None:
            logger.warning("Knihovna python-docx není nainstalována – přeskakuji extrakci DOCX.")
        else:
            try:
                doc = DocxDocument(file_path)
                for para in doc.paragraphs:
                    if para.text:
                        extracted_text += para.text + " "
            except Exception as e:
                logger.warning(f"Nelze extrahovat text z DOCX '{file_path}': {e}")

    elif ext in (".xlsx", ".xls"):
        if load_workbook is None:
            logger.warning("Knihovna openpyxl není nainstalována – přeskakuji extrakci XLSX.")
        else:
            try:
                wb = load_workbook(file_path, read_only=True, data_only=True)
                for sheet in wb.worksheets:
                    for row in sheet.iter_rows(values_only=True):
                        for cell in row:
                            if cell is not None:
                                extracted_text += str(cell) + " "
                wb.close()
            except Exception as e:
                logger.warning(f"Nelze extrahovat text z XLSX '{file_path}': {e}")

    elif ext in (".pptx", ".ppt"):
        if Presentation is None:
            logger.warning("Knihovna python-pptx není nainstalována – přeskakuji extrakci PPTX.")
        else:
            try:
                prs = Presentation(file_path)
                for slide in prs.slides:
                    for shape in slide.shapes:
                        if hasattr(shape, "text"):
                            extracted_text += shape.text + " "
            except Exception as e:
                logger.warning(f"Nelze extrahovat text z PPTX '{file_path}': {e}")

    return extracted_text.strip()


# ============================================
# AUTH ENDPOINTS
# ============================================
@app.post("/api/token")
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == form_data.username).first()
    if not user or not pwd_context.verify(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Nesprávné jméno nebo heslo",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(
        data={"sub": user.username, "role": user.role},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    logger.info(f"Uživatel '{user.username}' se přihlásil.")
    return {"access_token": access_token, "token_type": "bearer", "role": user.role}


# ============================================
# DOCUMENT ENDPOINTS
# ============================================
@app.post("/api/upload")
async def upload_document(
    title: str = Form(...),
    category: str = Form(...),
    version_number: float = Form(...),
    file: UploadFile = File(...),
    doc_status: str = Form("APPROVED"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    file_ext = validate_file_extension(file.filename)

    # Validace stavu
    if doc_status not in VALID_STATUSES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Neplatný stav '{doc_status}'. Povolené: {', '.join(sorted(VALID_STATUSES))}",
        )

    safe_title = title.replace(" ", "_").replace("/", "_")
    saved_filename = f"{safe_title}_v{version_number}_{datetime.now().strftime('%Y%m%d%H%M%S')}{file_ext}"
    file_path = os.path.join(UPLOAD_DIR, saved_filename)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Kontrola velikosti souboru
    file_size = os.path.getsize(file_path)
    if file_size > MAX_FILE_SIZE_MB * 1024 * 1024:
        os.remove(file_path)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Soubor je příliš velký. Maximum je {MAX_FILE_SIZE_MB} MB.",
        )

    # Antivirová kontrola (ClamAV)
    if CLAMAV_AVAILABLE:
        try:
            scan_result = clam_network.instream(open(file_path, "rb"))
            if scan_result and scan_result.get("stream") and scan_result["stream"][0] == "FOUND":
                virus_name = scan_result["stream"][1]
                os.remove(file_path)
                logger.warning(f"Zablokováno nahrávání souboru s virem: {virus_name}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Nahrávání zablokováno. Byl detekován malware: {virus_name}",
                )
        except Exception as e:
            logger.error(f"Chyba při antivirové kontrole: {e}")
            # Můžete se rozhodnout soubor smazat nebo povolit, pokud antivirus selhal
            pass

    # Extrakce textu z dokumentu (PDF, DOCX, XLSX)
    extracted_text = extract_text_from_file(file_path, file_ext)

    # Najdi nebo vytvoř dokument
    document = db.query(Document).filter(Document.title == title).first()
    if not document:
        document = Document(title=title, category=category, status=doc_status)
        db.add(document)
        db.commit()
        db.refresh(document)
    else:
        # Pokud není administrátor, nemůže měnit stav na jiný než existující (pokud není admin)
        if current_user.role != "admin" and document.status != doc_status:
            os.remove(file_path)
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Nemáte oprávnění měnit stav existujícího dokumentu.",
            )
        
        document.category = category
        if current_user.role == "admin":
            document.status = doc_status
        db.commit()

    new_version = DocumentVersion(
        document_id=document.id,
        version_number=version_number,
        file_path=file_path,
        extracted_text=extracted_text,
        uploaded_by=current_user.username,
    )
    db.add(new_version)
    db.commit()

    logger.info(f"Uživatel '{current_user.username}' nahrál dokument '{title}' v{version_number} [stav: {doc_status}].")
    return {"message": f"Dokument '{title}' verze {version_number} byl úspěšně uložen."}


@app.get("/api/search")
def search_documents(
    q: str = "",
    category: str = "",
    doc_status: str = "",
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(Document)

    if category:
        query = query.filter(Document.category == category)

    if doc_status:
        query = query.filter(Document.status == doc_status)
        
    # Obyčejný uživatel vidí pouze schválené dokumenty
    if current_user.role != "admin":
        query = query.filter(Document.status == "APPROVED")

    docs = query.all()
    results = []

    for d in docs:
        latest_version = (
            db.query(DocumentVersion)
            .filter(DocumentVersion.document_id == d.id)
            .order_by(DocumentVersion.version_number.desc())
            .first()
        )
        if not latest_version:
            continue

        matches = False
        if not q:
            matches = True
        else:
            q_low = q.lower()
            in_title = q_low in d.title.lower()
            in_cat = q_low in d.category.lower()
            in_text = latest_version.extracted_text and q_low in latest_version.extracted_text.lower()
            if in_title or in_cat or in_text:
                matches = True

        if matches:
            results.append({
                "document_id": d.id,
                "version_id": latest_version.id,
                "title": d.title,
                "category": d.category,
                "status": d.status or "APPROVED",
                "latest_version": latest_version.version_number,
                "uploaded_at": latest_version.uploaded_at,
                "uploaded_by": latest_version.uploaded_by or "–",
            })

    # Stránkování
    total = len(results)
    start = (page - 1) * per_page
    end = start + per_page
    paginated = results[start:end]

    return {
        "documents": paginated,
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": max(1, (total + per_page - 1) // per_page),
    }


@app.get("/api/download/{version_id}")
def download_document(version_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    version = db.query(DocumentVersion).filter(DocumentVersion.id == version_id).first()
    if not version:
        raise HTTPException(status_code=404, detail="Verze dokumentu nenalezena")

    if not os.path.exists(version.file_path):
        raise HTTPException(status_code=404, detail="Soubor na disku neexistuje")

    document = db.query(Document).filter(Document.id == version.document_id).first()
    
    # Běžný uživatel může stahovat jen APPROVED
    if current_user.role != "admin" and document.status != "APPROVED":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Nemáte oprávnění stahovat neschválený dokument."
        )

    file_ext = os.path.splitext(version.file_path)[1]
    download_name = f"{document.title}_v{version.version_number}{file_ext}"

    return FileResponse(path=version.file_path, filename=download_name)


@app.delete("/api/documents/{document_id}")
def delete_document(document_id: int, db: Session = Depends(get_db), current_user: User = Depends(require_admin)):
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Dokument nenalezen")

    # Smazat fyzické soubory všech verzí
    versions = db.query(DocumentVersion).filter(DocumentVersion.document_id == document.id).all()
    for v in versions:
        if os.path.exists(v.file_path):
            try:
                os.remove(v.file_path)
            except OSError as e:
                logger.warning(f"Nelze smazat soubor '{v.file_path}': {e}")

    db.delete(document)
    db.commit()

    logger.info(f"Admin '{current_user.username}' smazal dokument '{document.title}' (ID: {document_id}).")
    return {"message": f"Dokument '{document.title}' a všechny jeho verze byly smazány."}


@app.patch("/api/documents/{document_id}/status")
def update_document_status(
    document_id: int,
    new_status: str = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Změní stav/workflow dokumentu (pouze admin)."""
    if new_status not in VALID_STATUSES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Neplatný stav '{new_status}'. Povolené: {', '.join(sorted(VALID_STATUSES))}",
        )

    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Dokument nenalezen")

    old_status = document.status
    document.status = new_status
    db.commit()

    logger.info(f"Admin '{current_user.username}' změnil stav dokumentu '{document.title}' z '{old_status}' na '{new_status}'.")
    return {"message": f"Stav dokumentu '{document.title}' změněn na '{new_status}'."}


@app.get("/api/documents/{document_id}/versions")
def get_document_versions(document_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Dokument nenalezen")

    if current_user.role != "admin" and document.status != "APPROVED":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Nedostatečná oprávnění")

    versions = (
        db.query(DocumentVersion)
        .filter(DocumentVersion.document_id == document_id)
        .order_by(DocumentVersion.version_number.desc())
        .all()
    )

    return {
        "document_title": document.title,
        "versions": [
            {
                "id": v.id,
                "version_number": v.version_number,
                "uploaded_at": v.uploaded_at,
                "uploaded_by": v.uploaded_by or "–",
            }
            for v in versions
        ],
    }


@app.get("/api/recent")
def get_recent_documents(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # Omezíme i recent docs pro usery na APPROVED
    if current_user.role != "admin":
        recent_versions = (
            db.query(DocumentVersion)
            .join(Document)
            .filter(Document.status == "APPROVED")
            .order_by(DocumentVersion.uploaded_at.desc())
            .limit(5)
            .all()
        )
    else:
        recent_versions = (
            db.query(DocumentVersion)
            .order_by(DocumentVersion.uploaded_at.desc())
            .limit(5)
            .all()
        )

    results = []
    for v in recent_versions:
        doc = db.query(Document).filter(Document.id == v.document_id).first()
        if doc:
            results.append({
                "document_id": doc.id,
                "version_id": v.id,
                "title": doc.title,
                "category": doc.category,
                "status": doc.status or "APPROVED",
                "version_number": v.version_number,
                "uploaded_at": v.uploaded_at,
                "uploaded_by": v.uploaded_by or "–",
            })

    return results


# ============================================
# COMMENTS ENDPOINTS
# ============================================
@app.get("/api/documents/{document_id}/comments")
def get_comments(document_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Dokument nenalezen")
    
    if current_user.role != "admin" and document.status != "APPROVED":
        raise HTTPException(status_code=403, detail="Nedostatečná oprávnění")

    comments = db.query(Comment).filter(Comment.document_id == document_id).order_by(Comment.created_at.asc()).all()
    return [{"id": c.id, "author": c.author, "text": c.text, "created_at": c.created_at} for c in comments]

@app.post("/api/documents/{document_id}/comments")
def add_comment(
    document_id: int,
    text: str = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Dokument nenalezen")
    
    new_comment = Comment(document_id=document.id, author=current_user.username, text=text)
    db.add(new_comment)
    db.commit()
    logger.info(f"Uživatel '{current_user.username}' přidal komentář k dokumentu '{document.title}'.")
    return {"message": "Komentář přidán"}

# ============================================
# DIGITALIZATION (PDF GENERATION) ENDPOINT
# ============================================
@app.post("/api/generate_pdf")
def generate_pdf(
    title: str = Form(...),
    category: str = Form(...),
    content: str = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Generování PDF z poskytnutého obsahu
    pdf = FPDF()
    pdf.add_page()
    # Add a Unicode font (DejaVu) to support Czech characters
    # But since we might not have a TTF file on the server easily, 
    # we'll try to use a standard font or handle latin1 encoding for simplicity in prototype
    pdf.set_font("Arial", size=12)
    # Odstraníme diakritiku, aby nám nepadalo generování (zjednodušení pro FPDF bez unicode fontu)
    import unicodedata
    normalized_title = unicodedata.normalize('NFKD', title).encode('ASCII', 'ignore').decode('utf-8')
    normalized_content = unicodedata.normalize('NFKD', content).encode('ASCII', 'ignore').decode('utf-8')
    
    pdf.cell(200, 10, text=f"Formular: {normalized_title}", ln=True, align='C')
    pdf.ln(10)
    pdf.multi_cell(0, 10, text=normalized_content)
    
    safe_title = title.replace(" ", "_").replace("/", "_")
    saved_filename = f"{safe_title}_generated_{datetime.now().strftime('%Y%m%d%H%M%S')}.pdf"
    file_path = os.path.join(UPLOAD_DIR, saved_filename)
    
    pdf.output(file_path)
    
    # Uložit do databáze jako klasický dokument (verze 1.0)
    document = Document(title=title, category=category, status="PENDING_APPROVAL")
    db.add(document)
    db.commit()
    db.refresh(document)
    
    new_version = DocumentVersion(
        document_id=document.id,
        version_number=1.0,
        file_path=file_path,
        extracted_text=normalized_content,
        uploaded_by=current_user.username,
    )
    db.add(new_version)
    db.commit()
    
    logger.info(f"Uživatel '{current_user.username}' vygeneroval digitální formulář '{title}'.")
    return {"message": f"Digitální formulář '{title}' byl vygenerován a čeká na schválení."}

# ============================================
# STATS ENDPOINT
# ============================================
@app.get("/api/stats")
def get_stats(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    total_docs = db.query(Document).count()
    total_versions = db.query(DocumentVersion).count()
    total_users = db.query(User).count()

    # Kategorie s počty
    categories = (
        db.query(Document.category, func.count(Document.id))
        .group_by(Document.category)
        .all()
    )

    return {
        "total_documents": total_docs,
        "total_versions": total_versions,
        "total_users": total_users,
        "categories": [{"name": cat, "count": count} for cat, count in categories],
    }


# ============================================
# ADMIN — BACKUP
# ============================================
@app.post("/api/backup")
async def create_backup(current_user: User = Depends(require_admin)):
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"dms_backup_{timestamp}.sql"
        backup_path = os.path.join(BACKUP_DIR, backup_filename)
        
        db_url = engine.url
        cmd = [
            "mysqldump",
            f"--host={db_url.host}",
            f"--port={db_url.port or 3306}",
            f"--user={db_url.username}",
            f"--password={db_url.password}",
            "--skip-ssl",
            db_url.database,
        ]
        
        with open(backup_path, "w", encoding="utf-8") as f:
            subprocess.run(cmd, stdout=f, check=True)

        logger.info(f"Admin '{current_user.username}' vytvořil zálohu: {backup_filename}")
        return {"message": "Záloha databáze byla úspěšně vytvořena.", "file": backup_filename}
    except Exception as e:
        logger.error(f"Chyba při vytváření zálohy: {e}")
        raise HTTPException(status_code=500, detail=f"Chyba při vytváření zálohy: {str(e)}")


# ============================================
# ADMIN — SPRÁVA UŽIVATELŮ
# ============================================
@app.get("/api/users")
def list_users(db: Session = Depends(get_db), current_user: User = Depends(require_admin)):
    users = db.query(User).all()
    return [
        {
            "id": u.id,
            "username": u.username,
            "role": u.role,
            "created_at": u.created_at,
        }
        for u in users
    ]


@app.post("/api/users")
def create_user(
    username: str = Form(...),
    password: str = Form(...),
    role: str = Form("user"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    existing = db.query(User).filter(User.username == username).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"Uživatel '{username}' již existuje.")

    if role not in ("admin", "user"):
        raise HTTPException(status_code=400, detail="Role musí být 'admin' nebo 'user'.")

    new_user = User(
        username=username,
        hashed_password=pwd_context.hash(password),
        role=role,
    )
    db.add(new_user)
    db.commit()

    logger.info(f"Admin '{current_user.username}' vytvořil uživatele '{username}' s rolí '{role}'.")
    return {"message": f"Uživatel '{username}' byl úspěšně vytvořen."}


@app.delete("/api/users/{user_id}")
def delete_user(user_id: int, db: Session = Depends(get_db), current_user: User = Depends(require_admin)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Uživatel nenalezen")

    if user.username == "admin":
        raise HTTPException(status_code=400, detail="Výchozí admin účet nelze smazat.")

    if user.id == current_user.id:
        raise HTTPException(status_code=400, detail="Nemůžete smazat svůj vlastní účet.")

    db.delete(user)
    db.commit()

    logger.info(f"Admin '{current_user.username}' smazal uživatele '{user.username}' (ID: {user_id}).")
    return {"message": f"Uživatel '{user.username}' byl smazán."}


# Frontend je nyní oddělen v samostatném kontejneru Nginx. Backend servíruje pouze API.
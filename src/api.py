"""
WasteWisely API Server
FastAPI tabanlı backend - tarama, sınıflandırma ve aksiyon API'leri.
"""
import sys
import os
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import subprocess
import re

# BUG-4 FIX: ensure src/ is on sys.path
_src_dir = Path(__file__).resolve().parent
if str(_src_dir) not in sys.path:
    sys.path.insert(0, str(_src_dir))

from scanner import Scanner
from classifier import Classifier
from actions import Actions

app = FastAPI(
    title="WasteWisely API",
    description="Dijital Atık Denetçisi - Dosya sistemi analiz ve temizlik aracı",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def resolve_frontend_dir(module_path: str | Path | None = None, bundle_root: str | Path | None = None) -> Path | None:
    """Frontend dizinini source veya PyInstaller bundle icinden bulur."""
    source_root = Path(module_path or __file__).resolve().parent.parent
    candidates = []

    active_bundle_root = bundle_root or getattr(sys, "_MEIPASS", None)
    if active_bundle_root:
        candidates.append(Path(active_bundle_root) / "frontend")

    candidates.append(source_root / "frontend")

    for candidate in candidates:
        if candidate.exists():
            return candidate
    return None

# --- State ---
# BUG-6 FIX: Removed global state variables to prevent cross-request leakage



# --- Models ---
class ScanRequest(BaseModel):
    path: str = "."

class ActionRequest(BaseModel):
    target_path: str
    action: str  # "delete" or "archive"
    root_path: str


# --- API Routes ---
@app.get("/api/health")
def health():
    return {"status": "ok", "service": "WasteWisely"}


@app.get("/api/select-directory")
def select_directory():
    """Sistem dizin secme diyalogunu acar."""
    try:
        # Tkinter dialogunu ayri bir surecte calistir (threading cakismalarini onlemek icin)
        script = (
            "import tkinter as tk; "
            "from tkinter import filedialog; "
            "root = tk.Tk(); "
            "root.withdraw(); "
            "root.attributes('-topmost', True); "
            "path = filedialog.askdirectory(); "
            "print(path)"
        )
        path = subprocess.check_output([sys.executable, "-c", script], text=True).strip()
        return {"path": path}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Dizin secme hatasi: {str(e)}")


@app.post("/api/scan")
def run_scan(req: ScanRequest):
    """Belirtilen dizini tarar ve atık analizi yapar."""
    
    path_str = req.path.strip()
    
    # Fix 'c:' -> 'c:\' issue on Windows
    if os.name == 'nt' and re.match(r'^[a-zA-Z]:$', path_str):
        path_str += "\\"

    target = Path(path_str).resolve()
    if not target.exists():
        raise HTTPException(status_code=404, detail=f"Dizin bulunamadı: {req.path}")
    if not target.is_dir():
        raise HTTPException(status_code=400, detail=f"Belirtilen yol bir dizin değil: {req.path}")

    try:
        scanner = Scanner(str(target))
        raw_data = scanner.scan()

        classifier = Classifier(raw_data)
        classifier.classify()
        summary = classifier.get_summary()

        return {
            "success": True,
            "scan_root": str(target),
            "summary": summary,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))





@app.post("/api/action")
def perform_action(req: ActionRequest):
    """Dosya/klasör üzerinde silme veya arşivleme aksiyonu yapar."""
    if req.action not in ("delete", "archive"):
        raise HTTPException(status_code=400, detail="Geçersiz aksiyon. 'delete' veya 'archive' olmalı.")

    actions = Actions(req.root_path)

    if req.action == "delete":
        result = actions.delete(req.target_path)
    else:
        result = actions.archive(req.target_path)

    if not result['success']:
        raise HTTPException(status_code=400, detail=result['message'])

    return result


# --- Static Files (Frontend) ---
frontend_dir = resolve_frontend_dir()
if frontend_dir is not None:
    app.mount("/static", StaticFiles(directory=str(frontend_dir)), name="static")

    @app.get("/")
    def serve_frontend():
        return FileResponse(str(frontend_dir / "index.html"))


if __name__ == "__main__":
    import uvicorn
    print("[*] WasteWisely API baslatiliyor: http://localhost:8000")
    print("[>] Dashboard: http://localhost:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)

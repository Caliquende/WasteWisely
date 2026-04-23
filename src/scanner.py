"""
WasteWisely Scanner Module
Dosya sistemini tarayan ve metadata toplayan motor.
"""
import os
import stat as stat_module
from pathlib import Path
from datetime import datetime


# These directories are "waste candidates" - detected but NOT traversed inside
WASTE_DIR_NAMES = {
    'node_modules', '.venv', 'venv', '__pycache__', '.next',
    'target', 'dist', 'build', '.cache', '.parcel-cache',
    'bower_components', '.gradle', '.dart_tool', 'Pods',
}

# Sensitive file patterns
SENSITIVE_PATTERNS = {
    '.env', '.env.local', '.env.production', '.env.development',
    '.pem', '.key', '.p12', '.pfx', 'id_rsa', 'id_ed25519',
    'credentials.json', 'service-account.json', '.htpasswd',
    'secrets.yaml', 'secrets.yml',
}

# Ghost/junk file patterns
GHOST_PATTERNS = {
    '.ds_store', 'thumbs.db', 'desktop.ini', '.log',
    '.tmp', '.temp', '.swp', '.swo', '~',
}


class Scanner:
    """Dosya sistemini tarayan ve metadata toplayan sinif."""

    def __init__(self, root_path: str):
        self.root_path = Path(root_path).resolve()
        if not self.root_path.exists():
            raise ValueError(f"Dizin bulunamadi: {root_path}")
        if not self.root_path.is_dir():
            raise ValueError(f"Belirtilen yol bir dizin degil: {root_path}")

    def scan(self) -> list[dict]:
        """Dizini tarar ve dosya/klasor metadata listesi doner."""
        results = []
        self._scan_recursive(self.root_path, results)
        return results

    def _scan_recursive(self, path: Path, results: list):
        """Recursive tarama - symlink/junction'lara girmez, waste dizinlerini tespit eder."""
        try:
            entries = sorted(path.iterdir(), key=lambda e: e.name)
        except (PermissionError, FileNotFoundError, OSError):
            return

        for entry in entries:
            # BUG-1 FIX: use lstat (follow_symlinks=False equivalent) to detect
            # symlinks/junctions before deciding to recurse into them.
            try:
                raw_stat = os.stat(str(entry), follow_symlinks=False)
            except (PermissionError, FileNotFoundError, OSError):
                continue

            # If the entry is a symlink or junction, record it but never recurse
            if stat_module.S_ISLNK(raw_stat.st_mode):
                results.append(self._build_entry(entry, raw_stat, is_dir=False))
                continue

            # On Windows, check for reparse points (junctions) via FILE_ATTRIBUTE_REPARSE_POINT
            if hasattr(raw_stat, 'st_file_attributes'):
                FILE_ATTRIBUTE_REPARSE_POINT = 0x400
                if raw_stat.st_file_attributes & FILE_ATTRIBUTE_REPARSE_POINT:
                    results.append(self._build_entry(entry, raw_stat, is_dir=entry.is_dir()))
                    continue

            is_dir = stat_module.S_ISDIR(raw_stat.st_mode)

            # Waste directory detected - record with total size, don't recurse
            if is_dir and entry.name in WASTE_DIR_NAMES:
                results.append(self._build_entry(entry, raw_stat, is_dir=True, calc_size=True))
                continue

            # .git directory - record for repo detection, don't recurse
            if is_dir and entry.name == '.git':
                results.append(self._build_entry(entry, raw_stat, is_dir=True, calc_size=True))
                continue

            if is_dir:
                self._scan_recursive(entry, results)
            else:
                results.append(self._build_entry(entry, raw_stat, is_dir=False))

    def _build_entry(self, entry: Path, stats, is_dir: bool, calc_size: bool = False) -> dict:
        """Bir dosya/klasor icin metadata sozlugu olusturur."""
        size = self._get_dir_size(entry) if (is_dir and calc_size) else stats.st_size
        return {
            'path': str(entry),
            'relative_path': str(entry.relative_to(self.root_path)),
            'name': entry.name,
            'is_dir': is_dir,
            'size': size,
            'last_accessed': datetime.fromtimestamp(stats.st_atime).isoformat(),
            'last_modified': datetime.fromtimestamp(stats.st_mtime).isoformat(),
        }

    @staticmethod
    def _get_dir_size(path: Path) -> int:
        """Bir dizinin toplam boyutunu hesaplar."""
        total = 0
        try:
            for entry in path.rglob('*'):
                try:
                    if entry.is_file():
                        total += entry.stat().st_size
                except (PermissionError, FileNotFoundError, OSError):
                    continue
        except (PermissionError, FileNotFoundError, OSError):
            pass
        return total

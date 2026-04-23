"""
WasteWisely Actions Module
Guvenli silme ve arsivleme islemlerini yoneten modul.
"""
import os
import shutil
import zipfile
from pathlib import Path
from datetime import datetime


class Actions:
    """Dosya/klasor silme ve arsivleme aksiyonlarini yonetir."""

    ARCHIVE_DIR_NAME = '.wastewise_archive'

    def __init__(self, root_path: str):
        self.root_path = Path(root_path).resolve()
        self.archive_dir = self.root_path / self.ARCHIVE_DIR_NAME
        self.log = []

    def _safety_check(self, target: Path) -> str | None:
        """
        Ortak guvenlik kontrolu.
        Sorun varsa hata mesaji, yoksa None doner.
        """
        resolved = target.resolve()

        # BUG-3 FIX: explicitly block deleting/archiving the root itself
        if resolved == self.root_path:
            return 'Guvenlik hatasi: Kok dizinin kendisi hedef alinamaz.'

        # BUG-2 FIX: block targeting the archive dir (would delete its own zip)
        if resolved == self.archive_dir.resolve():
            return 'Guvenlik hatasi: Arsiv dizininin kendisi hedef alinamaz.'

        # Block anything outside root
        try:
            resolved.relative_to(self.root_path)
        except ValueError:
            return 'Guvenlik hatasi: Kok dizin disinda islem yapilaamaz.'

        return None

    def delete(self, target_path: str) -> dict:
        """
        Dosya veya klasoru guvenli sekilde siler.
        Returns: {'success': bool, 'message': str}
        """
        target = Path(target_path)
        if not target.exists():
            return {'success': False, 'message': f'Hedef bulunamadi: {target_path}'}

        err = self._safety_check(target)
        if err:
            return {'success': False, 'message': err}

        try:
            if target.is_dir():
                shutil.rmtree(target)
            else:
                target.unlink()

            entry = {
                'action': 'delete',
                'target': str(target),
                'timestamp': datetime.now().isoformat(),
                'success': True,
            }
            self.log.append(entry)
            return {'success': True, 'message': f'Basariyla silindi: {target_path}'}

        except PermissionError:
            return {'success': False, 'message': f'Izin hatasi: {target_path}'}
        except Exception as e:
            return {'success': False, 'message': f'Silme hatasi: {str(e)}'}

    def archive(self, target_path: str) -> dict:
        """
        Dosya/klasoru zip olarak arsivler, sonra orijinalini siler.
        Returns: {'success': bool, 'message': str, 'archive_path': str}
        """
        target = Path(target_path)
        if not target.exists():
            return {'success': False, 'message': f'Hedef bulunamadi: {target_path}'}

        err = self._safety_check(target)
        if err:
            return {'success': False, 'message': err}

        # BUG-2 FIX: archive dir must be outside the target being archived.
        # Use a sibling temp dir when target contains or IS the archive dir.
        try:
            target.resolve().relative_to(self.archive_dir.resolve())
            # If we get here, target is inside archive_dir - block it
            return {'success': False,
                    'message': 'Guvenlik hatasi: Arsiv dizini icindeki dosyalar hedef alinamaz.'}
        except ValueError:
            pass  # target is NOT inside archive_dir - safe to proceed

        try:
            # Write zip to a location that won't be deleted by rmtree(target)
            self.archive_dir.mkdir(exist_ok=True)

            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            archive_name = f"{target.name}_{timestamp}.zip"
            archive_path = self.archive_dir / archive_name

            with zipfile.ZipFile(archive_path, 'w', zipfile.ZIP_DEFLATED) as zf:
                if target.is_dir():
                    for file in target.rglob('*'):
                        if file.is_file():
                            zf.write(file, file.relative_to(target.parent))
                else:
                    zf.write(target, target.name)

            # Verify the zip was actually written before deleting original
            if not archive_path.exists() or archive_path.stat().st_size == 0:
                return {'success': False,
                        'message': 'Arsiv olusturulamadi, orijinal dosya korundu.'}

            # Remove original after verified archive
            if target.is_dir():
                shutil.rmtree(target)
            else:
                target.unlink()

            entry = {
                'action': 'archive',
                'target': str(target),
                'archive_path': str(archive_path),
                'timestamp': datetime.now().isoformat(),
                'success': True,
            }
            self.log.append(entry)
            return {
                'success': True,
                'message': f'Arsivlendi ve silindi: {target_path}',
                'archive_path': str(archive_path),
            }

        except PermissionError:
            return {'success': False, 'message': f'Izin hatasi: {target_path}'}
        except Exception as e:
            return {'success': False, 'message': f'Arsivleme hatasi: {str(e)}'}

    def get_log(self) -> list:
        """Yapilan tum aksiyonlarin logunu doner."""
        return self.log

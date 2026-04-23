"""
WasteWisely Test Suite - Scanner Tests
"""
import os
import sys
import tempfile
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))
from src.scanner import Scanner


class TestScanner:
    """Scanner modülü için testler."""

    def setup_method(self):
        """Her test için geçici dizin oluştur."""
        self.temp_dir = tempfile.mkdtemp()
        self.test_root = Path(self.temp_dir)

    def teardown_method(self):
        """Geçici dizini temizle."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _create_file(self, relative_path, content="test"):
        fp = self.test_root / relative_path
        fp.parent.mkdir(parents=True, exist_ok=True)
        fp.write_text(content)
        return fp

    def test_scan_empty_directory(self):
        scanner = Scanner(str(self.test_root))
        results = scanner.scan()
        assert results == []

    def test_scan_finds_files(self):
        self._create_file("file1.txt", "hello")
        self._create_file("file2.py", "print('hi')")
        scanner = Scanner(str(self.test_root))
        results = scanner.scan()
        names = [r['name'] for r in results]
        assert "file1.txt" in names
        assert "file2.py" in names

    def test_scan_detects_node_modules(self):
        nm = self.test_root / "node_modules"
        nm.mkdir()
        (nm / "package.json").write_text("{}")
        scanner = Scanner(str(self.test_root))
        results = scanner.scan()
        nm_items = [r for r in results if r['name'] == 'node_modules']
        assert len(nm_items) == 1
        assert nm_items[0]['is_dir'] is True

    def test_scan_detects_venv(self):
        venv = self.test_root / ".venv"
        venv.mkdir()
        (venv / "pyvenv.cfg").write_text("home = /usr")
        scanner = Scanner(str(self.test_root))
        results = scanner.scan()
        venv_items = [r for r in results if r['name'] == '.venv']
        assert len(venv_items) == 1

    def test_scan_detects_git_dir(self):
        git = self.test_root / ".git"
        git.mkdir()
        (git / "HEAD").write_text("ref: refs/heads/main")
        scanner = Scanner(str(self.test_root))
        results = scanner.scan()
        git_items = [r for r in results if r['name'] == '.git']
        assert len(git_items) == 1

    def test_scan_includes_size(self):
        content = "x" * 1000
        self._create_file("big.txt", content)
        scanner = Scanner(str(self.test_root))
        results = scanner.scan()
        item = [r for r in results if r['name'] == 'big.txt'][0]
        assert item['size'] == 1000

    def test_invalid_path_raises(self):
        try:
            Scanner("/nonexistent/path/xyz")
            assert False, "Should have raised ValueError"
        except ValueError:
            pass

    def test_scan_nested_files(self):
        self._create_file("a/b/c/deep.txt", "deep")
        scanner = Scanner(str(self.test_root))
        results = scanner.scan()
        deep = [r for r in results if r['name'] == 'deep.txt']
        assert len(deep) == 1

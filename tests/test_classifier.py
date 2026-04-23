"""
WasteWisely Test Suite - Classifier Tests
"""
import sys
import tempfile
from pathlib import Path
from datetime import datetime, timedelta

sys.path.insert(0, str(Path(__file__).parent.parent))
from src.classifier import Classifier


def _make_item(name, is_dir=False, size=100, days_old=0, path=None):
    """Test verisi oluşturmak için yardımcı."""
    mod_time = datetime.now() - timedelta(days=days_old)
    return {
        'path': path or f'/fake/{name}',
        'relative_path': name,
        'name': name,
        'is_dir': is_dir,
        'size': size,
        'last_accessed': mod_time.isoformat(),
        'last_modified': mod_time.isoformat(),
    }


class TestClassifier:

    def test_classifies_node_modules(self):
        data = [_make_item('node_modules', is_dir=True, size=500_000_000)]
        c = Classifier(data)
        result = c.classify()
        assert len(result['heavy_dependencies']) == 1

    def test_classifies_venv(self):
        data = [_make_item('.venv', is_dir=True, size=200_000_000)]
        c = Classifier(data)
        result = c.classify()
        assert len(result['heavy_dependencies']) == 1

    def test_classifies_env_file(self):
        data = [_make_item('.env', size=256)]
        c = Classifier(data)
        result = c.classify()
        assert len(result['sensitive_leaks']) == 1

    def test_classifies_pem_file(self):
        data = [_make_item('server.pem', size=1024)]
        c = Classifier(data)
        result = c.classify()
        assert len(result['sensitive_leaks']) == 1

    def test_classifies_ghost_files(self):
        data = [
            _make_item('.DS_Store', size=4096),
            _make_item('Thumbs.db', size=8192),
            _make_item('debug.log', size=50000),
        ]
        c = Classifier(data)
        result = c.classify()
        assert len(result['ghost_files']) == 3

    def test_classifies_forgotten_project(self):
        data = [_make_item('.git', is_dir=True, size=1000, days_old=200)]
        c = Classifier(data)
        result = c.classify()
        assert len(result['forgotten_projects']) == 1

    def test_recent_git_not_forgotten(self):
        data = [_make_item('.git', is_dir=True, size=1000, days_old=10)]
        c = Classifier(data)
        result = c.classify()
        assert len(result['forgotten_projects']) == 0

    def test_classifies_large_files(self):
        data = [_make_item('huge.iso', size=600_000_000, days_old=120)]
        c = Classifier(data)
        result = c.classify()
        assert len(result['large_files']) == 1

    def test_summary_counts(self):
        data = [
            _make_item('node_modules', is_dir=True, size=500_000_000),
            _make_item('.env', size=256),
            _make_item('.DS_Store', size=4096),
        ]
        c = Classifier(data)
        c.classify()
        summary = c.get_summary()
        assert summary['total_waste_count'] == 3
        assert summary['categories']['heavy_dependencies']['count'] == 1
        assert summary['categories']['sensitive_leaks']['count'] == 1
        assert summary['categories']['ghost_files']['count'] == 1

    def test_format_size(self):
        assert Classifier._format_size(0) == "0 B"
        assert "KB" in Classifier._format_size(2048)
        assert "MB" in Classifier._format_size(5_000_000)
        assert "GB" in Classifier._format_size(2_000_000_000)

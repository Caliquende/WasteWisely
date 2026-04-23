"""
WasteWisely Classifier Module
Tarama sonuçlarını atık kategorilerine ayıran sınıflandırıcı.
"""
from datetime import datetime, timedelta
import sys
from pathlib import Path

# BUG-4 FIX: ensure src/ is on sys.path
_src_dir = Path(__file__).resolve().parent
if str(_src_dir) not in sys.path:
    sys.path.insert(0, str(_src_dir))

from scanner import WASTE_DIR_NAMES, SENSITIVE_PATTERNS, GHOST_PATTERNS


# Risk levels for each category
RISK_LEVELS = {
    'heavy_dependencies': 'low',       # Yeniden oluşturulabilir, güvenli
    'sensitive_leaks': 'critical',      # Sızan bilgi, acil
    'ghost_files': 'low',              # Sistem kirliliği, zararsız
    'forgotten_projects': 'medium',     # Eski proje, dikkatli silme
    'large_files': 'medium',           # Büyük dosyalar, potansiyel atık
}

# Category display names
CATEGORY_NAMES = {
    'heavy_dependencies': 'Agir Bagimliliklar',
    'sensitive_leaks': 'Hassas Sizintilar',
    'ghost_files': 'Hayalet Dosyalar',
    'forgotten_projects': 'Unutulmus Projeler',
    'large_files': 'Buyuk Dosyalar',
}

# Category icons (for frontend)
CATEGORY_ICONS = {
    'heavy_dependencies': '📦',
    'sensitive_leaks': '🔑',
    'ghost_files': '👻',
    'forgotten_projects': '🕸️',
    'large_files': '💾',
}

LARGE_FILE_THRESHOLD = 500 * 1024 * 1024  # 500 MB
LARGE_FILE_STALE_DAYS = 90


class Classifier:
    """Tarama sonuçlarını atık kategorilerine ayıran sınıf."""

    def __init__(self, scan_data: list[dict], stale_days: int = 180):
        self.scan_data = scan_data
        self.stale_days = stale_days
        self.results = {key: [] for key in RISK_LEVELS}
        self._classified = False

    def classify(self) -> dict:
        """Tüm dosyaları sınıflandır ve kategorize et."""
        now = datetime.now()
        forgotten_cutoff = now - timedelta(days=self.stale_days)
        large_file_cutoff = now - timedelta(days=LARGE_FILE_STALE_DAYS)

        for item in self.scan_data:
            name_lower = item['name'].lower()
            path_lower = item['path'].lower().replace('\\', '/')

            # Skip system files that should never be considered waste
            if item['name'].lower() in ('pagefile.sys', 'hiberfil.sys', 'swapfile.sys'):
                continue

            # 1. Heavy Dependencies (waste directories)
            if item['is_dir'] and item['name'] in WASTE_DIR_NAMES:
                self.results['heavy_dependencies'].append(
                    self._enrich(item, 'heavy_dependencies',
                                 f"Yeniden oluşturulabilir bağımlılık klasörü: {item['name']}")
                )
                continue

            # 2. Sensitive Leaks
            if not item['is_dir'] and self._is_sensitive(name_lower):
                self.results['sensitive_leaks'].append(
                    self._enrich(item, 'sensitive_leaks',
                                 f"Potansiyel hassas bilgi içeren dosya: {item['name']}")
                )
                continue

            # 3. Ghost Files
            if not item['is_dir'] and self._is_ghost(name_lower):
                self.results['ghost_files'].append(
                    self._enrich(item, 'ghost_files',
                                 f"Sistem tarafından oluşturulmuş gereksiz dosya: {item['name']}")
                )
                continue

            # 4. Forgotten Projects (.git directories that are stale)
            if item['is_dir'] and item['name'] == '.git':
                mod_time = datetime.fromisoformat(item['last_modified'])
                if mod_time < forgotten_cutoff:
                    parent_path = str(item['path']).rsplit('.git', 1)[0].rstrip('/\\')
                    parent_name = Path(parent_path).name or parent_path
                    enriched = self._enrich(item, 'forgotten_projects',
                                     f"{self.stale_days} gündür dokunulmamış proje",
                                     override_path=parent_path)
                    enriched['name'] = f"{parent_name} (Proje)"
                    self.results['forgotten_projects'].append(enriched)
                continue

            # 5. Large Files (Only if stale)
            if not item['is_dir'] and item['size'] >= LARGE_FILE_THRESHOLD:
                mod_time = datetime.fromisoformat(item['last_modified'])
                if mod_time < large_file_cutoff:
                    self.results['large_files'].append(
                        self._enrich(item, 'large_files',
                                     f"Eski ve büyük dosya ({LARGE_FILE_STALE_DAYS}+ gün): {self._format_size(item['size'])}")
                    )

        self._classified = True
        return self.results

    def get_summary(self) -> dict:
        """Tüm kategoriler için özet istatistikler döner."""
        if not self._classified:
            self.classify()

        total_waste_size = 0
        total_waste_count = 0
        categories = {}

        for cat_key, items in self.results.items():
            total_size = sum(i['size'] for i in items)
            total_waste_size += total_size
            total_waste_count += len(items)
            categories[cat_key] = {
                'name': CATEGORY_NAMES[cat_key],
                'icon': CATEGORY_ICONS[cat_key],
                'risk': RISK_LEVELS[cat_key],
                'count': len(items),
                'total_size': total_size,
                'total_size_human': self._format_size(total_size),
                'items': items,
            }

        return {
            'total_items_scanned': len(self.scan_data),
            'total_waste_count': total_waste_count,
            'total_waste_size': total_waste_size,
            'total_waste_size_human': self._format_size(total_waste_size),
            'categories': categories,
        }

    def _enrich(self, item: dict, category: str, reason: str,
                override_path: str = None) -> dict:
        """Bir öğeyi kategori bilgileriyle zenginleştirir."""
        enriched = dict(item)
        enriched['category'] = category
        enriched['category_name'] = CATEGORY_NAMES[category]
        enriched['risk'] = RISK_LEVELS[category]
        enriched['reason'] = reason
        enriched['size_human'] = self._format_size(item['size'])
        if override_path:
            enriched['action_path'] = override_path
        else:
            enriched['action_path'] = item['path']
        return enriched

    @staticmethod
    def _is_sensitive(name: str) -> bool:
        """Dosya adının hassas pattern'e uyup uymadığını kontrol eder."""
        for pattern in SENSITIVE_PATTERNS:
            if name == pattern or name.endswith(pattern):
                return True
        return False

    @staticmethod
    def _is_ghost(name: str) -> bool:
        """Dosya adının ghost/junk pattern'e uyup uymadığını kontrol eder."""
        for pattern in GHOST_PATTERNS:
            if name == pattern or name.endswith(pattern):
                return True
        return False

    @staticmethod
    def _format_size(size_bytes: int) -> str:
        """Byte değerini insan okunabilir formata çevirir."""
        if size_bytes == 0:
            return "0 B"
        units = ['B', 'KB', 'MB', 'GB', 'TB']
        i = 0
        size = float(size_bytes)
        while size >= 1024 and i < len(units) - 1:
            size /= 1024
            i += 1
        return f"{size:.1f} {units[i]}"

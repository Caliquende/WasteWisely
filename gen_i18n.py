import json
import codecs

langs = {
    'tr': 'Türkçe', 'en': 'English', 'de': 'Deutsch', 'es': 'Español', 'fr': 'Français',
    'it': 'Italiano', 'ru': 'Русский', 'zh': '中文', 'ja': '日本語', 'ar': 'العربية'
}

keys = {
    "app_title": ["WasteWisely", "WasteWisely", "WasteWisely", "WasteWisely", "WasteWisely", "WasteWisely", "WasteWisely", "WasteWisely", "WasteWisely", "WasteWisely"],
    "nav_dashboard": ["📊 Dashboard", "📊 Dashboard", "📊 Dashboard", "📊 Panel", "📊 Tableau de Bord", "📊 Cruscotto", "📊 Панель", "📊 仪表板", "📊 ダッシュボード", "📊 لوحة القيادة"],
    "nav_scan": ["🔍 Tarama", "🔍 Scan", "🔍 Scannen", "🔍 Escanear", "🔍 Analyser", "🔍 Scansione", "🔍 Сканировать", "🔍 扫描", "🔍 スキャン", "🔍 مسح"],
    "nav_results": ["📋 Sonuçlar", "📋 Results", "📋 Ergebnisse", "📋 Resultados", "📋 Résultats", "📋 Risultati", "📋 Результаты", "📋 结果", "📋 結果", "📋 النتائج"],
    "nav_history": ["🕐 Geçmiş", "🕐 History", "🕐 Verlauf", "🕐 Historial", "🕐 Historique", "🕐 Cronologia", "🕐 История", "🕐 历史记录", "🕐 履歴", "🕐 السجل"],
    "welcome_title": ["WasteWisely'a Hoş Geldin", "Welcome to WasteWisely", "Willkommen bei WasteWisely", "Bienvenido a WasteWisely", "Bienvenue sur WasteWisely", "Benvenuto in WasteWisely", "Добро пожаловать в WasteWisely", "欢迎来到 WasteWisely", "WasteWiselyへようこそ", "مرحبًا بك في WasteWisely"],
    "welcome_desc": ["Dijital atıklarını tespit etmek için bir tarama başlat.", "Start a scan to detect your digital waste.", "Starten Sie einen Scan, um Ihren digitalen Müll zu erkennen.", "Inicie un escaneo para detectar su basura digital.", "Lancez une analyse pour détecter vos déchets numériques.", "Avvia una scansione per rilevare i tuoi rifiuti digitali.", "Начните сканирование, чтобы обнаружить цифровой мусор.", "开始扫描以检测您的数字垃圾。", "スキャンを開始してデジタルゴミを検出します。", "ابدأ مسحًا لاكتشاف النفايات الرقمية الخاصة بك."],
    "start_scan": ["İlk Taramayı Başlat", "Start First Scan", "Ersten Scan starten", "Iniciar primer escaneo", "Lancer la première analyse", "Avvia la prima scansione", "Начать первое сканирование", "开始首次扫描", "最初のスキャンを開始", "ابدأ المسح الأول"],
    "stat_scanned": ["Taranan Öğe", "Scanned Items", "Gescannte Elemente", "Elementos escaneados", "Éléments analysés", "Elementi scansionati", "Отсканированные элементы", "已扫描项目", "スキャンされたアイテム", "العناصر الممسوحة"],
    "stat_waste": ["Atık Tespit Edildi", "Waste Detected", "Müll Erkannt", "Basura detectada", "Déchets détectés", "Rifiuti rilevati", "Мусор обнаружен", "检测到垃圾", "ゴミが検出されました", "تم اكتشاف نفايات"],
    "stat_size": ["Kazanılabilir Alan", "Recoverable Space", "Wiederherstellbarer Platz", "Espacio recuperable", "Espace récupérable", "Spazio recuperabile", "Восстанавливаемое пространство", "可恢复空间", "回復可能なスペース", "المساحة القابلة للاسترداد"],
    "stat_risk": ["Kritik Uyarı", "Critical Warning", "Kritische Warnung", "Advertencia crítica", "Avertissement critique", "Avviso critico", "Критическое предупреждение", "严重警告", "重大な警告", "تحذير حرج"],
    "chart_categories": ["Kategori Dağılımı", "Category Distribution", "Kategorieverteilung", "Distribución de categorías", "Répartition par catégorie", "Distribuzione delle categorie", "Распределение по категориям", "类别分布", "カテゴリ分布", "توزيع الفئات"],
    "chart_treemap": ["Alan Haritası", "Treemap", "Treemap", "Treemap", "Treemap", "Treemap", "Карта областей", "树状图", "ツリーマップ", "خريطة المساحة"],
    "waste_categories": ["Atık Kategorileri", "Waste Categories", "Müllkategorien", "Categorías de basura", "Catégories de déchets", "Categorie di rifiuti", "Категории мусора", "垃圾类别", "ゴミのカテゴリ", "فئات النفايات"],
    "rescan": ["↻ Yeniden Tara", "↻ Rescan", "↻ Erneut scannen", "↻ Volver a escanear", "↻ Réanalyser", "↻ Nuova scansione", "↻ Пересканировать", "↻ 重新扫描", "↻ 再スキャン", "↻ إعادة المسح"],
    "new_scan": ["🔍 Yeni Tarama", "🔍 New Scan", "🔍 Neuer Scan", "🔍 Nuevo escaneo", "🔍 Nouvelle analyse", "🔍 Nuova scansione", "🔍 Новое сканирование", "🔍 新扫描", "🔍 新しいスキャン", "🔍 مسح جديد"],
    "scan_path": ["Taranacak Dizin", "Directory to Scan", "Zu scannendes Verzeichnis", "Directorio a escanear", "Répertoire à analyser", "Directory da scansionare", "Каталог для сканирования", "要扫描的目录", "スキャンするディレクトリ", "الدليل المراد مسحه"],
    "scan_path_placeholder": ["C:\\Projeler veya ~/Desktop", "C:\\Projects or ~/Desktop", "C:\\Projekte oder ~/Desktop", "C:\\Proyectos o ~/Desktop", "C:\\Projets ou ~/Desktop", "C:\\Progetti o ~/Desktop", "C:\\Проекты или ~/Desktop", "C:\\项目 或 ~/Desktop", "C:\\プロジェクト または ~/Desktop", "C:\\المشاريع أو ~/Desktop"],
    "scan_btn": ["Taramayı Başlat", "Start Scan", "Scan Starten", "Iniciar Escaneo", "Lancer l'Analyse", "Avvia Scansione", "Начать сканирование", "开始扫描", "スキャン開始", "بدء المسح"],
    "scan_hint": ["Tam dizin yolunu girin.", "Enter the full directory path.", "Geben Sie den vollständigen Verzeichnispfad ein.", "Ingrese la ruta completa del directorio.", "Entrez le chemin complet du répertoire.", "Inserisci il percorso completo della directory.", "Введите полный путь к каталогу.", "输入完整的目录路径。", "完全なディレクトリパスを入力してください。", "أدخل مسار الدليل بالكامل."],
    "scanning": ["Tarama başlatılıyor...", "Starting scan...", "Scan wird gestartet...", "Iniciando escaneo...", "Lancement de l'analyse...", "Avvio della scansione...", "Запуск сканирования...", "正在开始扫描...", "スキャンを開始しています...", "بدء المسح..."],
    "quick_scan": ["⚡ Hızlı Tarama", "⚡ Quick Scan", "⚡ Schneller Scan", "⚡ Escaneo rápido", "⚡ Analyse rapide", "⚡ Scansione rapida", "⚡ Быстрое сканирование", "⚡ 快速扫描", "⚡ クイックスキャン", "⚡ مسح سريع"],
    "path_work": ["Çalışma Dizini", "Working Directory", "Arbeitsverzeichnis", "Directorio de trabajo", "Répertoire de travail", "Directory di lavoro", "Рабочий каталог", "工作目录", "作業ディレクトリ", "دليل العمل"],
    "path_desktop": ["Masaüstü", "Desktop", "Desktop", "Escritorio", "Bureau", "Desktop", "Рабочий стол", "桌面", "デスクトップ", "سطح المكتب"],
    "path_downloads": ["İndirilenler", "Downloads", "Downloads", "Descargas", "Téléchargements", "Download", "Загрузки", "下载", "ダウンロード", "التنزيلات"],
    "no_results": ["Henüz sonuç yok", "No results yet", "Noch keine Ergebnisse", "Aún no hay resultados", "Pas encore de résultats", "Ancora nessun risultato", "Пока нет результатов", "暂无结果", "まだ結果はありません", "لا توجد نتائج بعد"],
    "no_results_desc": ["Önce bir tarama başlat.", "Start a scan first.", "Starten Sie zuerst einen Scan.", "Inicie un escaneo primero.", "Lancez d'abord une analyse.", "Avvia prima una scansione.", "Сначала начните сканирование.", "请先开始扫描。", "最初にスキャンを開始してください。", "ابدأ مسحًا أولاً."],
    "filter_all": ["Tümü", "All", "Alle", "Todo", "Tout", "Tutto", "Все", "全部", "すべて", "الكل"],
    "filter_dependencies": ["📦 Bağımlılıklar", "📦 Dependencies", "📦 Abhängigkeiten", "📦 Dependencias", "📦 Dépendances", "📦 Dipendenze", "📦 Зависимости", "📦 依赖", "📦 依存関係", "📦 التبعيات"],
    "filter_sensitive": ["🔑 Hassas", "🔑 Sensitive", "🔑 Sensibel", "🔑 Sensible", "🔑 Sensible", "🔑 Sensibile", "🔑 Конфиденциальные", "🔑 敏感", "🔑 機密", "🔑 حساس"],
    "filter_ghost": ["👻 Hayalet", "👻 Ghost", "👻 Geist", "👻 Fantasma", "👻 Fantôme", "👻 Fantasma", "👻 Призрак", "👻 幽灵", "👻 ゴースト", "👻 شبح"],
    "filter_forgotten": ["🕸️ Unutulmuş", "🕸️ Forgotten", "🕸️ Vergessen", "🕸️ Olvidado", "🕸️ Oublié", "🕸️ Dimenticato", "🕸️ Забытые", "🕸️ 遗忘", "🕸️ 忘れられた", "🕸️ منسية"],
    "filter_large": ["💾 Büyük", "💾 Large", "💾 Groß", "💾 Grande", "💾 Grand", "💾 Grande", "💾 Большие", "💾 大", "💾 大きい", "💾 كبير"],
    "bulk_clean": ["💥 Tüm Atıkları Temizle", "💥 Clean All Waste", "💥 Allen Müll Bereinigen", "💥 Limpiar Toda la Basura", "💥 Nettoyer Tous les Déchets", "💥 Pulisci Tutti i Rifiuti", "💥 Очистить весь мусор", "💥 清除所有垃圾", "💥 全てのゴミを消去", "💥 تنظيف جميع النفايات"],
    "history_title": ["🕐 İşlem Geçmişi", "🕐 Action History", "🕐 Aktionsverlauf", "🕐 Historial de acciones", "🕐 Historique des actions", "🕐 Cronologia azioni", "🕐 История действий", "🕐 操作历史", "🕐 アクション履歴", "🕐 سجل الإجراءات"],
    "no_history": ["Henüz işlem yapılmadı.", "No actions taken yet.", "Noch keine Aktionen durchgeführt.", "Aún no se han tomado acciones.", "Aucune action effectuée.", "Nessuna azione intrapresa.", "Действия еще не предпринимались.", "尚未执行任何操作。", "まだアクションは実行されていません。", "لم يتم اتخاذ أي إجراءات بعد."],
    "modal_title": ["İşlem Onayı", "Action Confirmation", "Aktionsbestätigung", "Confirmación de acción", "Confirmation d'action", "Conferma azione", "Подтверждение действия", "操作确认", "アクション確認", "تأكيد الإجراء"],
    "cancel": ["İptal", "Cancel", "Abbrechen", "Cancelar", "Annuler", "Annulla", "Отмена", "取消", "キャンセル", "إلغاء"],
    "confirm": ["Onayla", "Confirm", "Bestätigen", "Confirmar", "Confirmer", "Conferma", "Подтвердить", "确认", "確認", "تأكيد"],
    "modal_delete": ["🗑️ Sil", "🗑️ Delete", "🗑️ Löschen", "🗑️ Eliminar", "🗑️ Supprimer", "🗑️ Elimina", "🗑️ Удалить", "🗑️ 删除", "🗑️ 削除", "🗑️ حذف"],
    "modal_archive": ["📁 Arşivle", "📁 Archive", "📁 Archivieren", "📁 Archivar", "📁 Archiver", "📁 Archivia", "📁 Архив", "📁 归档", "📁 アーカイブ", "📁 أرشيف"],
    "toast_success": ["İşlem Başarılı", "Success", "Erfolgreich", "Éxito", "Succès", "Successo", "Успех", "成功", "成功", "نجاح"],
    "toast_error": ["Hata Oluştu", "Error", "Fehler", "Error", "Erreur", "Errore", "Ошибка", "错误", "エラー", "خطأ"],
}

translations = {}
lang_keys = list(langs.keys())
for i, l in enumerate(lang_keys):
    translations[l] = {}
    for k, v in keys.items():
        translations[l][k] = v[i]

js_content = f"""const translations = {json.dumps(translations, indent=4, ensure_ascii=False)};

let currentLang = localStorage.getItem('ww_lang') || 'tr';

function applyLanguage(lang) {{
    currentLang = lang;
    localStorage.setItem('ww_lang', lang);
    const t = translations[lang];
    
    document.querySelectorAll('[data-i18n]').forEach(el => {{
        const key = el.getAttribute('data-i18n');
        if (t[key]) {{
            if (el.tagName === 'INPUT' && el.type === 'text') {{
                el.placeholder = t[key];
            }} else {{
                el.innerText = t[key];
            }}
        }}
    }});

    document.documentElement.dir = (lang === 'ar') ? 'rtl' : 'ltr';
    document.documentElement.lang = lang;
}}

window.t = function(key) {{
    return translations[currentLang][key] || key;
}};
window.applyLanguage = applyLanguage;
"""

with codecs.open('frontend/i18n.js', 'w', 'utf-8') as f:
    f.write(js_content)

print("[*] i18n.js generated successfully with 10 languages.")

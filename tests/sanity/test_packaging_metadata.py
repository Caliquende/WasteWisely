from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_wastewise_spec_includes_local_module_paths_and_hidden_imports():
    spec_text = (ROOT / "WasteWisely.spec").read_text(encoding="utf-8")

    assert "pathex=['src']" in spec_text
    assert "'api'" in spec_text
    assert "'actions'" in spec_text
    assert "'scanner'" in spec_text
    assert "'classifier'" in spec_text
    assert "('frontend', 'frontend')" in spec_text


def test_installer_spec_keeps_embedded_app_binary_without_admin_manifest():
    spec_text = (ROOT / "WasteWisely_Installer.spec").read_text(encoding="utf-8")

    assert "('dist/WasteWisely.exe', '.')" in spec_text
    assert "uac_admin=True" not in spec_text

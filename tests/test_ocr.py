"""Unit tests for optional OCR helper (E18-5)."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from app.config import settings
from app.vault import ocr as ocr_mod


@pytest.fixture(autouse=True)
def _clear_cache():
    ocr_mod.clear_ocr_availability_cache()
    yield
    ocr_mod.clear_ocr_availability_cache()


def test_image_ocr_extensions_cover_common_formats():
    assert ".png" in ocr_mod.IMAGE_OCR_EXTENSIONS
    assert ".jpg" in ocr_mod.IMAGE_OCR_EXTENSIONS
    assert ".jpeg" in ocr_mod.IMAGE_OCR_EXTENSIONS
    assert ".webp" in ocr_mod.IMAGE_OCR_EXTENSIONS
    assert ".tif" in ocr_mod.IMAGE_OCR_EXTENSIONS


def test_ocr_ready_respects_config(monkeypatch):
    monkeypatch.setattr(ocr_mod, "is_ocr_available", lambda: True)
    monkeypatch.setattr(settings, "seiton_ocr_enabled", False)
    assert ocr_mod.ocr_ready() is False
    monkeypatch.setattr(settings, "seiton_ocr_enabled", True)
    assert ocr_mod.ocr_ready() is True


def test_pdf_ocr_ready_needs_pypdfium2(monkeypatch):
    monkeypatch.setattr(settings, "seiton_ocr_enabled", True)
    monkeypatch.setattr(ocr_mod, "is_ocr_available", lambda: True)

    real_import = __import__

    def _blocked(name, *args, **kwargs):
        if name == "pypdfium2":
            raise ImportError("missing")
        return real_import(name, *args, **kwargs)

    with patch("builtins.__import__", side_effect=_blocked):
        assert ocr_mod.is_pdf_ocr_available() is False


def test_ocr_image_returns_empty_when_not_ready(tmp_path: Path, monkeypatch):
    monkeypatch.setattr(ocr_mod, "ocr_ready", lambda: False)
    img = tmp_path / "a.png"
    img.write_bytes(b"x")
    assert ocr_mod.ocr_image(img) == ""


def test_ocr_image_calls_tesseract(tmp_path: Path, monkeypatch):
    monkeypatch.setattr(ocr_mod, "ocr_ready", lambda: True)
    monkeypatch.setattr(ocr_mod, "_ocr_lang", lambda: "deu")

    img = tmp_path / "a.png"
    img.write_bytes(b"x")

    fake_rgb = MagicMock()
    fake_image = MagicMock()
    fake_image.convert.return_value = fake_rgb
    fake_image.__enter__ = MagicMock(return_value=fake_image)
    fake_image.__exit__ = MagicMock(return_value=False)

    fake_tess = MagicMock()
    fake_tess.image_to_string.return_value = "  erkannt  "

    with (
        patch.dict("sys.modules", {"pytesseract": fake_tess}),
        patch("PIL.Image.open", return_value=fake_image),
    ):
        text = ocr_mod.ocr_image(img)

    assert text == "erkannt"
    fake_tess.image_to_string.assert_called_once()
    args, kwargs = fake_tess.image_to_string.call_args
    assert args[0] is fake_rgb
    assert kwargs.get("lang") == "deu"


def test_ocr_pdf_returns_empty_when_not_ready(tmp_path: Path, monkeypatch):
    monkeypatch.setattr(ocr_mod, "pdf_ocr_ready", lambda: False)
    pdf = tmp_path / "a.pdf"
    pdf.write_bytes(b"%PDF")
    assert ocr_mod.ocr_pdf(pdf) == ""


def test_ocr_pdf_renders_pages(tmp_path: Path, monkeypatch):
    monkeypatch.setattr(ocr_mod, "pdf_ocr_ready", lambda: True)
    monkeypatch.setattr(ocr_mod, "_ocr_lang", lambda: "eng")

    pdf_path = tmp_path / "scan.pdf"
    pdf_path.write_bytes(b"%PDF")

    fake_page = MagicMock()
    fake_bitmap = MagicMock()
    fake_pil = MagicMock()
    fake_pil.convert.return_value = fake_pil
    fake_bitmap.to_pil.return_value = fake_pil
    fake_page.render.return_value = fake_bitmap

    fake_doc = MagicMock()
    fake_doc.__len__.return_value = 1
    fake_doc.__getitem__.return_value = fake_page

    fake_pypdfium = MagicMock()
    fake_pypdfium.PdfDocument.return_value = fake_doc

    fake_tess = MagicMock()
    fake_tess.image_to_string.return_value = "Seite eins"

    with patch.dict(
        "sys.modules",
        {"pypdfium2": fake_pypdfium, "pytesseract": fake_tess},
    ):
        text = ocr_mod.ocr_pdf(pdf_path)

    assert text == "Seite eins"
    fake_page.render.assert_called_once()
    fake_doc.close.assert_called_once()

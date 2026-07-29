# OCR (E18-5)

Optionale Texterkennung für **gescannte PDFs** und **Foto-Dokumente**
(Zeugnisse, Rechnungen) via [Tesseract](https://github.com/tesseract-ocr/tesseract)
und `pytesseract`. Ohne Installation ändert sich nichts: PDFs ohne Text-Layer
bleiben `doc_type=pdf_no_text`, Bilddateien werden nicht indexiert.

## Setup

```bash
# Python-Extras
pip install -r requirements-ocr.txt

# System-Binary + Sprachpakete (Beispiele)
brew install tesseract tesseract-lang          # macOS
sudo apt install tesseract-ocr tesseract-ocr-deu   # Debian/Ubuntu
```

`pypdfium2` rendert PDF-Seiten zu Bildern (kein Poppler nötig).

## Konfiguration

| Env | Default | Bedeutung |
|-----|---------|-----------|
| `SEITON_OCR_ENABLED` | `true` | OCR nutzen, wenn Deps + Binary vorhanden |
| `SEITON_OCR_LANG` | `deu+eng` | Tesseract-Sprachen (`+`-getrennt) |

## Verhalten

| Datei | Ergebnis |
|-------|----------|
| PDF mit Text-Layer | `doc_type=pdf` (wie bisher, kein OCR) |
| PDF ohne Text, OCR ok | `doc_type=pdf_ocr` + erkannter Text |
| PDF ohne Text, kein OCR | `doc_type=pdf_no_text`, leerer Text |
| `.png` / `.jpg` / …, OCR ok | `doc_type=image_ocr` |
| Bilder ohne OCR | nicht unterstützt (`get_extractor` → `None`) |

Der Vault-Index (`app/vault/index.py`) bleibt unverändert — nur neue Extractor-
Ergebnisse fließen ein.

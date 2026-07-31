# Vision-LLM für Fotos (E18-6)

Optionale Bildbeschreibung via OpenAI Vision für **reine Foto-Inhalte** (kein
brauchbarer OCR-Text). Ergebnis landet als durchsuchbarer Text im Vault-Index
(`doc_type=image_vision`): Beschreibung + Tags.

OCR (E18-5) hat Vorrang: Wenn Tesseract Text liefert → `image_ocr`, kein
Vision-Call.

## Setup

Braucht einen gültigen `OPENAI_API_KEY` und ein vision-fähiges Modell
(z. B. `gpt-4o-mini`). Keine Extra-Python-Pakete.

```env
SEITON_VISION_ENABLED=true
# Optional: eigenes Modell, sonst OPENAI_MODEL
SEITON_VISION_MODEL=
```

Standard ist **aus** (API-Kosten), analog zu `EMBEDDINGS_ENABLED`.

## Verhalten

| Situation | Ergebnis |
|-----------|----------|
| OCR liefert Text | `image_ocr` (kein Vision) |
| OCR leer / aus, Vision an | `image_vision` + Beschreibung/Tags |
| OCR und Vision aus | Bild nicht indexiert |

Prompt: `prompts/vision.v1.txt`. Siehe auch [`ocr.md`](ocr.md).

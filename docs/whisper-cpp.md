# Lokaler Whisper (whisper.cpp) — E6-4

Optionale **lokale** Spracherkennung statt OpenAI Whisper — spart API-Kosten
auf der Heim-Box (Mac Mini / Mini-PC). Default bleibt `WHISPER_PROVIDER=openai`.

## Voraussetzungen

1. [whisper.cpp](https://github.com/ggerganov/whisper.cpp) bauen bzw. Binary
   installieren (`whisper-cli` oder älteres `main`)
2. GGML-Modell laden, z. B. nach `models/` (Ordner ist gitignored, ADR 0002):

```bash
mkdir -p models
# Beispiel: ggml-base.bin von den whisper.cpp-Releases / models-Skript
```

3. Optional: `ffmpeg` für Telegram-OGG → WAV (16 kHz mono)

## Konfiguration

```env
WHISPER_PROVIDER=whisper.cpp
WHISPER_CPP_BINARY=whisper-cli
WHISPER_CPP_MODEL=models/ggml-base.bin
WHISPER_CPP_FALLBACK_OPENAI=true
WHISPER_LANGUAGE=de
```

| Env | Default | Bedeutung |
|-----|---------|-----------|
| `WHISPER_PROVIDER` | `openai` | `openai` oder `whisper.cpp` |
| `WHISPER_CPP_BINARY` | `whisper-cli` | Pfad oder PATH-Name |
| `WHISPER_CPP_MODEL` | `models/ggml-base.bin` | GGML-Modelldatei |
| `WHISPER_CPP_FALLBACK_OPENAI` | `true` | Bei fehlendem Binary/Fehler → OpenAI |
| `WHISPER_LANGUAGE` | leer | ISO-639-1 Hint (E6-3), auch für whisper.cpp `-l` |

## Docker / Heim-Box

Das Binary liegt typisch auf dem **Host**. Varianten:

- Worker auf dem Host (ohne Container) mit lokalem Binary, oder
- Binary + Modell in den Container mounten und `WHISPER_CPP_BINARY` setzen

Fallback auf OpenAI braucht weiterhin `OPENAI_API_KEY`.

## Verhalten

```
Telegram Voice → Cache/Download → transcribe_audio()
  → whisper.cpp wenn Provider=`whisper.cpp` und verfügbar
  → sonst OpenAI whisper-1 (Default / Fallback)
```

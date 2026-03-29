# LIT Runtime

Der Nova School Server erwartet den primären LiteRT-LM-Stack in diesem Ordner.

Offizielle Herkunft der `lit`-Binary:

- `https://github.com/google-ai-edge/LiteRT-LM`

Empfohlene Inhalte auf Windows:

- `lit.windows_x86_64.exe`
- `gemma-3n-E4B-it-int4.litertlm`

Empfohlene Inhalte auf Linux:

- eine native `lit`-Binary
- ein kompatibles `.litertlm`-Modell

Externer Downloadpfad fuer das empfohlene Modell:

- `https://huggingface.co/google/gemma-3n-E4B-it-litert-lm/tree/main`

Vor dem Download:

- bei Hugging Face anmelden
- Googles Gemma-Nutzungsbedingungen fuer das gated Modell akzeptieren

Der Server bevorzugt diesen Ordner automatisch, wenn keine expliziten Pfade in den Servereinstellungen gesetzt sind.

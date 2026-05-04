# STT Model Comparator

A small app to compare speech-to-text models on the same audio fragment.

You can:
- upload an audio file
- run several transcription models
- compare transcripts side-by-side
- estimate cost per model for the clip
- score output quality against an optional reference transcript (WER)

## Quick start

1. Create and activate a Python virtual environment.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. (Optional) Configure API keys for paid providers:

```bash
set OPENAI_API_KEY=your_openai_key
set GROQ_API_KEY=your_groq_key
```

4. Run the app:

```bash
streamlit run app.py
```

## Supported providers (MVP)

- Local free models via `faster-whisper` (`tiny`, `base`, `small`)
- OpenAI (`gpt-4o-mini-transcribe`, `whisper-1`)
- Groq (`whisper-large-v3`, `distil-whisper-large-v3-en`)

You can add more models in `model_registry.py`.

## Cost estimation

Costs are estimated with per-minute prices defined in `model_registry.py`.
Update those values to match your billing contracts/current published pricing.

## Notes

- This MVP computes WER locally if you provide a reference transcript.
- If no reference is provided, the app still compares runtime, transcript length, and cost.
- Local models are free (no API key needed) but may run slower on smaller machines.

## Deploy on Railway

1. Push this repo to GitHub.
2. In Railway, create a new project from the GitHub repo.
3. Railway will install dependencies from `requirements.txt`.
4. Start command is provided by `Procfile`:

```bash
web: streamlit run app.py --server.port $PORT --server.address 0.0.0.0
```

5. Add environment variables in Railway:
   - `OPENAI_API_KEY`
   - `GROQ_API_KEY`

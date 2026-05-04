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

3. Configure API keys:

```bash
set OPENAI_API_KEY=your_openai_key
set GROQ_API_KEY=your_groq_key
```

4. Run the app:

```bash
streamlit run app.py
```

## Supported providers (MVP)

- OpenAI (`gpt-4o-mini-transcribe`, `whisper-1`)
- Groq (`whisper-large-v3`, `distil-whisper-large-v3-en`)

You can add more models in `model_registry.py`.

## Cost estimation

Costs are estimated with per-minute prices defined in `model_registry.py`.
Update those values to match your billing contracts/current published pricing.

## Notes

- This MVP computes WER locally if you provide a reference transcript.
- If no reference is provided, the app still compares runtime, transcript length, and cost.

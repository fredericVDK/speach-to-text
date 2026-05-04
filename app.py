import io
import os
import tempfile
import time
import wave
from typing import Dict, List, Optional

import pandas as pd
import streamlit as st
from jiwer import wer
from openai import OpenAI

from model_registry import MODEL_SPECS, ModelSpec, by_id


def get_audio_duration_seconds(file_bytes: bytes) -> Optional[float]:
    # WAV can be measured without external ffmpeg dependency.
    try:
        with wave.open(io.BytesIO(file_bytes), "rb") as wav_file:
            return wav_file.getnframes() / float(wav_file.getframerate())
    except wave.Error:
        return None


def estimate_cost_usd(duration_seconds: Optional[float], spec: ModelSpec) -> Optional[float]:
    if duration_seconds is None:
        return None
    minutes = duration_seconds / 60.0
    return minutes * spec.estimated_price_per_minute_usd


def transcribe_with_openai(api_key: str, model_name: str, tmp_path: str) -> str:
    client = OpenAI(api_key=api_key)
    with open(tmp_path, "rb") as audio_file:
        response = client.audio.transcriptions.create(
            model=model_name,
            file=audio_file,
            response_format="text",
        )
    return str(response)


def transcribe_with_groq(api_key: str, model_name: str, tmp_path: str) -> str:
    # Groq offers an OpenAI-compatible transcription API.
    client = OpenAI(api_key=api_key, base_url="https://api.groq.com/openai/v1")
    with open(tmp_path, "rb") as audio_file:
        response = client.audio.transcriptions.create(
            model=model_name,
            file=audio_file,
            response_format="text",
        )
    return str(response)


def run_transcription(spec: ModelSpec, tmp_path: str) -> Dict:
    start = time.perf_counter()
    transcript = ""
    error = None
    try:
        if spec.provider == "openai":
            key = os.getenv("OPENAI_API_KEY", "").strip()
            if not key:
                raise RuntimeError("Missing OPENAI_API_KEY")
            transcript = transcribe_with_openai(key, spec.api_model_name, tmp_path)
        elif spec.provider == "groq":
            key = os.getenv("GROQ_API_KEY", "").strip()
            if not key:
                raise RuntimeError("Missing GROQ_API_KEY")
            transcript = transcribe_with_groq(key, spec.api_model_name, tmp_path)
        else:
            raise RuntimeError(f"Unsupported provider: {spec.provider}")
    except Exception as exc:
        error = str(exc)
    elapsed = time.perf_counter() - start
    return {
        "model_id": spec.id,
        "provider": spec.provider,
        "model_label": spec.label,
        "api_model_name": spec.api_model_name,
        "runtime_seconds": round(elapsed, 3),
        "transcript": transcript.strip(),
        "error": error,
    }


def main() -> None:
    st.set_page_config(page_title="STT Comparator", layout="wide")
    st.title("Speech-to-Text Model Comparator")
    st.write(
        "Upload one audio fragment, run multiple models, compare transcript quality, speed, and estimated cost."
    )

    all_models = by_id()
    default_selection = [MODEL_SPECS[0].id, MODEL_SPECS[1].id]
    selected_ids = st.multiselect(
        "Choose models to compare",
        options=[m.id for m in MODEL_SPECS],
        default=default_selection,
        format_func=lambda x: all_models[x].label,
    )

    uploaded = st.file_uploader(
        "Upload audio",
        type=["wav", "mp3", "m4a", "flac", "ogg", "webm"],
        accept_multiple_files=False,
    )

    reference_text = st.text_area(
        "Reference transcript (optional, for WER scoring)",
        placeholder="Paste ground-truth transcript to calculate word error rate.",
    )

    run = st.button("Run comparison", type="primary", disabled=not uploaded or not selected_ids)
    if not run:
        return

    if uploaded is None:
        st.warning("Please upload an audio file.")
        return

    file_bytes = uploaded.read()
    duration_seconds = get_audio_duration_seconds(file_bytes)

    with tempfile.NamedTemporaryFile(delete=False, suffix=f"_{uploaded.name}") as tmp:
        tmp.write(file_bytes)
        temp_audio_path = tmp.name

    results: List[Dict] = []
    progress = st.progress(0, text="Running models...")
    for i, model_id in enumerate(selected_ids, start=1):
        spec = all_models[model_id]
        result = run_transcription(spec, temp_audio_path)
        result["estimated_cost_usd"] = estimate_cost_usd(duration_seconds, spec)
        if reference_text.strip() and not result["error"] and result["transcript"]:
            result["wer"] = wer(reference_text, result["transcript"])
        else:
            result["wer"] = None
        results.append(result)
        progress.progress(i / len(selected_ids), text=f"Completed {i}/{len(selected_ids)} models")

    os.unlink(temp_audio_path)

    rows = []
    for r in results:
        rows.append(
            {
                "Model": r["model_label"],
                "Runtime (s)": r["runtime_seconds"],
                "Estimated Cost (USD)": None
                if r["estimated_cost_usd"] is None
                else round(r["estimated_cost_usd"], 6),
                "WER (lower is better)": None if r["wer"] is None else round(r["wer"], 4),
                "Status": "OK" if not r["error"] else f"ERROR: {r['error']}",
                "Transcript chars": len(r["transcript"]) if r["transcript"] else 0,
            }
        )

    st.subheader("Comparison table")
    st.dataframe(pd.DataFrame(rows), use_container_width=True)

    if duration_seconds is None:
        st.info(
            "Could not detect audio duration from this format. Cost is shown as blank. "
            "WAV duration is detected natively in this MVP."
        )
    else:
        st.caption(f"Detected clip duration: {round(duration_seconds, 2)} seconds")

    st.subheader("Transcripts")
    for r in results:
        with st.expander(r["model_label"], expanded=False):
            if r["error"]:
                st.error(r["error"])
            else:
                st.write(r["transcript"] or "(empty)")

    valid = [r for r in results if not r["error"]]
    if valid:
        st.subheader("Best model hint")
        scored = []
        for r in valid:
            # If WER exists, prioritize quality first; otherwise speed + cost.
            quality_score = r["wer"] if r["wer"] is not None else 1.0
            cost_score = r["estimated_cost_usd"] if r["estimated_cost_usd"] is not None else 999.0
            speed_score = r["runtime_seconds"]
            combined = (quality_score * 0.6) + (cost_score * 0.3) + (speed_score * 0.1)
            scored.append((combined, r))
        scored.sort(key=lambda x: x[0])
        winner = scored[0][1]
        st.success(
            f"Suggested winner: {winner['model_label']} "
            f"(runtime={winner['runtime_seconds']}s, "
            f"cost={winner['estimated_cost_usd']}, wer={winner['wer']})"
        )


if __name__ == "__main__":
    main()

from dataclasses import dataclass
from typing import Dict, List


@dataclass(frozen=True)
class ModelSpec:
    id: str
    provider: str
    label: str
    api_model_name: str
    estimated_price_per_minute_usd: float


MODEL_SPECS: List[ModelSpec] = [
    ModelSpec(
        id="openai_gpt4o_mini_transcribe",
        provider="openai",
        label="OpenAI - gpt-4o-mini-transcribe",
        api_model_name="gpt-4o-mini-transcribe",
        estimated_price_per_minute_usd=0.006,
    ),
    ModelSpec(
        id="openai_whisper_1",
        provider="openai",
        label="OpenAI - whisper-1",
        api_model_name="whisper-1",
        estimated_price_per_minute_usd=0.006,
    ),
    ModelSpec(
        id="groq_whisper_large_v3",
        provider="groq",
        label="Groq - whisper-large-v3",
        api_model_name="whisper-large-v3",
        estimated_price_per_minute_usd=0.004,
    ),
    ModelSpec(
        id="groq_distil_whisper_large_v3_en",
        provider="groq",
        label="Groq - distil-whisper-large-v3-en",
        api_model_name="distil-whisper-large-v3-en",
        estimated_price_per_minute_usd=0.002,
    ),
]


def by_id() -> Dict[str, ModelSpec]:
    return {m.id: m for m in MODEL_SPECS}

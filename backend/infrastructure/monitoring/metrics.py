from prometheus_client import Counter, Histogram

# Metrics Definitions
CALL_DURATION = Histogram(
    "victoria_call_duration_seconds",
    "Time spent in calls",
    buckets=[1, 5, 10, 30, 60, 120, 300, 600]
)

CALLS_TOTAL = Counter(
    "victoria_calls_total",
    "Total number of calls processed",
    ["status", "client_type"]
)

TTS_GENERATION_DURATION = Histogram(
    "victoria_tts_generation_seconds",
    "Time spent generating TTS audio",
    ["provider"]
)

STT_TRANSCRIPTION_DURATION = Histogram(
    "victoria_stt_transcription_seconds",
    "Time spent converting speech to text",
    ["provider"]
)

LLM_GENERATION_DURATION = Histogram(
    "victoria_llm_generation_seconds",
    "Time spent generating LLM response",
    ["model"]
)

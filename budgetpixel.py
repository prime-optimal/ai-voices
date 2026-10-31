#!/usr/bin/env python3
"""
BudgetPixel text-to-speech provider.

BudgetPixel's public developer API (/v1, bpx_ keys) does not expose speech
models, so this talks to the same endpoints the budgetpixel.com Audio Workshop
uses. Those authenticate with the web session's access token, which is
exchanged from the browser session cookie in BUDGETPIXEL_SESSION.
"""

import os
import sys
import time

import requests

SITE_BASE = "https://budgetpixel.com"
API_BASE = "https://api.budgetpixel.com"
SESSION_COOKIE = "__Secure-next-auth.session-token"

DEFAULT_MODEL = "speech-2.8-hd"
DEFAULT_VOICE = "Robot_Armor"

TTS_MODELS = {
    "speech-2.8-hd": {"name": "MiniMax Speech 2.8 HD", "voices": "minimax"},
    "speech-2.8-turbo": {"name": "MiniMax Speech 2.8 Turbo", "voices": "minimax"},
    "byteplus-tts": {"name": "BytePlus TTS", "voices": "byteplus"},
}

MIN_TEXT_LENGTH = 10
MAX_TEXT_LENGTH = 5000
FAILED_STATUSES = {"failed", "error", "cancelled", "canceled"}


def _fail(message, detail=None):
    print(f"❌ {message}")
    if detail:
        print(f"   {detail}")
    sys.exit(1)


def get_access_token(session=None):
    """Exchange the budgetpixel.com session cookie for an API access token."""
    session = session or os.environ.get("BUDGETPIXEL_SESSION")
    if not session:
        _fail(
            "BUDGETPIXEL_SESSION is not set",
            f"Copy the '{SESSION_COOKIE}' cookie from a logged-in budgetpixel.com tab, then run `mise run login` in the ai-voices repo (see README).",
        )

    cookie = session if "=" in session else f"{SESSION_COOKIE}={session}"
    response = requests.get(
        f"{SITE_BASE}/api/auth/session", headers={"Cookie": cookie}, timeout=30
    )
    if response.status_code != 200:
        _fail(
            f"BudgetPixel session lookup failed: {response.status_code}",
            response.text[:300],
        )

    token = response.json().get("accessToken")
    if not token:
        _fail(
            "BudgetPixel session is invalid or expired",
            "Log in to budgetpixel.com again, copy a fresh cookie, and run `mise run login`.",
        )
    return token


def _api(method, path, token, **kwargs):
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.request(
        method, f"{API_BASE}{path}", headers=headers, timeout=60, **kwargs
    )
    if not response.ok:
        try:
            error = response.json().get("error") or response.text
        except ValueError:
            error = response.text
        _fail(
            f"BudgetPixel {method} {path} failed: {response.status_code}",
            str(error)[:300],
        )
    return response.json()


def list_models():
    print("\n🎛️  BudgetPixel TTS models:\n")
    for model_id, info in TTS_MODELS.items():
        marker = " (default)" if model_id == DEFAULT_MODEL else ""
        print(f"  {model_id:<18} {info['name']}{marker}")
    print()


def fetch_voices(token, model):
    """Return the live voice list for a model's voice family."""
    family = TTS_MODELS[model]["voices"]
    return _api("GET", f"/api/v1/voices/{family}", token).get("voices", [])


def filter_voices(voices, query):
    if not query:
        return voices
    q = query.lower()
    return [
        v
        for v in voices
        if q in v.get("name", "").lower()
        or q in v.get("voice_id", "").lower()
        or q in (v.get("category") or "").lower()
        or q in (v.get("language") or "").lower()
    ]


def print_voices(voices):
    for i, v in enumerate(voices, 1):
        meta = " · ".join(x for x in (v.get("language"), v.get("category")) if x)
        print(f"  {i:>3}. {v.get('name', '?'):<40} {v['voice_id']:<36} {meta}")


def list_voices(token, model, query=None):
    voices = filter_voices(fetch_voices(token, model), query)
    print(f"\n🎤 {TTS_MODELS[model]['name']} voices ({len(voices)}):\n")
    print_voices(voices)
    print()


def select_voice_interactive(token, model):
    """Search the live voice list and pick one by number."""
    voices = fetch_voices(token, model)
    while True:
        query = input(
            f"\n🔎 Search {len(voices)} voices (name/language/category, Enter = all, q = quit): "
        ).strip()
        if query.lower() == "q":
            print("👋 Goodbye!")
            sys.exit(0)
        matches = filter_voices(voices, query)
        if not matches:
            print("   No matches.")
            continue
        print()
        print_voices(matches)
        choice = input(f"\nPick 1-{len(matches)} (Enter = search again): ").strip()
        if choice.isdigit() and 1 <= int(choice) <= len(matches):
            picked = matches[int(choice) - 1]
            print(f"✅ Using voice: {picked.get('name')} (ID: {picked['voice_id']})\n")
            return picked["voice_id"]


def validate_text(text):
    if not MIN_TEXT_LENGTH <= len(text) <= MAX_TEXT_LENGTH:
        _fail(
            f"BudgetPixel needs {MIN_TEXT_LENGTH}-{MAX_TEXT_LENGTH} characters (got {len(text)})."
        )


def submit_request(token, text, voice_id, model):
    payload = {
        "text": text,
        "model": model,
        "voice_id": voice_id,
        "is_private": True,
        "folder_id": None,
        "speed": 1.0,
        "pitch": 0,
        "volume": 1.0,
        "emotion": "neutral",
        "parameters": {"audio_format": "mp3", "sample_rate": 44100, "bitrate": 256000},
    }

    print("\n📤 Submitting request to BudgetPixel...")
    print(f"   Model: {model}")
    print(f"   Text: {text[:50]}{'...' if len(text) > 50 else ''}")
    print(f"   Voice: {voice_id}")

    result = _api("POST", "/api/v1/tts/generate", token, json=payload)
    generation = result.get("generation") or result
    job_ids = {
        str(x)
        for x in (generation.get("id"), generation.get("generation_id"))
        if x is not None
    }
    if not job_ids:
        _fail("BudgetPixel did not return a generation id", str(result)[:300])

    print("✅ Request submitted successfully!")
    print(f"   Generation ID: {', '.join(sorted(job_ids))}\n")
    return job_ids


def _find_job(token, job_ids):
    history = _api("GET", "/api/v1/audios/history?limit=25&offset=0", token)
    for job in history.get("audio_generations", []):
        if {str(job.get("id")), str(job.get("generation_id"))} & job_ids:
            return job
    return None


def poll_until_complete(token, job_ids, poll_interval=2, timeout=600):
    """Poll the audio history until the job completes; return its audio URL."""
    print("⏳ Waiting for processing to complete...")
    deadline = time.time() + timeout
    last_status = None
    while time.time() < deadline:
        job = _find_job(token, job_ids)
        status = (job or {}).get("status", "pending")
        if status != last_status:
            print(f"   Status: {status}")
            last_status = status
        if status == "completed":
            audios = job.get("audios") or []
            if not audios or not audios[0].get("url"):
                _fail("BudgetPixel job completed without an audio URL", str(job)[:300])
            print("✅ Processing complete!\n")
            return audios[0]["url"]
        if status in FAILED_STATUSES:
            _fail(f"BudgetPixel generation {status}", job.get("error_message"))
        time.sleep(poll_interval)
    _fail(f"Timed out after {timeout}s waiting for BudgetPixel")


def generate(text, voice_id, model=DEFAULT_MODEL, poll_interval=2):
    """Run a full BudgetPixel TTS generation and return the audio URL."""
    validate_text(text)
    token = get_access_token()
    job_ids = submit_request(token, text, voice_id, model)
    return poll_until_complete(token, job_ids, poll_interval)

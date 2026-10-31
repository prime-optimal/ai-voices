#!/usr/bin/env python3
"""
AI Voice Generator - Command-line text-to-speech tool (BudgetPixel Speech 2.8 HD by default, fal.ai MiniMax optionally)
"""

import argparse
import shutil
import subprocess
import requests
import time
import os
import sys
from pathlib import Path

import budgetpixel

# Import voice configuration
from voices import (
    ALL_VOICE_IDS,
    resolve_voice_id,
    list_voices,
    select_voice_interactive,
)

APP_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = APP_DIR / "output"
FNOX_CONFIG = APP_DIR / "fnox.toml"


def load_secret(name):
    """Return env var `name`, falling back to the repo's fnox.toml via `fnox get`."""
    value = os.environ.get(name)
    if value or not shutil.which("fnox") or not FNOX_CONFIG.exists():
        return value
    result = subprocess.run(
        ["fnox", "get", name, "-c", str(FNOX_CONFIG)],
        capture_output=True,
        text=True,
    )
    value = result.stdout.strip() if result.returncode == 0 else ""
    if value:
        os.environ[name] = value
    return value or None


def submit_request(text, voice_id, api_key):
    """Submit a text-to-speech request and return request ID"""
    url = "https://queue.fal.run/fal-ai/minimax/speech-02-hd"

    headers = {"Authorization": f"Key {api_key}", "Content-Type": "application/json"}

    payload = {
        "text": text,
        "voice_setting": {"voice_id": voice_id},
        "output_format": "url",  # Get URL instead of hex
        "enable_safety_checker": False,
    }

    print(f"\n📤 Submitting request...")
    print(f"   Text: {text[:50]}{'...' if len(text) > 50 else ''}")
    print(f"   Voice: {voice_id}")

    response = requests.post(url, headers=headers, json=payload)

    if response.status_code != 200:
        print(f"❌ Error submitting request: {response.status_code}")
        print(f"   Response: {response.text}")
        sys.exit(1)

    result = response.json()
    request_id = result.get("request_id")
    status_url = result.get("status_url")

    print(f"✅ Request submitted successfully!")
    print(f"   Request ID: {request_id}\n")

    return request_id, status_url


def check_status(status_url, api_key):
    """Check the status of the request"""
    headers = {"Authorization": f"Key {api_key}"}

    response = requests.get(status_url, headers=headers)

    # 202 is a normal response for async operations (IN_QUEUE or IN_PROGRESS)
    if response.status_code not in [200, 202]:
        print(f"❌ Error checking status: {response.status_code}")
        return None

    return response.json()


def poll_until_complete(request_id, status_url, api_key, poll_interval=2):
    """Poll the status URL until the request is complete"""
    print(f"⏳ Processing request (ID: {request_id})...")
    print(f"   Checking status every {poll_interval} seconds...\n")

    start_time = time.time()

    while True:
        status_data = check_status(status_url, api_key)

        if not status_data:
            print("❌ Failed to get status")
            sys.exit(1)

        status = status_data.get("status")
        queue_position = status_data.get("queue_position", 0)

        if status == "IN_QUEUE":
            print(f"⏳ In queue... Position: {queue_position}")
        elif status == "IN_PROGRESS":
            print(f"⚙️  Processing...")
        elif status == "COMPLETED":
            elapsed = time.time() - start_time
            print(f"\n✅ Completed in {elapsed:.1f} seconds!\n")
            return status_data
        else:
            print(f"❌ Unknown status: {status}")
            sys.exit(1)

        time.sleep(poll_interval)


def get_result(response_url, api_key):
    """Get the final result of the request"""
    headers = {"Authorization": f"Key {api_key}"}

    print(f"📥 Retrieving result from response URL...")
    print(f"   URL: {response_url}")

    response = requests.get(response_url, headers=headers)

    if response.status_code != 200:
        print(f"❌ Error getting result: {response.status_code}")
        print(f"   Response: {response.text}")

        # Try alternative URL patterns
        if "/queue/" in response_url:
            # Try without /queue/
            alt_url = response_url.replace("/queue/", "/")
            print(f"   Trying alternative URL: {alt_url}")
            response = requests.get(alt_url, headers=headers)

            if response.status_code != 200:
                print(f"   Alternative also failed: {response.status_code}")
                sys.exit(1)
        else:
            sys.exit(1)

    return response.json()


def generate_filename(voice_id, display_name, text, default_output="output.mp3"):
    """Generate a filename based on voice and text with naming convention.

    Format: For custom voices: {display_name}-{YYYY-MM-DD}-{text}.mp3
            For built-in voices: {voice_id}-{YYYY-MM-DD}-{text}.mp3
    Maximum filename length: 100 characters
    """
    from datetime import datetime

    # Get current date
    date_str = datetime.now().strftime("%Y-%m-%d")

    # Use display name for custom voices, voice_id for built-in voices
    if display_name != voice_id:
        # This is a custom voice - use the display name (sanitized)
        voice_identifier = "".join(
            c if c.isalnum() else "_" for c in display_name.lower()
        )
    else:
        # This is a built-in voice - use the voice ID (sanitized)
        voice_identifier = "".join(c if c.isalnum() else "_" for c in voice_id.lower())

    # Sanitize text for filename
    # Remove or replace special characters, keep alphanumeric and spaces
    safe_text = "".join(c if c.isalnum() or c in (" ", "-", "_") else "_" for c in text)

    # Replace multiple spaces/underscores with single underscore
    import re

    safe_text = re.sub(r"[_\s]+", "_", safe_text)

    # Remove leading/trailing underscores
    safe_text = safe_text.strip("_")

    # Calculate available space for text
    # Format: {voice_identifier}-{date}-{text}.mp3
    # voice_identifier + "-" + date + "-" + text + ".mp3"
    # 100 max total
    date_part = len(date_str)  # YYYY-MM-DD = 10 chars
    extension_part = 4  # .mp3 = 4 chars
    separators = 2  # two hyphens
    voice_part = len(voice_identifier)

    # Available for text
    available_for_text = 100 - date_part - extension_part - separators - voice_part

    # Ensure we have at least some text
    if available_for_text < 1:
        # Voice identifier is too long, truncate it
        max_voice_len = 100 - date_part - extension_part - separators - 1
        voice_identifier = voice_identifier[:max_voice_len]
        available_for_text = (
            100 - date_part - extension_part - separators - len(voice_identifier)
        )

    # Truncate text if needed
    if len(safe_text) > available_for_text:
        safe_text = safe_text[:available_for_text].rstrip("_")

    # Construct filename
    filename = f"{voice_identifier}-{date_str}-{safe_text}.mp3"

    return filename


def download_audio(audio_url, output_path):
    """Download the audio file"""
    print(f"⬇️  Downloading audio...")
    print(f"   URL: {audio_url}")
    print(f"   Destination: {output_path}")

    response = requests.get(audio_url)

    if response.status_code != 200:
        print(f"❌ Error downloading file: {response.status_code}")
        sys.exit(1)

    # Create directory if it doesn't exist
    os.makedirs(
        os.path.dirname(output_path) if os.path.dirname(output_path) else ".",
        exist_ok=True,
    )

    with open(output_path, "wb") as f:
        f.write(response.content)

    file_size = os.path.getsize(output_path)
    print(f"✅ Downloaded successfully!")
    print(f"   File: {output_path}")
    print(f"   Size: {file_size / 1024:.1f} KB\n")


def run_fal(text, voice_id, api_key, poll_interval):
    """Run a fal.ai MiniMax generation and return the audio URL."""
    request_id, status_url = submit_request(text, voice_id, api_key)
    status_data = poll_until_complete(request_id, status_url, api_key, poll_interval)

    response_url = status_data.get("response_url")
    if not response_url:
        print("❌ Error: No response_url in status data")
        sys.exit(1)

    audio_url = get_result(response_url, api_key).get("audio", {}).get("url")
    if not audio_url:
        print("❌ Error: No audio URL in response")
        sys.exit(1)
    return audio_url


def main():
    parser = argparse.ArgumentParser(
        description="AI Voice Generator - Convert text to speech (BudgetPixel by default, or fal.ai)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
Examples:
  %(prog)s The dead are dancing tonight      (default voice, text as plain words)
  %(prog)s --pick                            (search voices interactively)
  %(prog)s --list-models
  %(prog)s --list-voices --search robot
  %(prog)s --model speech-2.8-turbo --voice Robot_Armor "Faster render"
  %(prog)s --provider fal --voice "Joe Rogan" "Hello world"

Files are saved to {OUTPUT_DIR} unless --output or --output-dir is given.
No text → prompts for multi-line input (Ctrl+D to finish).

Environment Variables (fall back to {FNOX_CONFIG} via fnox):
  BUDGETPIXEL_SESSION  budgetpixel.com session cookie (provider budgetpixel)
  FAL_API_KEY          fal.ai API key (provider fal)
  VOICE                Voice used when --voice is omitted (default: {budgetpixel.DEFAULT_VOICE})
""",
    )

    parser.add_argument(
        "--provider",
        choices=["budgetpixel", "fal"],
        default="budgetpixel",
        help="TTS provider (default: budgetpixel)",
    )

    parser.add_argument(
        "--model",
        choices=list(budgetpixel.TTS_MODELS),
        default=budgetpixel.DEFAULT_MODEL,
        help=f"BudgetPixel model (default: {budgetpixel.DEFAULT_MODEL})",
    )

    parser.add_argument(
        "--voice",
        type=str,
        help="Voice ID (default: $VOICE or $DEFAULT_VOICE or "
        f"{budgetpixel.DEFAULT_VOICE}; see --list-voices)",
    )

    parser.add_argument(
        "--pick",
        action="store_true",
        help="Choose the voice from the interactive picker",
    )

    parser.add_argument("words", nargs="*", help="Text to speak (quotes optional)")

    parser.add_argument("--text", type=str, help="Text to convert to speech")

    parser.add_argument(
        "--output",
        type=str,
        help="Exact output file path (default: auto-named file in --output-dir)",
    )

    parser.add_argument(
        "--output-dir",
        type=Path,
        default=OUTPUT_DIR,
        help=f"Folder for auto-named files (default: {OUTPUT_DIR})",
    )

    parser.add_argument(
        "--api-key",
        type=str,
        help="fal.ai API key (or set FAL_API_KEY environment variable)",
    )

    parser.add_argument(
        "--list-models",
        action="store_true",
        help="List BudgetPixel TTS models and exit",
    )

    parser.add_argument(
        "--list-voices",
        action="store_true",
        help="List voices for the selected provider/model and exit",
    )

    parser.add_argument(
        "--search",
        type=str,
        help="Filter --list-voices by name, ID, language or category",
    )

    parser.add_argument(
        "--poll-interval",
        type=int,
        default=2,
        help="Seconds to wait between status checks (default: 2)",
    )

    args = parser.parse_args()
    use_bp = args.provider == "budgetpixel"

    if args.list_models:
        budgetpixel.list_models()
        return

    if args.list_voices:
        if use_bp:
            load_secret("BUDGETPIXEL_SESSION")
            budgetpixel.list_voices(
                budgetpixel.get_access_token(), args.model, args.search
            )
        else:
            list_voices()
        return

    if use_bp:
        load_secret("BUDGETPIXEL_SESSION")

    api_key = None
    if not use_bp:
        api_key = args.api_key or load_secret("FAL_API_KEY")
        if not api_key:
            print("❌ Error: API key required")
            print(
                "   Either use --api-key flag or set FAL_API_KEY environment variable"
            )
            sys.exit(1)

    if args.voice is None and not args.pick:
        args.voice = (
            os.environ.get("VOICE")
            or os.environ.get("DEFAULT_VOICE")
            or budgetpixel.DEFAULT_VOICE
        )

    if use_bp:
        if args.voice is None:
            args.voice = budgetpixel.select_voice_interactive(
                budgetpixel.get_access_token(), args.model
            )
        voice_id = display_name = args.voice
        print(
            f"✅ Using voice: {voice_id} ({budgetpixel.TTS_MODELS[args.model]['name']})\n"
        )
    else:
        if args.voice is None:
            args.voice = select_voice_interactive()
        voice_id, display_name = resolve_voice_id(args.voice)
        if voice_id not in ALL_VOICE_IDS:
            print(f"⚠️  Warning: '{args.voice}' is not in the known voice list.")
            print("   It may still work if it's a valid voice ID.")
            print("   Use --list-voices to see all known options.\n")
        elif display_name != voice_id:
            print(f"✅ Using voice: {display_name} (ID: {voice_id})\n")
        else:
            print(f"✅ Using voice: {voice_id}\n")

    # Get text from user if not provided
    text = args.text or " ".join(args.words)
    if not text:
        print("\nEnter the text to convert to speech:")
        print("(Press Ctrl+D/Ctrl+Z on a new line when finished)")
        lines = []
        try:
            for line in sys.stdin:
                lines.append(line.rstrip("\n"))
            text = "\n".join(lines)
        except KeyboardInterrupt:
            print("\n\n❌ Cancelled by user")
            sys.exit(1)

    if not text.strip():
        print("❌ Error: Empty text provided")
        sys.exit(1)

    if len(text) > 5000:
        print(f"❌ Error: Text too long ({len(text)} characters). Maximum is 5000.")
        sys.exit(1)

    try:
        output_file = args.output or str(
            args.output_dir / generate_filename(voice_id, display_name, text)
        )
        print(f"📝 Output file: {output_file}\n")

        if use_bp:
            audio_url = budgetpixel.generate(
                text, voice_id, args.model, args.poll_interval
            )
        else:
            audio_url = run_fal(text, voice_id, api_key, args.poll_interval)

        download_audio(audio_url, output_file)

        print(f"🎉 All done! Your audio file is ready at: {output_file}")

    except KeyboardInterrupt:
        print("\n\n❌ Cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
AI Voice Generator - Command-line text-to-speech tool using MiniMax Speech-02 HD API
"""
import argparse
import requests
import time
import os
import sys

# Import voice configuration
from voices import (
    CUSTOM_VOICES,
    BUILTIN_VOICES,
    ALL_VOICE_IDS,
    VOICE_NAME_TO_ID,
    resolve_voice_id,
    list_voices,
    select_voice_interactive,
)



def submit_request(text, voice_id, api_key):
    """Submit a text-to-speech request and return request ID"""
    url = "https://queue.fal.run/fal-ai/minimax/speech-02-hd"

    headers = {
        "Authorization": f"Key {api_key}",
        "Content-Type": "application/json"
    }

    payload = {
        "text": text,
        "voice_setting": {
            "voice_id": voice_id
        },
        "output_format": "url"  # Get URL instead of hex
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
    headers = {
        "Authorization": f"Key {api_key}"
    }

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
    headers = {
        "Authorization": f"Key {api_key}"
    }

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
        voice_identifier = "".join(c if c.isalnum() else "_" for c in display_name.lower())
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
        available_for_text = 100 - date_part - extension_part - separators - len(voice_identifier)

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
    os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else ".", exist_ok=True)

    with open(output_path, "wb") as f:
        f.write(response.content)

    file_size = os.path.getsize(output_path)
    print(f"✅ Downloaded successfully!")
    print(f"   File: {output_path}")
    print(f"   Size: {file_size / 1024:.1f} KB\n")


def main():
    parser = argparse.ArgumentParser(
        description="AI Voice Generator - Convert text to speech using MiniMax Speech-02 HD",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --voice "Wise_Woman" --text "Hello world"
  %(prog)s --list-voices
  %(prog)s --voice "Deep_Voice_Man" --text "This is a test" --output test.mp3

Environment Variables:
  FAL_KEY    Your fal.ai API key (required if not using --api-key)
"""
    )

    parser.add_argument(
        "--voice",
        type=str,
        help="Voice ID to use (see --list-voices for all options)"
    )

    parser.add_argument(
        "--text",
        type=str,
        help="Text to convert to speech"
    )

    parser.add_argument(
        "--output",
        type=str,
        default="output.mp3",
        help="Output file path (default: output.mp3)"
    )

    parser.add_argument(
        "--api-key",
        type=str,
        help="fal.ai API key (or set FAL_KEY environment variable)"
    )

    parser.add_argument(
        "--list-voices",
        action="store_true",
        help="List all available voice IDs and exit"
    )

    parser.add_argument(
        "--poll-interval",
        type=int,
        default=2,
        help="Seconds to wait between status checks (default: 2)"
    )

    args = parser.parse_args()

    # List voices and exit
    if args.list_voices:
        list_voices()
        return

    # Get API key from args or environment
    api_key = args.api_key or os.environ.get("FAL_KEY")

    if not api_key:
        print("❌ Error: API key required")
        print("   Either use --api-key flag or set FAL_KEY environment variable")
        sys.exit(1)

    # Get voice - show interactive menu if not provided
    if args.voice is None:
        args.voice = select_voice_interactive()

    # Resolve voice input to actual voice ID
    voice_id, display_name = resolve_voice_id(args.voice)

    # Check if it's a valid voice
    if voice_id not in ALL_VOICE_IDS:
        print(f"⚠️  Warning: '{args.voice}' is not in the known voice list.")
        print("   It may still work if it's a valid voice ID.")
        print("   Use --list-voices to see all known options.\n")
    else:
        # Show which voice we're using
        if display_name != voice_id:
            print(f"✅ Using voice: {display_name} (ID: {voice_id})\n")
        else:
            print(f"✅ Using voice: {voice_id}\n")

    # Get text from user if not provided
    text = args.text
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
        # Generate filename if not provided
        output_file = args.output
        if output_file == "output.mp3":
            # User didn't specify custom output, use naming convention
            output_file = generate_filename(voice_id, display_name, text)
            print(f"📝 Using auto-generated filename: {output_file}\n")

        # Submit request
        request_id, status_url = submit_request(text, voice_id, api_key)

        # Poll until complete
        status_data = poll_until_complete(request_id, status_url, api_key, args.poll_interval)

        # Get the response_url from the final status
        response_url = status_data.get("response_url")
        if not response_url:
            print("❌ Error: No response_url in status data")
            sys.exit(1)

        # Get result
        result = get_result(response_url, api_key)

        # Download audio
        audio_url = result.get("audio", {}).get("url")
        if not audio_url:
            print("❌ Error: No audio URL in response")
            sys.exit(1)

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

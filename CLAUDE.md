# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a **command-line text-to-speech (TTS) generator** that converts text (up to 5000 characters) into natural-sounding speech using the MiniMax Speech-02 HD AI model via the fal.ai platform. It's a single-file Python application focused on simplicity and ease of use.

## Common Commands

### Installation
```bash
# Using uv (recommended)
uv sync

# Using pip
pip install requests>=2.31.0
```

### Running the Application

#### Interactive Mode (Recommended)
```bash
# Run without arguments for interactive voice selection menu
python main.py
```
This will show an interactive menu where you can:
- Select voices by number
- Custom voices appear first
- Built-in voices appear second
- Enter 'q' to quit at any time

#### Command-Line Mode
```bash
# List all available voices
python main.py --list-voices

# Generate speech with auto-generated filename
python main.py --voice "Wise_Woman" --text "Hello world"

# Generate speech from stdin (multi-line support)
python main.py --voice "Deep_Voice_Man"
# Type text, then press Ctrl+D when finished

# Custom output file
python main.py --voice "Calm_Woman" --text "Welcome" --output custom.mp3

# Using API key directly
python main.py --voice "Lively_Girl" --text "Hello!" --api-key "your-key-here"
```

### Environment Setup
```bash
# Set API key as environment variable
export FAL_KEY="your-api-key-here"
```

## Available Voices

The application includes 17 pre-configured voice IDs:
- Wise_Woman, Friendly_Person, Inspirational_girl
- Deep_Voice_Man, Calm_Woman, Casual_Guy, Lively_Girl
- Patient_Man, Young_Knight, Determined_Man
- Lovely_Girl, Decent_Boy, Imposing_Manner, Elegant_Man
- Abbess, Sweet_Girl_2, Exuberant_Girl

Use `python main.py --list-voices` to display all options.

## Code Architecture

### Project Structure
- **main.py** - Single Python file containing the entire CLI application (382 lines)
- **pyproject.toml** - Project configuration and dependencies
- **schema.json** - OpenAPI 3.0.4 specification for the MiniMax API
- **llms.txt** - Model documentation from fal.ai
- **README.md** - Comprehensive usage documentation

### Application Flow
The application follows a straightforward 4-step process:

1. **Submit** → POST to `https://queue.fal.run/fal-ai/minimax/speech-02-hd`
   - Sends text and voice settings
   - Receives `request_id` and `status_url`

2. **Poll** → GET to `status_url`
   - Continuously checks status (IN_QUEUE → IN_PROGRESS → COMPLETED)
   - Polling interval is configurable (default: 2 seconds)

3. **Retrieve** → GET to `response_url`
   - Gets the result object
   - Extracts `audio.url` from response

4. **Download** → GET to `audio.url`
   - Downloads MP3 file
   - Saves to specified path

### Key Functions (main.py)

- `main()` - Entry point with argument parsing (lines 396-440)
- `list_voices()` - Displays all available voice IDs (lines 77-102)
- `select_voice_interactive()` - Interactive voice selection menu (lines 105-165)
- `resolve_voice_id()` - Resolves display names to voice IDs (lines 48-74)
- `submit_request()` - POSTs TTS request to fal.ai API (lines 168-183)
- `check_status()` - Checks request status (lines 186-199)
- `poll_until_complete()` - Polls status URL until completion (lines 202-230)
- `get_result()` - Retrieves final result from response URL (lines 233-261)
- `generate_filename()` - Creates auto-generated filenames (lines 264-314)
- `download_audio()` - Downloads MP3 file from URL (lines 317-338)

### Dependencies
- **fal-client** (>=0.8.1) - Official Python SDK for fal.ai (included but not used in main.py)
- **requests** (>=2.31.0) - HTTP library for API calls
- **Python 3.14+** - Requires very recent Python version

## File Naming Convention

When no custom output is specified, files are auto-generated using this pattern:
```
{voice_id}-{YYYY-MM-DD}-{text}.mp3
```

Rules:
- Maximum 100 characters total
- Voice ID is sanitized to lowercase with underscores
- Text is sanitized to alphanumeric, spaces, hyphens, and underscores
- Multiple spaces/underscores are replaced with single underscore
- Text is truncated if needed to fit 100-character limit

Examples:
- `wise_woman-2025-10-31-hello_world.mp3`
- `deep_voice_man-2025-10-31-this_is_a_test.mp3`

## Development Notes

### Design Philosophy
- **Single-file application** - No complex module structure, everything in main.py
- **CLI-first design** - No web interface or GUI
- **Synchronous polling** - Uses time.sleep() instead of async/await
- **Direct HTTP requests** - Uses `requests` library directly (fal-client SDK in dependencies but not used)
- **Fail-fast error handling** - Exits immediately on errors with clear messages
- **User-friendly output** - Uses emojis and clear status messages

### Input Validation
- Text length: Maximum 5000 characters
- Minimum 1 non-whitespace character required
- API key required (via --api-key flag or FAL_KEY environment variable)
- Voice ID validated against known list (warning shown if not found but still works)

### Configuration Options
- `--voice` - Voice ID (required)
- `--text` - Text to convert (optional if using stdin)
- `--output` - Output file path (default: auto-generated filename)
- `--api-key` - fal.ai API key (or use FAL_KEY environment variable)
- `--poll-interval` - Seconds between status checks (default: 2)

## Working with the Codebase

### Modifying Voice Options
Voice IDs are defined in the `VOICE_IDS` list (lines 13-31 in main.py). The application will work with any valid voice ID from the fal.ai API, not just the predefined list.

### Understanding the API Flow
- The application uses queue-based processing
- Requests go to `IN_QUEUE` → `IN_PROGRESS` → `COMPLETED`
- Status is polled at regular intervals
- Result URL handling includes failover for alternative URL patterns (lines 146-156)

### Extending Functionality
Key areas for potential enhancement:
- Add batch text processing
- Implement async/await for better performance
- Add progress bars for long texts
- Add voice preview functionality
- Use the fal-client SDK instead of raw HTTP requests
- Add support for audio settings (speed, pitch, volume, emotions)

## API Integration

The project integrates with **fal.ai's MiniMax Speech-02 HD model**:
- Endpoint: `https://queue.fal.run/fal-ai/minimax/speech-02-hd`
- Authentication: `Authorization: Key {api_key}`
- Response format: URL-based (set via `"output_format": "url"`)
- Complete API specification available in `schema.json`

For detailed API documentation including all voice and audio settings, see:
- `llms.txt` - Model documentation
- `schema.json` - OpenAPI specification with all request/response schemas

## Important Files

- **main.py** - Main application code (382 lines, single file)
- **README.md** - User-facing documentation and examples
- **pyproject.toml** - Python project configuration
- **schema.json** - Complete API schema with all configuration options
- **.python-version** - Specifies Python 3.14

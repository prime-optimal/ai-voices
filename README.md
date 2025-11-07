# AI Voices - Text-to-Speech Generator

A command-line tool for generating high-quality speech from text using the MiniMax Speech-02 HD AI model.

## Features

- **Custom voices** - Use your trained voice models (primary)
- **Built-in voices** - 17 fal.ai default voices (secondary)
- Convert text to natural-sounding speech
- Automatic request polling until completion
- Download generated MP3 files
- Simple command-line interface

## Installation

1. Clone or download this repository
2. Install dependencies using uv:

```bash
uv sync
```

Or using pip:

```bash
pip install requests>=2.31.0
```

## Setup

You'll need a fal.ai API key. You can get one at [fal.ai](https://fal.ai).

Set the API key as an environment variable:

```bash
export FAL_KEY="your-api-key-here"
```

Or pass it directly with the `--api-key` flag when running the script.

## Usage

### Interactive Mode (No Arguments)

Run without arguments to use the interactive voice selection menu:

```bash
python main.py
```

This will:
1. Show a menu with all available voices
2. Custom voices appear first (if configured)
3. Built-in voices appear second
4. Enter the number of your choice (or 'q' to quit)
5. Then enter your text to convert to speech

### List all available voices

```bash
python main.py --list-voices
```

### Generate speech with arguments

When you don't specify `--output`, files are automatically named using this convention:
`{voice_id}-{YYYY-MM-DD}-{text}.mp3`

Example: `wise_woman-2025-10-31-hello_world.mp3` (max 100 characters)

```bash
python main.py --voice "Wise_Woman" --text "Hello world"
```

### Generate speech from stdin (multi-line text)

```bash
python main.py --voice "Deep_Voice_Man"
# Then type your text and press Ctrl+D when finished
```

### Custom output file

```bash
python main.py --voice "Calm_Woman" --text "Welcome to our service" --output custom_name.mp3
```

### Using API key directly

```bash
python main.py --voice "Lively_Girl" --text "Hello everyone!" --api-key "your-api-key-here"
```

### Naming Convention

When no custom output is specified, files follow this pattern:

**For Custom Voices (using display name):**
```
{voice_display_name}-{YYYY-MM-DD}-{text}.mp3
```
- **Example**: `joe_rogan-2025-11-06-whats_up_party_people.mp3`
- **Note**: Uses the display name from CUSTOM_VOICES, not the voice ID!

**For Built-in Voices (using voice ID):**
```
{voice_id}-{YYYY-MM-DD}-{text}.mp3
```
- **Example**: `deep_voice_man-2025-11-06-this_is_a_test.mp3`

**General Rules:**
- **Name**: Converted to lowercase, special characters replaced with underscores
- **YYYY-MM-DD**: Current date
- **text**: Sanitized version of your input text (alphanumeric, spaces, hyphens, underscores only)
- **Maximum length**: 100 characters (text part is truncated if needed)

## Examples

### Using Custom Voices (Primary)

Generate speech with a custom voice (Joe Rogan):

```bash
python main.py --voice "voicedb78eca71747381369" --text "What's up party people, it's your boy Joe Rogan!"
```

Generate speech with another custom voice:

```bash
python main.py --voice "voice463769271747633951" --text "This is a test of the custom voice" --output custom_voice.mp3
```

### Using Built-in Voices (Secondary)

Generate a greeting with a built-in voice:

```bash
python main.py --voice "Friendly_Person" --text "Welcome to the AI voices demo!"
```

Generate speech with a built-in deep voice:

```bash
python main.py --voice "Deep_Voice_Man" --text "This is a test of the text-to-speech system" --output ./audio/test.mp3
```

## Command-line Options

- `--voice`: Voice ID to use (required)
- `--text`: Text to convert to speech (optional if using stdin)
- `--output`: Output file path (default: output.mp3)
- `--api-key`: fal.ai API key (or use FAL_KEY environment variable)
- `--list-voices`: List all available voice IDs
- `--poll-interval`: Seconds to wait between status checks (default: 2)

## Voice Configuration File

All voice definitions are now in a separate `voices.py` file, making it easy to manage without editing the main code.

**To add/remove/edit voices:**
1. Simply edit the `voices.py` file
2. Modify the `CUSTOM_VOICES` dictionary for your custom voices
3. The `BUILTIN_VOICES` list contains all fal.ai default voices

**File Structure:**
- `voices.py` - All voice definitions in one place
- `main.py` - Main application logic
- `rich_version.py` - Rich TUI interface
- `textual_version.py` - Textual TUI interface

This separation makes it easy to:
- Add custom voices without touching application code
- Version control your voice preferences
- Share voice configurations between different versions
- Keep voice management separate from functionality

## Managing Voices

### Custom Voices (Your Trained Voices)
Custom voices are your trained voice models and appear first in the voice list.

**Important:** Only add voice IDs that are currently active in your fal.ai account. Test voices before adding them!

**Step 1: Test the voice ID first**
```bash
python main.py --voice "your_voice_id" --text "test"
```

If it works (generates audio successfully), proceed to add it:

**Step 2: Add to voices.py**
1. Edit `voices.py`
2. Find the `CUSTOM_VOICES` dictionary
3. Add your voice using this format:
   ```python
   CUSTOM_VOICES = {
       "your_working_voice_id": "Your Display Name",
   }
   ```
4. Save the file

**Example:**
```python
CUSTOM_VOICES = {
    "voicedb123456789": "My Custom Voice",
}
```

**Note:** Voice IDs can become inactive over time. If a previously working voice starts failing with "voice with id X not found", you'll need to create a new voice on fal.ai and update the ID.

### Listing All Voices
Run `--list-voices` to see all available voices:
```bash
python main.py --list-voices
```

This shows:
- **Custom Voices** (your trained voices) - Primary
- **Built-in Voices** (fal.ai defaults) - Secondary

### Voice Categories

**Custom Voices** 🎤
- Your trained voice models
- Listed first with display names
- Use the voice ID from fal.ai when generating speech

**Built-in Voices** 🔧
- fal.ai's default voice models
- Listed second
- 17 different voice options

## How It Works

1. **Submit**: Sends your text and voice selection to the MiniMax Speech-02 HD API
2. **Queue**: The request is added to a processing queue
3. **Poll**: The script checks the status every few seconds until processing is complete
4. **Download**: Downloads the generated MP3 file to your specified location

The entire process typically takes 5-15 seconds depending on queue load and text length.

## Voice ID Reference

When using the `--voice` flag, you can use either:
- **Custom voice ID** (e.g., `voicedb78eca71747381369`)
- **Built-in voice ID** (e.g., `Wise_Woman`)

Both will be validated against the known voice list. Use `--list-voices` to see all options.

## Troubleshooting

**Error: API key required**
- Set the FAL_KEY environment variable or use the `--api-key` flag

**Error: Text too long**
- Maximum text length is 5000 characters

**Request fails**
- Check your API key is valid
- Ensure you have sufficient credits on fal.ai
- Verify your internet connection

## API Details

This tool uses the fal.ai MiniMax Speech-02 HD model:
- Endpoint: `https://queue.fal.run/fal-ai/minimax/speech-02-hd`
- Supports up to 5000 characters per request
- Returns MP3 audio files
- Standard queue-based processing

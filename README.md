# AI Voices - Text-to-Speech Generator

A command-line tool for generating speech from text with MiniMax Speech 2.8 (and BytePlus TTS) through [BudgetPixel](https://budgetpixel.com), the default provider, or through fal.ai.

## Features

- **BudgetPixel provider (default)**: Speech 2.8 HD/Turbo and BytePlus TTS, with a searchable voice catalog
- **fal.ai provider**: `--provider fal`, with custom voices from `voices.py` and 17 built-in voices
- Default voice `Robot_Armor`
- Files go to `output/` by default (`--output-dir` to change)
- Automatic polling until the request completes, then the MP3 is downloaded

## Installation

```bash
uv sync            # dependencies for running from the repo
mise run install   # installs the `voice` command into ~/.local/bin
```

`mise run install` runs `uv tool install --editable --force .`. Because the install is editable, `voice` works from any directory and still uses this repo's `fnox.toml` and `output/` folder; code changes apply without reinstalling. (`say` is not used as the name because macOS ships `/usr/bin/say`.)

## Setup

### BudgetPixel (default)

BudgetPixel's public API key (`bpx_…`) does not expose the speech models. Only the web app does, so the CLI authenticates with your web session:

1. Log in to [budgetpixel.com](https://budgetpixel.com) in your browser.
2. Open DevTools (⌥⌘I) → **Application** tab (Safari: **Storage**) → **Cookies** → `https://budgetpixel.com`, select `__Secure-next-auth.session-token`, and copy its **Value**.
3. Run `mise run login` (same as `fnox set BUDGETPIXEL_SESSION --provider age`) and paste it. It is stored age-encrypted in `fnox.toml`.

When the cookie expires, the CLI reports `session is invalid or expired`; repeat steps 1–3.

BudgetPixel requires 10–5000 characters of text.

### fal.ai

`--provider fal` needs a fal.ai API key ([fal.ai](https://fal.ai)), stored age-encrypted in `fnox.toml` as `FAL_API_KEY`.

### How secrets are loaded

`main.py` (and so `voice` and every mise task) reads `BUDGETPIXEL_SESSION` / `FAL_API_KEY` from the environment first, then falls back to `fnox get <KEY> -c <repo>/fnox.toml`. No `fnox exec` wrapper needed. `--api-key` still overrides the fal key.

## Quick Generation

```bash
voice the dead are dancing tonight          # default voice (Robot_Armor, Speech 2.8 HD); quotes optional
voice                                       # prompts for multi-line text, Ctrl+D to finish
voice --pick                                # search voices interactively, pick one, enter text
VOICE=Charming_Lady voice hello there       # one-off voice override
voice --provider fal --voice "Joe Rogan" "what's up party people"
```

Text with apostrophes needs quotes (or `\'`), since the shell reads it first.

The same from inside the repo via mise:

```bash
mise run say "the dead are dancing tonight"  # default voice
VOICE="Charming_Lady" mise run say hello     # one-off voice override
MODEL="speech-2.8-turbo" mise run say hello  # one-off model override
mise run voice                               # interactive voice picker
mise run voices robot                        # list voices (optional search term)
mise run models                              # list BudgetPixel models
mise run login                               # store/refresh the BudgetPixel cookie
```

The default voice is `$VOICE`, then `$DEFAULT_VOICE` (set to `Robot_Armor` in `mise.toml` for mise tasks), then `Robot_Armor`. Aliases: `mise run s`, `mise run v`. Files land in `output/`.

## Usage

### Interactive Mode

Use `--pick` to search the BudgetPixel catalog. Type a search term (e.g. `robot`), pick a number, then enter your text. With `--provider fal`, the original numbered menu (custom voices first, then built-in) is shown instead.

```bash
python main.py --pick
python main.py --pick --provider fal
```

### List all available voices

```bash
python main.py --list-voices                    # BudgetPixel, model from --model
python main.py --list-voices --search armor     # filtered
python main.py --list-models
python main.py --provider fal --list-voices
```

### Generate speech with arguments

When you don't specify `--output`, files are written to `output/` (or `--output-dir`) and named using this convention:
`{voice_id}-{YYYY-MM-DD}-{text}.mp3`

Example: `robot_armor-2026-10-30-hello_world.mp3` (max 100 characters)

```bash
python main.py --voice "Robot_Armor" --text "Hello world, this is the robot"
python main.py --voice "Charming_Lady" --model speech-2.8-turbo --text "Hello world"
python main.py --provider fal --voice "Wise_Woman" --text "Hello world"
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

### Using a fal.ai API key directly

```bash
python main.py --provider fal --voice "Lively_Girl" --text "Hello everyone!" --api-key "your-api-key-here"
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

- `--provider`: `budgetpixel` (default) or `fal`
- `--model`: BudgetPixel model: `speech-2.8-hd` (default), `speech-2.8-turbo`, `byteplus-tts`
- `--voice`: Voice ID (default: `$VOICE`, `$DEFAULT_VOICE`, then `Robot_Armor`)
- `--pick`: Choose the voice from the interactive picker
- `words…` / `--text`: Text to convert (plain trailing words, quotes optional; omitted → stdin prompt)
- `--output`: Output file path (overrides `--output-dir`)
- `--output-dir`: Folder for auto-named files (default: `output/` in the repo)
- `--api-key`: fal.ai API key (or use FAL_API_KEY environment variable)
- `--list-models`: List BudgetPixel models
- `--list-voices`: List voices for the selected provider/model
- `--search`: Filter `--list-voices` output
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
- Set the FAL_API_KEY environment variable or use the `--api-key` flag

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

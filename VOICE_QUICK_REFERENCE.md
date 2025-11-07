# Voice Management Quick Reference

## 📍 Location
All voice definitions are in: `voices.py`

## 🎯 Add a Custom Voice

```python
CUSTOM_VOICES = {
    "voice_id_from_fal": "Your Display Name",
}
```

**Example:**
```python
CUSTOM_VOICES = {
    "voicedb78eca71747381369": "Joe Rogan",
}
```

## 📁 File Naming Convention

**For Custom Voices:**
Uses the display name (sanitized) instead of voice ID!

```python
# If you have:
CUSTOM_VOICES = {
    "voicedb78eca71747381369": "Joe Rogan",
}

# Generated file will be:
joe_rogan-2025-11-06-your_text_here.mp3
#      ↑^^^^^^^^^  (display name, not voice ID!)
```

**For Built-in Voices:**
Uses the voice ID (sanitized) as before.

```python
# Built-in voice: Wise_Woman
wise_woman-2025-11-06-your_text_here.mp3
```

**Benefits:**
- ✅ No more cryptic voice IDs in filenames
- ✅ Easy to identify which voice was used
- ✅ Readable and user-friendly names

## 🗑️ Remove a Custom Voice

**Option 1: Delete the line**
```python
CUSTOM_VOICES = {
    "voice1": "Name 1",
    # "voice2": "Name 2",  ← Delete this line
    "voice3": "Name 3",
}
```

**Option 2: Empty the dictionary**
```python
CUSTOM_VOICES = {}
```

## ✏️ Change Display Name

```python
# Before:
"voicedb78": "Joe Rogan",

# After:
"voicedb78": "The Joe Rogan Voice",
```

**Note:** Changing the display name will change the filename!

## ✅ Test First!

Before adding a voice, test it works:
```bash
python main.py --voice "your_voice_id" --text "test"
```

## 📋 What You'll See

After adding custom voices, they'll appear **FIRST** in all voice lists:

```
🎤 CUSTOM VOICES (Your trained voices)
 1. Joe Rogan                    ← YOUR VOICES
 2. Your Custom Voice

🔧 BUILT-IN VOICES (fal.ai defaults)
 3. Wise_Woman                   ← BUILT-IN VOICES
 4. Friendly_Person
 ...
```

## 🎮 Works in All Versions

- `python main.py` (CLI)
- `uv run rich_version.py` (Rich TUI) ⭐ Recommended
- `uv run textual_version.py` (Textual TUI)

All versions use the same `voices.py` file!

## ⚠️ Important Notes

- Only add **working** voice IDs (test first!)
- Display name can be anything you want
- Voice ID must be exactly right (from fal.ai)
- Built-in voices list shouldn't be modified
- Changes take effect immediately (no restart needed)

---

**That's it!** Just edit the `CUSTOM_VOICES` dictionary in `voices.py`! 🎉

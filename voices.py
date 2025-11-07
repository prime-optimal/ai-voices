#!/usr/bin/env python3
"""
Voice Configuration for AI Voices Text-to-Speech

This file contains all voice definitions. Edit this file to:
- Add your custom voices
- Remove or modify existing voices
- Change display names

Custom voices (your trained voices) appear first in the list.
Built-in voices (fal.ai defaults) appear second.
"""

# Custom Voices (Primary) - Your trained voices
# To add a new custom voice:
# 1. First verify the voice ID works: python main.py --voice "voice_id" --text "test"
# 2. If it works, add it here using this format:
#    "voice_id_from_fal": "Display Name",
#
# NOTE: Only add voices that are currently active in your fal.ai account
CUSTOM_VOICES = {
    # Add your working custom voices here
    # Example:
    # "voicedb123456789": "Joe Rogan",
    # "voice987654321": "Custom Voice Name",
    "Voicedb78eca71747381369": "Joe Rogan",
    "Voicebe353c561762474627": "Sydney Sweeney"
}

# Built-in Voices (Secondary) - fal.ai's default voices
# These are the default voices provided by fal.ai
BUILTIN_VOICES = [
    "Wise_Woman",
    "Friendly_Person",
    "Inspirational_girl",
    "Deep_Voice_Man",
    "Calm_Woman",
    "Casual_Guy",
    "Lively_Girl",
    "Patient_Man",
    "Young_Knight",
    "Determined_Man",
    "Lovely_Girl",
    "Decent_Boy",
    "Imposing_Manner",
    "Elegant_Man",
    "Abbess",
    "Sweet_Girl_2",
    "Exuberant_Girl"
]

# Combined list of all valid voice IDs for validation
ALL_VOICE_IDS = list(CUSTOM_VOICES.keys()) + BUILTIN_VOICES

# Create reverse lookup for custom voices: display_name -> voice_id
VOICE_NAME_TO_ID = {name: id for id, name in CUSTOM_VOICES.items()}


def resolve_voice_id(voice_input):
    """
    Resolve voice input to actual voice ID.

    Args:
        voice_input: Either a voice ID or display name

    Returns:
        tuple: (actual_voice_id, display_name)
    """
    # If it's already a voice ID, return as-is
    if voice_input in ALL_VOICE_IDS:
        # Get display name if it's a custom voice
        display_name = CUSTOM_VOICES.get(voice_input, voice_input)
        return voice_input, display_name

    # If it's a display name, convert to voice ID
    if voice_input in VOICE_NAME_TO_ID:
        voice_id = VOICE_NAME_TO_ID[voice_input]
        return voice_id, voice_input

    # Unknown voice
    return voice_input, voice_input


def list_voices():
    """Display available voice IDs"""
    print("\n" + "=" * 60)
    print("🎤 CUSTOM VOICES (Your trained voices)")
    print("=" * 60)

    if CUSTOM_VOICES:
        for i, (voice_id, display_name) in enumerate(CUSTOM_VOICES.items(), 1):
            print(f"{i:2}. {display_name}")
            print(f"    ID: {voice_id}")
        print()
    else:
        print("   (No custom voices configured)")
        print("   To add a custom voice:")
        print("   1. Test that the voice ID works: python main.py --voice \"voice_id\" --text \"test\"")
        print("   2. If it works, add it to CUSTOM_VOICES in voices.py")
        print()

    print("=" * 60)
    print("🔧 BUILT-IN VOICES (fal.ai defaults)")
    print("=" * 60)
    for i, voice in enumerate(BUILTIN_VOICES, 1):
        print(f"{i:2}. {voice}")

    print("\n" + "=" * 60)
    print(f"Total: {len(CUSTOM_VOICES)} custom + {len(BUILTIN_VOICES)} built-in = {len(ALL_VOICE_IDS)} voices\n")


def select_voice_interactive():
    """
    Interactive voice selection menu.
    Returns the selected voice ID.
    """
    print("\n" + "=" * 60)
    print("🎤 SELECT A VOICE")
    print("=" * 60)

    voice_options = []
    option_num = 1

    # List custom voices first
    if CUSTOM_VOICES:
        print("\n📌 Custom Voices:")
        for voice_id, display_name in CUSTOM_VOICES.items():
            print(f"  {option_num}. {display_name}")
            print(f"     (ID: {voice_id})")
            voice_options.append(voice_id)
            option_num += 1
    else:
        print("\n📌 Custom Voices: (none configured)")

    # List built-in voices
    print("\n📌 Built-in Voices:")
    for voice in BUILTIN_VOICES:
        print(f"  {option_num}. {voice}")
        voice_options.append(voice)
        option_num += 1

    print(f"\n{'-' * 60}")
    print(f"Total: {len(voice_options)} voices available")
    print(f"{'-' * 60}")
    print("\nEnter the number of your choice (or 'q' to quit): ", end="")

    import sys
    while True:
        try:
            choice = input().strip().lower()

            # Check if user wants to quit
            if choice in ['q', 'quit', 'exit']:
                print("\n❌ Cancelled by user")
                sys.exit(0)

            # Try to convert to number
            choice_num = int(choice)

            # Check if valid range
            if 1 <= choice_num <= len(voice_options):
                selected_voice = voice_options[choice_num - 1]
                selected_display = CUSTOM_VOICES.get(selected_voice, selected_voice)
                print(f"\n✅ Selected: {selected_display}\n")
                return selected_voice
            else:
                print(f"❌ Please enter a number between 1 and {len(voice_options)} (or 'q' to quit): ", end="")

        except ValueError:
            print("❌ Please enter a valid number (or 'q' to quit): ", end="")
        except (EOFError, KeyboardInterrupt):
            print("\n\n❌ Cancelled by user")
            sys.exit(0)

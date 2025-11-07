#!/usr/bin/env python3
"""
AI Voice Generator - Textual TUI Version
A beautiful terminal UI for the text-to-speech generator
"""
from textual.app import App, ComposeResult
from textual.containers import Vertical, Horizontal
from textual.widgets import (
    Header,
    Footer,
    Button,
    Label,
    Input,
    Static,
    TextArea,
)
from textual.binding import Binding
import subprocess
import sys
import os

# Import voice data from voices.py
from voices import CUSTOM_VOICES, BUILTIN_VOICES, ALL_VOICE_IDS


class TextualTTSApp(App):
    """
    Textual TUI for AI Voice Generator
    """
    CSS = """
    .main {
        padding: 1;
    }

    .voice-section {
        height: 3;
        border: solid $primary;
        padding: 1;
    }

    .text-section {
        height: 10;
        border: solid $secondary;
        padding: 1;
        margin: 1 0;
    }

    .output-section {
        height: 1fr;
        border: solid $success;
        padding: 1;
    }

    .generate-btn {
        background: $success;
        color: $text;
        width: 100%;
    }

    .voice-list {
        background: $panel;
        color: $text;
        height: 100%;
        padding: 1;
        overflow: auto;
    }
    """

    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("g", "generate", "Generate"),
    ]

    def __init__(self):
        super().__init__()
        self.selected_voice = None
        self.text_content = ""

    def compose(self) -> ComposeResult:
        """Create the UI layout"""
        yield Header(show_clock=True)

        with Vertical(classes="main"):
            # Voice Selection
            with Vertical(classes="voice-section"):
                yield Label("🎤 Select Voice (by number)")
                voice_input = Input(
                    placeholder="Enter voice number (1-17)",
                    id="voice-input"
                )
                yield voice_input

            # Text Input
            with Vertical(classes="text-section"):
                yield Label("📝 Enter Text to Convert")
                yield TextArea(id="text-input")

            # Output with voice list
            with Vertical(classes="output-section"):
                yield Label("📊 Status, Voice List & Output")
                yield Static(self._format_voice_list() + "\n\n" + "Ready! Select a voice, enter text, and press 'g' to generate.", id="output-display")

            # Generate Button
            yield Button("✨ Generate Speech", id="generate-btn", classes="generate-btn")

        yield Footer()

    def on_mount(self) -> None:
        """App is now running - nothing needed here for now"""
        pass

    def _format_voice_list(self):
        """Format the voice list for display"""
        lines = []
        option_num = 1

        # Custom voices
        if CUSTOM_VOICES:
            lines.append("CUSTOM VOICES:")
            for voice_id, display_name in CUSTOM_VOICES.items():
                lines.append(f"{option_num}. {display_name} ({voice_id})")
                option_num += 1
            lines.append("")

        # Built-in voices
        lines.append("BUILT-IN VOICES:")
        for voice in BUILTIN_VOICES:
            lines.append(f"{option_num}. {voice}")
            option_num += 1

        return "\n".join(lines)

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle voice input submission"""
        if event.input.id == "voice-input":
            self._handle_voice_selection(event.value)

    def _handle_voice_selection(self, value: str):
        """Handle voice selection by number"""
        try:
            choice = int(value)
            option_num = 1

            # Check custom voices
            for voice_id, display_name in CUSTOM_VOICES.items():
                if choice == option_num:
                    self.selected_voice = voice_id
                    display = self._format_voice_list() + f"\n\n✅ Selected: {display_name} ({voice_id})\nPress 'g' to generate!"
                    self.query_one("#output-display", Static).update(display)
                    return
                option_num += 1

            # Check built-in voices
            for voice in BUILTIN_VOICES:
                if choice == option_num:
                    self.selected_voice = voice
                    display = self._format_voice_list() + f"\n\n✅ Selected: {voice}\nPress 'g' to generate!"
                    self.query_one("#output-display", Static).update(display)
                    return
                option_num += 1

            # Invalid choice
            display = self._format_voice_list() + f"\n\n❌ Invalid choice: {choice}\nPlease enter a number between 1 and {option_num - 1}"
            self.query_one("#output-display", Static).update(display)

        except ValueError:
            display = self._format_voice_list() + f"\n\n❌ Invalid input: '{value}'\nPlease enter a number (1-17)"
            self.query_one("#output-display", Static).update(display)

    def on_text_area_changed(self, event: TextArea.Changed) -> None:
        """Handle text input"""
        self.text_content = event.text_area.text

    def action_generate(self) -> None:
        """Generate speech"""
        self.generate_speech()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press"""
        if event.button.id == "generate-btn":
            self.generate_speech()

    def generate_speech(self) -> None:
        """Generate speech using the CLI version"""
        if not self.selected_voice:
            self.query_one("#output-display", Static).update(
                "❌ Please select a voice first! (Enter a number in the voice field)"
            )
            return

        if not self.text_content.strip():
            self.query_one("#output-display", Static).update(
                "❌ Please enter some text first!"
            )
            return

        api_key = os.environ.get("FAL_KEY")
        if not api_key:
            self.query_one("#output-display", Static).update(
                "❌ Please set FAL_KEY environment variable\n\n"
                "export FAL_KEY='your-api-key-here'"
            )
            return

        output = self.query_one("#output-display", Static)
        output.update("🚀 Generating speech...\n\n")
        self.log(f"Generating with voice: {self.selected_voice}")
        self.log(f"Text: {self.text_content[:50]}...")

        try:
            result = subprocess.run(
                [sys.executable, "main.py", "--voice", self.selected_voice, "--text", self.text_content],
                capture_output=True,
                text=True,
                env={**os.environ, "FAL_KEY": api_key},
            )

            if result.returncode == 0:
                output.update(f"✅ Success!\n\n{result.stdout}")
            else:
                output.update(f"❌ Generation failed:\n\n{result.stderr}")
        except Exception as e:
            output.update(f"❌ Error: {str(e)}")


if __name__ == "__main__":
    app = TextualTTSApp()
    app.run()

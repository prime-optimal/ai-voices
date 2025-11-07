#!/usr/bin/env python3
"""
AI Voice Generator - Rich + Prompt Toolkit Version
A beautiful command-line TUI for the text-to-speech generator
"""
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.spinner import Spinner
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich import print as rprint
from rich.text import Text
from rich.tree import Tree
from rich import box
import sys
import os
from pathlib import Path

# Import voice data from main.py
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from main import CUSTOM_VOICES, BUILTIN_VOICES, ALL_VOICE_IDS


console = Console()

def show_welcome():
    """Show welcome screen"""
    welcome_text = """
    ██████╗ ███╗   ██╗ █████╗ ███╗   ██╗    ██╗   ██╗██████╗ ███████╗
    ██╔══██╗████╗  ██║██╔══██╗████╗  ██║    ██║   ██║██╔══██╗██╔════╝
    ██████╔╝██╔██╗ ██║╚█████╔╝██╔██╗ ██║    ██║   ██║██████╔╝█████╗
    ██╔══██╗██║╚██╗██║██╔══██╗██║╚██╗██║    ██║   ██║██╔═══╝ ██╔══╝
    ██║  ██║██║ ╚████║╚█████╔╝██║ ╚████║    ╚██████╔╝██║     ███████╗
    ╚═╝  ╚═╝╚═╝  ╚═══╝ ╚════╝ ╚═╝  ╚═══╝     ╚═════╝ ╚═╝     ╚══════╝

    [bold cyan]AI Voice Generator - Text-to-Speech with Rich UI[/]
    """
    console.print(welcome_text)
    console.print()


def get_api_key():
    """Get and validate API key"""
    api_key = os.environ.get("FAL_KEY")

    if not api_key:
        console.print("[yellow]⚠️  FAL_KEY environment variable not set[/]")
        api_key = Prompt.ask("Enter your fal.ai API key", password=True)

        if not api_key:
            console.print("[red]❌ API key is required![/]")
            return None

    return api_key


def select_voice():
    """Interactive voice selection using Rich"""
    console.print("\n[bold]🎤 SELECT A VOICE[/bold]\n")

    # Create a table for voice selection
    table = Table(show_header=True, header_style="bold magenta", box=box.ROUNDED)
    table.add_column("#", style="dim", width=4)
    table.add_column("Voice", style="cyan")
    table.add_column("Type", style="green", width=15)

    voice_options = []
    option_num = 1

    # Add custom voices
    if CUSTOM_VOICES:
        table.add_section()
        for voice_id, display_name in CUSTOM_VOICES.items():
            table.add_row(
                str(option_num),
                f"[bold]{display_name}[/]",
                "[yellow]Custom[/]"
            )
            voice_options.append(("custom", voice_id, display_name))
            option_num += 1

    # Add built-in voices
    table.add_section()
    for voice in BUILTIN_VOICES:
        table.add_row(
            str(option_num),
            f"[cyan]{voice}[/]",
            "[blue]Built-in[/]"
        )
        voice_options.append(("built-in", voice, voice))
        option_num += 1

    console.print(table)

    # Selection prompt
    while True:
        choice = Prompt.ask(
            "\n[bold]Select a voice[/bold]",
            choices=[str(i) for i in range(1, len(voice_options) + 1)] + ["q"],
            default="1"
        )

        if choice.lower() == "q":
            console.print("[yellow]Cancelled[/]")
            return None

        try:
            idx = int(choice) - 1
            if 0 <= idx < len(voice_options):
                voice_type, voice_id, display_name = voice_options[idx]
                console.print(f"\n[green]✅ Selected: {display_name}[/] ([dim]{voice_type}[/])\n")
                return voice_id
        except ValueError:
            console.print("[red]Invalid choice. Try again.[/]")


def get_text_input():
    """Get text input from user"""
    console.print("[bold]📝 ENTER TEXT[/bold]\n")
    console.print("Type your text below (press [bold]Ctrl+D[/bold] or [bold]Enter twice[/bold] to finish):\n")

    lines = []
    try:
        while True:
            line = Prompt.ask("", default="", show_default=False)
            if line == "" and lines:
                break
            lines.append(line)
    except (EOFError, KeyboardInterrupt):
        pass

    if not lines:
        console.print("[yellow]No text entered[/]")
        return None

    text = "\n".join(lines)
    console.print(f"\n[green]✅ Text captured: {len(text)} characters[/]\n")
    return text


def show_generation_status(voice_id, text):
    """Show generation in progress with rich formatting"""
    console.print("\n[bold]🚀 GENERATION IN PROGRESS[/bold]\n")

    # Status panel
    status_panel = Panel(
        f"Voice: [cyan]{voice_id}[/]\n"
        f"Text: [cyan]{text[:50]}{'...' if len(text) > 50 else ''}[/]\n",
        title="[bold]Processing[/]",
        border_style="blue",
        padding=(1, 2)
    )
    console.print(status_panel)

    # Spinner
    with Progress(
        SpinnerColumn(),
        TextColumn("[bold blue]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Generating speech...", total=None)
        # Note: In a real implementation, you'd hook into the actual generation process
        # For now, we'll just show the spinner


def confirm_generate():
    """Ask for confirmation before generating"""
    return Confirm.ask("\n[bold]Generate speech now?[/bold]")


def main():
    """Main application loop"""
    try:
        # Show welcome
        show_welcome()

        # Get API key
        api_key = get_api_key()
        if not api_key:
            return 1

        # Select voice
        voice_id = select_voice()
        if not voice_id:
            return 0

        # Get text
        text = get_text_input()
        if not text:
            return 0

        # Confirm
        if not confirm_generate():
            console.print("[yellow]Generation cancelled[/]")
            return 0

        # Show generation status
        show_generation_status(voice_id, text)

        # Call the actual generation function
        console.print("\n[bold cyan]🚀 Calling CLI to generate...[/]\n")

        import subprocess
        result = subprocess.run(
            [sys.executable, "main.py", "--voice", voice_id, "--text", text],
            capture_output=True,
            text=True,
            env={**os.environ, "FAL_KEY": api_key},
        )

        # Display the result
        if result.returncode == 0:
            console.print("[bold green]✅ Generation Successful![/]")
            console.print()
            console.print(result.stdout)
        else:
            console.print("[bold red]❌ Generation Failed![/]")
            console.print()
            console.print(f"[red]{result.stderr}[/]")

        return result.returncode

    except KeyboardInterrupt:
        console.print("\n[yellow]Cancelled by user[/]")
        return 0
    except Exception as e:
        console.print(f"\n[red bold]Error: {str(e)}[/]")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)

#!/usr/bin/env python3
"""Generate ElevenLabs voice audio from a game JSON file.

Usage:
    python generate_audio.py <game.json> [--output <dir>]

Requires ELEVENLABS_API_KEY environment variable.

Each AI model gets a unique voice ID. Configure in VOICE_MAP below.
Outputs one .mp3 per statement: r{round}-sr{sub_round}-{player}.mp3
Also generates confessional audio with a whispered style.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

# Voice IDs per character — configure these after selecting voices in ElevenLabs
# Default IDs are placeholders; replace with your actual voice IDs.
VOICE_MAP = {
    "Claude": os.environ.get("VOICE_ID_CLAUDE", "pNInz6obpgDQGcFmaJgB"),   # Adam
    "GPT": os.environ.get("VOICE_ID_GPT", "ErXwobaYiN019PkySvjV"),         # Antoni
    "Gemini": os.environ.get("VOICE_ID_GEMINI", "VR6AewLTigWG4xSOukaG"),   # Arnold
    "DeepSeek": os.environ.get("VOICE_ID_DEEPSEEK", "pqHfZKP75CvOlQylNhV4"),  # Bill
    "Llama": os.environ.get("VOICE_ID_LLAMA", "nPczCjzI2devNBz1zQrb"),     # Brian
}

# ElevenLabs model and settings
TTS_MODEL = "eleven_turbo_v2"
VOICE_SETTINGS_NORMAL = {
    "stability": 0.5,
    "similarity_boost": 0.75,
    "style": 0.3,
}
VOICE_SETTINGS_CONFESSIONAL = {
    "stability": 0.6,
    "similarity_boost": 0.75,
    "style": 0.1,  # More subdued for confessional
}


def generate_speech(text: str, voice_id: str, settings: dict, output_path: Path) -> None:
    """Call ElevenLabs TTS API and save audio to file."""
    try:
        import httpx
    except ImportError:
        print("ERROR: httpx not installed. Run: pip install httpx", file=sys.stderr)
        sys.exit(1)

    api_key = os.environ.get("ELEVENLABS_API_KEY")
    if not api_key:
        print("ERROR: ELEVENLABS_API_KEY not set", file=sys.stderr)
        sys.exit(1)

    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
    headers = {
        "xi-api-key": api_key,
        "Content-Type": "application/json",
    }
    payload = {
        "text": text,
        "model_id": TTS_MODEL,
        "voice_settings": settings,
    }

    response = httpx.post(url, json=payload, headers=headers, timeout=30.0)
    response.raise_for_status()

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(response.content)
    print(f"  -> {output_path.name} ({len(response.content) / 1024:.1f} KB)")


def process_game(game_path: Path, output_dir: Path) -> None:
    """Generate audio for all statements in a game."""
    with open(game_path) as f:
        game = json.load(f)

    game_id = game["game_id"]
    total_files = 0

    for rnd in game["rounds"]:
        round_num = rnd["round_number"]

        for stmt in rnd["statements"]:
            player = stmt["player"]
            sub_round = stmt.get("sub_round", 1)
            voice_id = VOICE_MAP.get(player)

            if not voice_id:
                print(f"  WARN: No voice configured for {player}, skipping")
                continue

            # Public statement audio
            public_file = output_dir / game_id / f"r{round_num}-sr{sub_round}-{player}.mp3"
            if not public_file.exists():
                print(f"  Generating: {player} R{round_num} SR{sub_round} (public)")
                generate_speech(stmt["public_text"], voice_id, VOICE_SETTINGS_NORMAL, public_file)
                total_files += 1
            else:
                print(f"  Skipping (exists): {public_file.name}")

            # Confessional audio (private reasoning, whispered style)
            confessional_file = output_dir / game_id / f"r{round_num}-sr{sub_round}-{player}-confessional.mp3"
            if not confessional_file.exists():
                print(f"  Generating: {player} R{round_num} SR{sub_round} (confessional)")
                generate_speech(
                    stmt["private_reasoning"], voice_id, VOICE_SETTINGS_CONFESSIONAL, confessional_file
                )
                total_files += 1
            else:
                print(f"  Skipping (exists): {confessional_file.name}")

    print(f"\nDone! Generated {total_files} audio files in {output_dir / game_id}/")


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate ElevenLabs audio from game JSON")
    parser.add_argument("game_json", type=Path, help="Path to game JSON file")
    parser.add_argument(
        "--output", "-o", type=Path, default=Path("audio_output"),
        help="Output directory (default: audio_output/)"
    )
    args = parser.parse_args()

    if not args.game_json.exists():
        print(f"ERROR: {args.game_json} not found", file=sys.stderr)
        sys.exit(1)

    print(f"Processing: {args.game_json}")
    process_game(args.game_json, args.output)


if __name__ == "__main__":
    main()

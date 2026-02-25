#!/usr/bin/env bash
set -euo pipefail

# ═══════════════════════════════════════════════════════
#  ModelArena — Episode Production Pipeline
#
#  Usage: ./produce-episode.sh <episode-id> [num-games]
#  Example: ./produce-episode.sh ep001 10
#
#  Steps:
#    1. Run games (CLI)
#    2. PAUSE — you pick the main event game
#    3. Generate audio (ElevenLabs)
#    4. Copy main event to video pipeline
#    5. Render video (Remotion)
#
#  Requires: .env with API keys, ffmpeg, node
# ═══════════════════════════════════════════════════════

EPISODE_ID="${1:?Usage: ./produce-episode.sh <episode-id> [num-games]}"
NUM_GAMES="${2:-10}"
RESULTS_DIR="results/${EPISODE_ID}"

echo ""
echo "╔═══════════════════════════════════════╗"
echo "║  MODEL ARENA — Episode Production     ║"
echo "╠═══════════════════════════════════════╣"
echo "║  Episode:  ${EPISODE_ID}                      ║"
echo "║  Games:    ${NUM_GAMES}                             ║"
echo "╚═══════════════════════════════════════╝"
echo ""

# ─── Step 1: Run games ───────────────────────────────
echo "▸ STEP 1: Running ${NUM_GAMES} Mafia games..."
echo ""

python -m engine.cli mafia \
    --games "${NUM_GAMES}" \
    --episode-id "${EPISODE_ID}" \
    --output results

echo ""
echo "Games written to: ${RESULTS_DIR}/"
echo ""

# ─── Step 2: Pick main event ─────────────────────────
echo "═══════════════════════════════════════════"
echo ""
echo "  Game files:"
echo ""
for f in "${RESULTS_DIR}/${EPISODE_ID}"-*.json; do
    if [ -f "$f" ]; then
        GAME_ID=$(python -c "import json; d=json.load(open('$f')); print(f\"{d['game_id']}  |  Mafia: {d['mafia_player']:<10}  Winner: {d['winner']:<6}  Rounds: {d['total_rounds']}\")")
        echo "    $GAME_ID"
    fi
done

echo ""
echo "═══════════════════════════════════════════"
echo ""
echo "  Review the game logs above."
echo "  Pick the most entertaining game as the main event."
echo ""
read -rp "  Enter game ID (e.g. ${EPISODE_ID}-001): " MAIN_EVENT
echo ""

MAIN_EVENT_FILE="${RESULTS_DIR}/${MAIN_EVENT}.json"
if [ ! -f "${MAIN_EVENT_FILE}" ]; then
    echo "ERROR: ${MAIN_EVENT_FILE} not found"
    exit 1
fi

echo "  Main event: ${MAIN_EVENT}"
echo ""

# ─── Step 3: Generate audio ──────────────────────────
echo "▸ STEP 3: Generating audio for main event..."
echo ""

if [ -z "${ELEVENLABS_API_KEY:-}" ]; then
    echo "  ELEVENLABS_API_KEY not set — skipping audio generation."
    echo "  Set it in .env to generate voice audio."
    echo ""
else
    python video/scripts/generate_audio.py \
        "${MAIN_EVENT_FILE}" \
        --output video/public/audio
    echo ""
fi

# ─── Step 4: Copy to video pipeline ──────────────────
echo "▸ STEP 4: Setting up video pipeline..."
echo ""

cp "${MAIN_EVENT_FILE}" video/src/sample-data/game.json
cp "${RESULTS_DIR}/stats.json" video/src/sample-data/stats.json
echo "  Copied game + stats to video/src/sample-data/"
echo ""

# ─── Step 5: Render video ────────────────────────────
echo "▸ STEP 5: Rendering video..."
echo ""

if ! command -v ffmpeg &> /dev/null; then
    echo "  ffmpeg not installed — skipping video render."
    echo "  Install with: apt install ffmpeg"
    echo "  Then render manually:"
    echo "    cd video && npx remotion render src/index.ts Episode --output out/${EPISODE_ID}.mp4"
    echo ""
else
    cd video
    npx remotion render src/index.ts Episode \
        --output "out/${EPISODE_ID}.mp4" \
        --concurrency 4
    cd ..
    echo ""
    echo "  Video rendered: video/out/${EPISODE_ID}.mp4"
    echo ""
fi

# ─── Done ─────────────────────────────────────────────
echo "╔═══════════════════════════════════════╗"
echo "║  DONE                                 ║"
echo "╠═══════════════════════════════════════╣"
echo "║  Results:  ${RESULTS_DIR}/            ║"
echo "║  Main:     ${MAIN_EVENT}              ║"
echo "╚═══════════════════════════════════════╝"
echo ""
echo "Next steps:"
echo "  1. Review the video"
echo "  2. git add results/ && git commit"
echo "  3. Push to deploy website"
echo "  4. Upload video to YouTube"
echo ""

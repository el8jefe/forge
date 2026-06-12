#!/bin/bash
# FORGE nightly launcher — run this before you go to sleep.
# Starts the pipeline scheduler in the background.
# Runs at midnight, 6am, noon, and 6pm automatically.

cd "$(dirname "$0")"

# Safety: never run live sends if TEST_MODE is still true
CURRENT_MODE=$(grep -i "^TEST_MODE" .env 2>/dev/null | cut -d'=' -f2 | tr -d ' ')
if [[ "$CURRENT_MODE" == "true" ]]; then
  echo ""
  echo "⚠️  WARNING: TEST_MODE=true in your .env"
  echo "   Emails will be routed to your own address, not real leads."
  echo "   To go live, set TEST_MODE=false in .env"
  echo ""
  read -p "Continue in test mode? (y/n): " confirm
  [[ "$confirm" != "y" ]] && echo "Aborted." && exit 1
fi

# Kill any existing scheduler so there's never two running at once
EXISTING=$(pgrep -f "agent.py --schedule" 2>/dev/null)
if [[ -n "$EXISTING" ]]; then
  echo "Stopping existing scheduler (PID $EXISTING)..."
  kill "$EXISTING"
  sleep 2
fi

LOG_FILE="$(pwd)/scheduler.log"
echo ""
echo "Starting FORGE scheduler..."
echo "  Logs: $LOG_FILE"
echo "  Runs: midnight · 6am · noon · 6pm"
echo "  Stop: kill \$(cat forge.pid)"
echo ""

nohup python3 agent.py --schedule >> "$LOG_FILE" 2>&1 &
echo $! > forge.pid
echo "Scheduler running (PID $(cat forge.pid)). Safe to close terminal. Good night."

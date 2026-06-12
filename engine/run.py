"""
run.py — RETIRED (Phase 4)

The Flask platform has been replaced by:
  - Web UI:  forge/web  (Next.js on port 3000)
  - API:     forge/engine/api.py  (FastAPI on port 8000)

See engine/platform/RETIRED.md for migration notes.
"""

import sys

print(
    "\nFORGE Flask platform is retired (Phase 4).\n"
    "  Web:  cd forge/web && npm run dev\n"
    "  API:  cd forge/engine && python3 api.py\n"
    "  Docs: engine/platform/RETIRED.md\n",
    file=sys.stderr,
)
raise SystemExit(1)

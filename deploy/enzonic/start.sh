#!/usr/bin/env sh
# Enzonic Python (always-on runtime), not Enzonic Deploy or Minecraft free tier.
# Set panel Startup Command: sh deploy/enzonic/start.sh
set -eu
cd "$(dirname "$0")/../.."
: "${PORT:=10000}"
export PORT
export PYTHONUNBUFFERED=1
export PYTHONDONTWRITEBYTECODE=1
echo "MATCHLAB AZ: verifying 506207 registry records before public startup"
python3 prepare_database.py
python3 -c 'import world_db; counts=world_db.counts(); assert counts and counts.get("total")==506207, "SQLite registry integrity check failed"; print("SQLite verified:", counts["total"])'
exec python3 hosting_server.py

"""Enzonic Python Generic main-file entrypoint for MATCHLAB AZ.

Enzonic's panel launches main.py. Prepare and verify the world registry
before accepting connections so users never receive partial API data.
"""
import os

def main():
    os.environ.setdefault("PYTHONUNBUFFERED", "1")
    from prepare_database import main as prepare_database
    prepare_database()
    import world_db
    counts = world_db.counts()
    if not counts or counts.get("total") != 506207:
        raise RuntimeError("MATCHLAB AZ: verified football registry is unavailable")
    from hosting_server import main as start_http
    start_http()

if __name__ == "__main__":
    main()

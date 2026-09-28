import hashlib
import json
from datetime import datetime
from pathlib import Path

LOG_FILE = Path("audit_log.jsonl")

def _hash_entry(entry: dict) -> str:
    """Compute SHA-256 hash of a log entry."""
    payload = json.dumps(entry, sort_keys=True).encode()
    return hashlib.sha256(payload).hexdigest()

def log_event(event_type: str, detail: str, model: str = "", metadata: dict = None):
    """Append a tamper-evident entry to the audit log."""
    # Get previous hash
    prev_hash = "GENESIS"
    if LOG_FILE.exists():
        with open(LOG_FILE, "r") as f:
            lines = f.readlines()
            if lines:
                last = json.loads(lines[-1])
                prev_hash = last.get("hash", "GENESIS")

    entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "event": event_type,
        "detail": detail,
        "model": model,
        "metadata": metadata or {},
        "prev_hash": prev_hash,
    }
    entry["hash"] = _hash_entry(entry)

    with open(LOG_FILE, "a") as f:
        f.write(json.dumps(entry) + "\n")

    return entry

def verify_chain() -> tuple[bool, int]:
    """Verify the entire audit chain is intact. Returns (is_valid, num_entries)."""
    if not LOG_FILE.exists():
        return True, 0

    prev_hash = "GENESIS"
    count = 0
    with open(LOG_FILE, "r") as f:
        for line in f:
            entry = json.loads(line)
            if entry["prev_hash"] != prev_hash:
                return False, count
            # Recompute hash without the hash field
            check = {k: v for k, v in entry.items() if k != "hash"}
            if _hash_entry(check) != entry["hash"]:
                return False, count
            prev_hash = entry["hash"]
            count += 1
    return True, count

def get_recent_logs(n: int = 10) -> list:
    """Return the last n audit entries."""
    if not LOG_FILE.exists():
        return []
    with open(LOG_FILE, "r") as f:
        lines = f.readlines()
    return [json.loads(line) for line in lines[-n:]]
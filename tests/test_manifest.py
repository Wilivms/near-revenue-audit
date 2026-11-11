"""The committed raw snapshots are exactly the ones listed in data/raw/MANIFEST.json."""
import json

from src.manifest import MANIFEST, entries


def test_manifest_matches_raw_files():
    listed = json.loads(MANIFEST.read_text())["files"]
    actual = entries()
    assert set(actual) == set(listed), f"unlisted or missing: {sorted(set(actual) ^ set(listed))[:5]}"
    changed = [k for k in actual if actual[k]["sha256"] != listed[k]["sha256"]]
    assert not changed, f"changed since the manifest: {changed[:5]}"

from pathlib import Path
import json
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from backend.app.core.learning.unified_dataset_builder import build_default_unified_learning_dataset


def main() -> int:
    manifest = build_default_unified_learning_dataset()
    manifest_path = Path(manifest["artifacts"]["dataset"]).with_name("manifest.json")
    print(json.dumps({"status": "ok", "manifest_path": str(manifest_path), **manifest}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

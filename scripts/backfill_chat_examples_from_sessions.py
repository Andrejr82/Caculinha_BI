from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


from backend.app.core.learning.chat_example_backfill import backfill_examples_from_session_db
from backend.app.core.utils.session_manager import SessionManager


def main() -> int:
    result = backfill_examples_from_session_db(db_path=str(SessionManager.default_db_path()))
    print(
        "chat_example_backfill",
        f"scanned={result['scanned']}",
        f"captured={result['captured']}",
        f"skipped={result['skipped']}",
        f"duplicates={result['duplicates']}",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

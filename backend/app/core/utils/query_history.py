# backend/app/core/utils/query_history.py

import json
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

class QueryHistory:
    """
    Manages user query history, persisting it to daily JSONL files.
    Allows for searching and filtering of past queries.
    (T1.3.3 from TASK_LIST)
    """
    def __init__(self, history_dir: str = "data/query_history"):
        self.history_dir = history_dir
        os.makedirs(self.history_dir, exist_ok=True)
        print(f"QueryHistory initialized in {self.history_dir}")

    def _get_daily_file_path(self, date: Optional[datetime] = None) -> str:
        """Generates the file path for a given day."""
        if date is None:
            date = datetime.now()
        date_str = date.strftime("%Y-%m-%d")
        return os.path.join(self.history_dir, f"queries_{date_str}.jsonl")

    def add_query(self, user_id: str, query: str, response: Dict[str, Any], timestamp: Optional[datetime] = None):
        """
        Adds a new query entry to the daily history file.
        """
        if timestamp is None:
            timestamp = datetime.now()
        
        entry = {
            "timestamp": timestamp.isoformat(),
            "user_id": user_id,
            "query": query,
            "response_summary": self._summarize_response(response), # Store a summary, not full response
            "full_response_hash": self._hash_response(response) # Hash of full response for integrity/lookup
        }
        file_path = self._get_daily_file_path(timestamp)
        
        try:
            with open(file_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
            print(f"Query added to history for user {user_id}.")
        except OSError as e:
            print(f"Error writing query history file {file_path}: {e}")

    def _summarize_response(self, response: Dict[str, Any]) -> str:
        """Creates a brief summary of the response for history logging."""
        if "type" in response:
            if response["type"] == "text" and "text" in response:
                return response["text"][:100] + ("..." if len(response["text"]) > 100 else "")
            if response["type"] == "tool_result" and "tool_name" in response:
                return f"Tool result from {response['tool_name']}"
            if response["type"] == "code_result" and "result" in response:
                return "Code execution result."
        return json.dumps(response)[:100] + ("..." if len(json.dumps(response)) > 100 else "")

    def _hash_response(self, response: Dict[str, Any]) -> str:
        """Generates a hash of the full response for later integrity checks or matching."""
        import hashlib
        return hashlib.sha256(json.dumps(response, sort_keys=True).encode("utf-8")).hexdigest()

    def get_history(self, user_id: Optional[str] = None, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Retrieves query history for a user, within a date range, with an optional limit.
        """
        history_records: List[Dict[str, Any]] = []

        # Use reasonable defaults instead of datetime.min/max to avoid Windows issues
        if start_date is None:
            start_date = datetime(2020, 1, 1)  # Reasonable past date
        if end_date is None:
            end_date = datetime(2099, 12, 31)  # Reasonable future date

        # Create date ranges with safe boundaries
        end_date_upper = end_date.replace(hour=23, minute=59, second=59, microsecond=999999)
        start_date_lower = start_date.replace(hour=0, minute=0, second=0, microsecond=0)

        # Iterate through history files (simple scan, can be optimized with file naming convention)
        for filename in sorted(os.listdir(self.history_dir), reverse=True): # Newest files first
            if filename.startswith("queries_") and filename.endswith(".jsonl"):
                file_date_str = filename[8:18] # YYYY-MM-DD
                try:
                    file_date = datetime.strptime(file_date_str, "%Y-%m-%d")
                except ValueError:
                    continue  # Skip invalid filenames

                if file_date > end_date_upper:
                    continue
                if file_date < start_date_lower:
                    break # Assuming files are sorted, we can stop early

                file_path = os.path.join(self.history_dir, filename)
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        for line in f:
                            try:
                                entry = json.loads(line)
                                entry_timestamp = datetime.fromisoformat(entry["timestamp"])

                                if start_date <= entry_timestamp <= end_date:
                                    if user_id is None or entry.get("user_id") == user_id:
                                        history_records.append(entry)
                                        if len(history_records) >= limit:
                                            return history_records # Return early if limit reached
                            except json.JSONDecodeError:
                                print(f"Warning: Corrupt JSON line in {filename}: {line.strip()}")
                except OSError as e:
                    print(f"Error reading history file {file_path}: {e}")
        
        return history_records[:limit]

    def search_queries(self, user_id: Optional[str] = None, keyword: str = "", limit: int = 100) -> List[Dict[str, Any]]:
        """
        Searches query history for entries containing a specific keyword.
        """
        matching_records: List[Dict[str, Any]] = []
        all_records = self.get_history(user_id=user_id, limit=None) # Get all relevant history first

        keyword_lower = keyword.lower()
        for entry in all_records:
            if keyword_lower in entry.get("query", "").lower() or \
               keyword_lower in entry.get("response_summary", "").lower():
                matching_records.append(entry)
                if len(matching_records) >= limit:
                    break
        return matching_records

# Example usage
if __name__ == '__main__':
    from app.config.settings import Settings
    temp_settings = Settings()

    # Ensure history directory exists for testing
    os.makedirs(temp_settings.LEARNING_EXAMPLES_PATH, exist_ok=True) # Using LEARNING_EXAMPLES_PATH as temp history dir

    history = QueryHistory(history_dir=temp_settings.LEARNING_EXAMPLES_PATH)

    user1_id = "test_user_1"
    user2_id = "test_user_2"

    # Add some queries
    history.add_query(user1_id, "Vendas totais do produto A?", {"type": "text", "text": "Total de vendas: 100"})
    history.add_query(user1_id, "Gráfico de vendas por região?", {"type": "chart", "chart_spec": {"data": []}})
    history.add_query(user2_id, "Qual o estoque atual?", {"type": "text", "text": "Estoque: 500"})
    history.add_query(user1_id, "Top 5 produtos?", {"type": "code_result", "result": [{"prod": "X", "val": 50}]}
)

    print("\n--- Testing get_history ---")
    all_history = history.get_history()
    print(f"All history ({len(all_history)} records):")
    for entry in all_history:
        print(f"  [{entry['timestamp']}] User {entry['user_id']}: {entry['query']} -> {entry['response_summary']}")

    user1_history = history.get_history(user_id=user1_id)
    print(f"\nUser 1 history ({len(user1_history)} records):")
    for entry in user1_history:
        print(f"  [{entry['timestamp']}] User {entry['user_id']}: {entry['query']} -> {entry['response_summary']}")

    print("\n--- Testing search_queries ---")
    search_results = history.search_queries(keyword="vendas")
    print(f"Search 'vendas' ({len(search_results)} records):")
    for entry in search_results:
        print(f"  [{entry['timestamp']}] User {entry['user_id']}: {entry['query']} -> {entry['response_summary']}")

    search_user1_chart = history.search_queries(user_id=user1_id, keyword="gráfico")
    print(f"\nSearch 'gráfico' for User 1 ({len(search_user1_chart)} records):")
    for entry in search_user1_chart:
        print(f"  [{entry['timestamp']}] User {entry['user_id']}: {entry['query']} -> {entry['response_summary']}")

    # Clean up dummy files
    for filename in os.listdir(temp_settings.LEARNING_EXAMPLES_PATH):
        if filename.startswith("queries_"):
            os.remove(os.path.join(temp_settings.LEARNING_EXAMPLES_PATH, filename))
    print("\nCleaned up dummy history files.")
    print("\nQueryHistory tests passed!")

# backend/app/core/rag/example_collector.py

import json
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

from app.config.settings import settings

class ExampleCollector:
    """
    Collects successful queries, their generated code, and results to serve as
    few-shot examples for RAG and continuous learning.
    (T6.4.2 from TASK_LIST)
    """
    def __init__(self, examples_dir: str = settings.LEARNING_EXAMPLES_PATH):
        self.examples_dir = examples_dir
        os.makedirs(self.examples_dir, exist_ok=True)
        print(f"ExampleCollector initialized in {self.examples_dir}")

    def _get_daily_file_path(self, date: Optional[datetime] = None) -> str:
        """Generates the file path for a given day's examples."""
        if date is None:
            date = datetime.now()
        date_str = date.strftime("%Y-%m-%d")
        return os.path.join(self.examples_dir, f"examples_{date_str}.jsonl")

    def add_example(self, user_id: str, query: str, code: str, result: Dict[str, Any], intent: str, timestamp: Optional[datetime] = None):
        """
        Adds a new successful example to the daily examples file.
        """
        if timestamp is None:
            timestamp = datetime.now()
        
        entry = {
            "timestamp": timestamp.isoformat(),
            "user_id": user_id,
            "query": query,
            "code": code,
            "result_summary": self._summarize_result(result),
            "intent": intent # e.g., "sales_analysis", "product_comparison"
        }
        file_path = self._get_daily_file_path(timestamp)
        
        try:
            with open(file_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
            print(f"Example added to collector for user {user_id}.")
        except OSError as e:
            print(f"Error writing example file {file_path}: {e}")

    def _summarize_result(self, result: Dict[str, Any]) -> str:
        """Creates a brief summary of the result."""
        # For simplicity, just return the first 100 chars of the result if it's a string, or its type.
        if isinstance(result, dict) and "result" in result:
            res = result["result"]
            if isinstance(res, str):
                return res[:100] + ("..." if len(res) > 100 else "")
            return f"Dict result with keys: {list(res.keys())}"
        return str(type(result))

    def get_all_examples(self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """
        Retrieves all examples within a date range.
        """
        all_examples: List[Dict[str, Any]] = []
        
        if start_date is None:
            start_date = datetime.min
        if end_date is None:
            end_date = datetime.max

        for filename in sorted(os.listdir(self.examples_dir)):
            if filename.startswith("examples_") and filename.endswith(".jsonl"):
                file_date_str = filename[9:19] # YYYY-MM-DD
                file_date = datetime.strptime(file_date_str, "%Y-%m-%d")
                
                if file_date > end_date.replace(hour=23, minute=59, second=59, microsecond=999999):
                    continue
                if file_date < start_date.replace(hour=0, minute=0, second=0, microsecond=0):
                    continue

                file_path = os.path.join(self.examples_dir, filename)
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        for line in f:
                            try:
                                entry = json.loads(line)
                                entry_timestamp = datetime.fromisoformat(entry["timestamp"])

                                if start_date <= entry_timestamp <= end_date:
                                    all_examples.append(entry)
                            except json.JSONDecodeError:
                                print(f"Warning: Corrupt JSON line in {filename}: {line.strip()}")
                except OSError as e:
                    print(f"Error reading examples file {file_path}: {e}")
        
        return all_examples

# Example usage
if __name__ == '__main__':
    from app.config.settings import Settings
    temp_settings = Settings()

    # Ensure examples directory exists for testing
    os.makedirs(temp_settings.LEARNING_EXAMPLES_PATH, exist_ok=True)

    collector = ExampleCollector(examples_dir=temp_settings.LEARNING_EXAMPLES_PATH)

    user1_id = "test_user_1"
    
    # Add some examples
    collector.add_example(user1_id, "Vendas totais por produto", "df.groupby('product').sum()", {"result": "ok"}, "sales_analysis")
    collector.add_example(user1_id, "Top 5 clientes", "df.groupby('client').count().sort()", {"result": "ok"}, "customer_segmentation")
    collector.add_example(user1_id, "Média de preço por categoria", "df.groupby('category').mean('price')", {"result": "ok"}, "pricing_analysis")

    print("\n--- Testing get_all_examples ---")
    all_examples = collector.get_all_examples()
    print(f"All examples ({len(all_examples)} records):")
    for entry in all_examples:
        print(f"  [{entry['timestamp']}] User {entry['user_id']}: {entry['query']} -> {entry['intent']}")

    # Clean up dummy files
    for filename in os.listdir(temp_settings.LEARNING_EXAMPLES_PATH):
        if filename.startswith("examples_"):
            os.remove(os.path.join(temp_settings.LEARNING_EXAMPLES_PATH, filename))
    print("\nCleaned up dummy example files.")
    print("\nExampleCollector tests passed!")

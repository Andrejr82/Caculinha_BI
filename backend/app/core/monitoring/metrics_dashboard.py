# backend/app/core/monitoring/metrics_dashboard.py

import json
import os
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from collections import defaultdict
from pathlib import Path

from app.config.settings import settings
from app.core.utils.query_history import QueryHistory # To get query data
from app.core.utils.response_cache import ResponseCache # To query cache stats

class MetricsDashboard:
    """
    Collects and provides various metrics for monitoring the BI agent's performance.
    (T4.4.2 from TASK_LIST)
    """
    def __init__(self, query_history: Optional[QueryHistory] = None, response_cache: Optional[ResponseCache] = None):
        self.query_history = query_history if query_history else QueryHistory(history_dir=settings.LEARNING_EXAMPLES_PATH) # Using LEARNING_EXAMPLES_PATH as history
        self.response_cache = response_cache if response_cache else ResponseCache(cache_dir=settings.LEARNING_FEEDBACK_PATH, ttl_minutes=settings.CACHE_TTL_MINUTES) # Using LEARNING_FEEDBACK_PATH as cache

    def get_metrics(self, days: int = 7) -> Dict[str, Any]:
        """
        Retrieves key performance indicators (KPIs) for the last N days.
        - Success Rate (from feedback)
        - Average Response Time (placeholder)
        - Cache Hit Rate
        - Total Queries
        - Total Errors
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        all_queries = self.query_history.get_history(start_date=start_date, end_date=end_date, limit=None)
        
        total_queries = len(all_queries)
        total_errors = sum(1 for q in all_queries if "error" in q.get("response_summary", "").lower()) # Simple error detection
        
        # Cache hit rate (placeholder - requires more sophisticated cache logging)
        # For now, we'll simulate. In a real system, the cache would log hits/misses.
        cache_hits = 0 # Placeholder for actual cache hits
        cache_misses = total_queries # Placeholder for actual cache misses
        cache_hit_rate = (cache_hits / total_queries) * 100 if total_queries > 0 else 0

        # Success rate (placeholder - needs dedicated feedback system)
        # Assuming feedback is stored by QueryHistory for now
        feedback_file_path = Path(settings.LEARNING_FEEDBACK_PATH) / "feedback.jsonl"
        positive_feedback = 0
        negative_feedback = 0
        try:
            if os.path.exists(feedback_file_path):
                with open(feedback_file_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        if not line.strip():
                            continue
                        try:
                            feedback_entry = json.loads(line)
                            timestamp_str = feedback_entry.get("timestamp", "")
                            if not timestamp_str:
                                continue

                            # Handle different timestamp formats
                            try:
                                entry_timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                            except (ValueError, AttributeError):
                                continue

                            if start_date <= entry_timestamp <= end_date:
                                if feedback_entry.get("feedback_type") == "positive":
                                    positive_feedback += 1
                                elif feedback_entry.get("feedback_type") == "negative":
                                    negative_feedback += 1
                        except (json.JSONDecodeError, KeyError) as parse_error:
                            continue
        except Exception as e:
            print(f"Error reading feedback file: {e}")

        total_feedback = positive_feedback + negative_feedback
        success_rate = (positive_feedback / total_feedback) * 100 if total_feedback > 0 else 0


        return {
            "total_queries": total_queries,
            "total_errors": total_errors,
            "success_rate_feedback": round(success_rate, 2),
            "cache_hit_rate": round(cache_hit_rate, 2), # Needs actual implementation
            "average_response_time_ms": "N/A" # Placeholder, needs instrumented timing
        }

    def get_error_trend(self, days: int = 30) -> List[Dict[str, Any]]:
        """
        Provides a daily trend of errors for the last N days.
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        error_counts_by_date = defaultdict(int)
        all_queries = self.query_history.get_history(start_date=start_date, end_date=end_date, limit=None)

        for query_entry in all_queries:
            if "error" in query_entry.get("response_summary", "").lower():
                query_date = datetime.fromisoformat(query_entry["timestamp"]).strftime("%Y-%m-%d")
                error_counts_by_date[query_date] += 1
        
        trend_data = []
        current_date = start_date
        while current_date <= end_date:
            date_str = current_date.strftime("%Y-%m-%d")
            trend_data.append({
                "date": date_str,
                "error_count": error_counts_by_date[date_str]
            })
            current_date += timedelta(days=1)
        
        return trend_data

    def get_top_queries(self, days: int = 7, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Identifies the most frequent queries in the last N days.
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        query_counts = defaultdict(int)
        all_queries = self.query_history.get_history(start_date=start_date, end_date=end_date, limit=None)

        for query_entry in all_queries:
            query_text = query_entry.get("query", "")
            if query_text:
                query_counts[query_text] += 1
        
        top_queries = sorted(query_counts.items(), key=lambda item: item[1], reverse=True)
        return [{"query": q, "count": count} for q, count in top_queries[:limit]]

if __name__ == '__main__':
    from app.config.settings import Settings
    temp_settings = Settings()
    os.makedirs(temp_settings.LEARNING_FEEDBACK_PATH, exist_ok=True) # Ensure dir exists for feedback.jsonl
    os.makedirs(temp_settings.LEARNING_EXAMPLES_PATH, exist_ok=True) # Ensure dir exists for query_history
    
    # Setup dummy query history and feedback
    history = QueryHistory(history_dir=temp_settings.LEARNING_EXAMPLES_PATH)
    history.add_query("user1", "Vendas por produto?", {"type": "text", "text": "OK"})
    history.add_query("user1", "Erro na consulta de estoque.", {"type": "error", "error": "simulated error"})
    history.add_query("user2", "Quais os top 5 produtos?", {"type": "text", "text": "OK"})
    history.add_query("user1", "Vendas por produto?", {"type": "text", "text": "OK"}) # Duplicate query
    
    # Simulate feedback
    feedback_file = Path(temp_settings.LEARNING_FEEDBACK_PATH) / "feedback.jsonl"
    with open(feedback_file, 'a', encoding='utf-8') as f:
        f.write(json.dumps({"timestamp": datetime.now().isoformat(), "user_id": "user1", "feedback_type": "positive"}) + "\n")
        f.write(json.dumps({"timestamp": (datetime.now() - timedelta(days=1)).isoformat(), "user_id": "user1", "feedback_type": "negative"}) + "\n")
    
    dashboard = MetricsDashboard(query_history=history)

    print("\n--- Testing get_metrics ---")
    metrics = dashboard.get_metrics(days=7)
    print(json.dumps(metrics, indent=2))
    assert metrics["total_queries"] >= 4
    assert metrics["total_errors"] >= 1
    assert metrics["success_rate_feedback"] > 0

    print("\n--- Testing get_error_trend ---")
    error_trend = dashboard.get_error_trend(days=7)
    print(json.dumps(error_trend, indent=2))
    assert any(item["error_count"] > 0 for item in error_trend)

    print("\n--- Testing get_top_queries ---")
    top_queries = dashboard.get_top_queries(days=7, limit=2)
    print(json.dumps(top_queries, indent=2))
    assert top_queries[0]["query"] == "Vendas por produto?"
    assert top_queries[0]["count"] == 2

    # Clean up dummy files
    for filename in os.listdir(temp_settings.LEARNING_EXAMPLES_PATH):
        if filename.startswith("queries_"):
            os.remove(os.path.join(temp_settings.LEARNING_EXAMPLES_PATH, filename))
    if os.path.exists(feedback_file):
        os.remove(feedback_file)
    print("\nCleaned up dummy metrics files.")
    print("\nMetricsDashboard tests passed!")

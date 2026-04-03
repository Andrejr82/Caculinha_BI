# backend/app/core/monitoring/metrics_dashboard.py

import json
import os
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from collections import defaultdict
from pathlib import Path

from backend.app.config.settings import settings
from backend.app.core.utils.query_history import QueryHistory
from backend.app.core.utils.response_cache import ResponseCache
from backend.services.metrics import MetricsService

logger = logging.getLogger(__name__)

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
        - Average Response Time
        - Cache Hit Rate
        - Total Queries
        - Total Errors
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        all_queries = self.query_history.get_history(start_date=start_date, end_date=end_date, limit=None)
        history_total_queries = len(all_queries)
        history_total_errors = sum(
            1 for q in all_queries if "error" in q.get("response_summary", "").lower()
        )

        metrics = MetricsService()
        total_queries = metrics.get_counter("chat_requests_total") or history_total_queries
        total_errors = metrics.get_counter("chat_errors_total") or history_total_errors

        cache_lookups = metrics.get_counter("chat_cache_lookups_total")
        cache_hits = metrics.get_counter("chat_cache_hits_total")
        cache_hit_rate = (cache_hits / cache_lookups) * 100 if cache_lookups > 0 else 0.0

        latency_stats = metrics.get_histogram_stats("chat_latency_seconds")
        average_latency_ms = 0.0
        if latency_stats.get("count", 0) > 0:
            average_latency_ms = float(latency_stats.get("avg", 0.0) or 0.0) * 1000.0

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
            logger.warning("Error reading feedback file: %s", e)

        total_feedback = positive_feedback + negative_feedback
        success_rate = (positive_feedback / total_feedback) * 100 if total_feedback > 0 else 0


        return {
            "total_queries": total_queries,
            "total_errors": total_errors,
            "success_rate_feedback": round(success_rate, 2),
            "cache_hit_rate": round(cache_hit_rate, 2),
            "average_response_time_ms": f"{average_latency_ms:.2f}",
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


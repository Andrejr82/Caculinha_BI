"""
Evaluations Repository - Stores response quality evaluations

Persists evaluations as JSON files for admin review.
"""

import json
import os
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional
from threading import Lock

logger = logging.getLogger(__name__)


class EvaluationsRepository:
    """
    File-based storage for response evaluations.
    
    Stores evaluations in data/evaluations/ as JSON files.
    """
    
    def __init__(self, base_path: str = None):
        if base_path is None:
            base_path = Path(__file__).parent.parent.parent.parent / "data" / "evaluations"
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
        self._lock = Lock()
        logger.info(f"EvaluationsRepository initialized at: {self.base_path}")
    
    def save(self, evaluation: Dict[str, Any]) -> str:
        """
        Save an evaluation record.
        
        Args:
            evaluation: Evaluation data with request_id, scores, etc.
            
        Returns:
            request_id of saved evaluation
        """
        request_id = evaluation.get("request_id", datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S_%f"))
        
        # Ensure required fields
        evaluation["request_id"] = request_id
        evaluation["created_at"] = evaluation.get("created_at", datetime.now(timezone.utc).isoformat())
        
        file_path = self.base_path / f"{request_id}.json"
        
        with self._lock:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(evaluation, f, ensure_ascii=False, indent=2, default=str)
        
        logger.info(f"Evaluation saved: {request_id}")
        return request_id
    
    def get(self, request_id: str) -> Optional[Dict[str, Any]]:
        """Get a single evaluation by request_id."""
        file_path = self.base_path / f"{request_id}.json"
        
        if not file_path.exists():
            return None
        
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    
    def get_all(
        self,
        limit: int = 100,
        offset: int = 0,
        min_score: Optional[float] = None,
        max_score: Optional[float] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get all evaluations with optional filtering.
        
        Args:
            limit: Maximum number of results
            offset: Skip this many results
            min_score: Minimum overall_score filter
            max_score: Maximum overall_score filter
            
        Returns:
            List of evaluation records
        """
        evaluations = []
        
        try:
            files = sorted(self.base_path.glob("*.json"), key=lambda f: f.stat().st_mtime, reverse=True)
            
            for file_path in files:
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        eval_data = json.load(f)
                    
                    # Apply score filters
                    score = eval_data.get("overall_score", 0)
                    if min_score is not None and score < min_score:
                        continue
                    if max_score is not None and score > max_score:
                        continue
                    
                    evaluations.append(eval_data)
                except Exception as e:
                    logger.warning(f"Error reading evaluation file {file_path}: {e}")
                    continue
        except Exception as e:
            logger.error(f"Error listing evaluations: {e}")
        
        # Apply pagination
        return evaluations[offset:offset + limit]
    
    def add_feedback(
        self,
        request_id: str,
        feedback_type: str,  # "thumbs_up", "thumbs_down"
        comment: Optional[str] = None
    ) -> bool:
        """
        Add user feedback to an existing evaluation.
        
        Args:
            request_id: Evaluation ID
            feedback_type: "thumbs_up" or "thumbs_down"
            comment: Optional feedback comment
            
        Returns:
            True if feedback was added successfully
        """
        evaluation = self.get(request_id)
        if not evaluation:
            return False
        
        # Add feedback
        if "feedback" not in evaluation:
            evaluation["feedback"] = []
        
        evaluation["feedback"].append({
            "type": feedback_type,
            "comment": comment,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        
        # Re-save
        self.save(evaluation)
        return True
    
    def count(self) -> int:
        """Get total number of evaluations."""
        return len(list(self.base_path.glob("*.json")))


# Global singleton instance
evaluations_repo = EvaluationsRepository()

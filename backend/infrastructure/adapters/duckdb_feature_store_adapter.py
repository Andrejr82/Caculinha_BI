"""
DuckDBFeatureStoreAdapter — Adapter de Feature Store DuckDB

Autor: Backend Specialist Agent
Data: 2026-02-07
"""

import json
from typing import List, Optional, Dict, Any
from pathlib import Path
from datetime import datetime

import duckdb
import structlog

from backend.domain.ports.feature_store_port import IFeatureStore
from backend.domain.entities.feature import Feature, FeatureValue

logger = structlog.get_logger(__name__)


class DuckDBFeatureStoreAdapter(IFeatureStore):
    """Adapter DuckDB para Feature Store ML."""
    
    def __init__(self, db_path: str = "data/features.duckdb"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialized = False
        self._conn = None
    
    def _get_connection(self) -> duckdb.DuckDBPyConnection:
        if self._conn is None:
            self._conn = duckdb.connect(str(self.db_path))
        return self._conn
    
    async def _ensure_initialized(self):
        if self._initialized:
            return
        conn = self._get_connection()
        conn.execute("""
            CREATE TABLE IF NOT EXISTS features (
                id VARCHAR PRIMARY KEY,
                tenant_id VARCHAR NOT NULL,
                entity_id VARCHAR NOT NULL,
                feature_name VARCHAR NOT NULL,
                value JSON NOT NULL,
                value_type VARCHAR,
                version INTEGER DEFAULT 1,
                ttl_seconds INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                metadata JSON,
                UNIQUE(tenant_id, entity_id, feature_name)
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_feat_key ON features(tenant_id, entity_id)")
        self._initialized = True
    
    async def store_feature(self, feature: Feature) -> str:
        await self._ensure_initialized()
        conn = self._get_connection()
        # Delete existing then insert
        conn.execute("DELETE FROM features WHERE id = ?", [feature.id])
        conn.execute("""
            INSERT INTO features 
            (id, tenant_id, entity_id, feature_name, value, value_type, version, ttl_seconds, created_at, updated_at, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, [
            feature.id, feature.tenant_id, feature.entity_id, feature.feature_name,
            json.dumps(feature.value), feature.value_type, feature.version, feature.ttl_seconds,
            feature.created_at, feature.updated_at,
            json.dumps(feature.metadata) if feature.metadata else None,
        ])
        return feature.id
    
    async def get_feature(
        self, tenant_id: str, entity_id: str, feature_name: str, version: Optional[int] = None
    ) -> Optional[Feature]:
        await self._ensure_initialized()
        conn = self._get_connection()
        result = conn.execute("""
            SELECT * FROM features WHERE tenant_id = ? AND entity_id = ? AND feature_name = ?
        """, [tenant_id, entity_id, feature_name]).fetchone()
        if not result:
            return None
        return Feature(
            id=result[0], tenant_id=result[1], entity_id=result[2], feature_name=result[3],
            value=json.loads(result[4]), version=result[6], ttl_seconds=result[7],
            created_at=result[8], updated_at=result[9],
            metadata=json.loads(result[10]) if result[10] else None,
        )
    
    async def get_features_for_entity(
        self, tenant_id: str, entity_id: str, feature_names: Optional[List[str]] = None
    ) -> Dict[str, Feature]:
        await self._ensure_initialized()
        conn = self._get_connection()
        if feature_names:
            placeholders = ",".join("?" * len(feature_names))
            query = f"SELECT * FROM features WHERE tenant_id = ? AND entity_id = ? AND feature_name IN ({placeholders})"
            results = conn.execute(query, [tenant_id, entity_id] + feature_names).fetchall()
        else:
            results = conn.execute(
                "SELECT * FROM features WHERE tenant_id = ? AND entity_id = ?",
                [tenant_id, entity_id]
            ).fetchall()
        return {
            r[3]: Feature(id=r[0], tenant_id=r[1], entity_id=r[2], feature_name=r[3],
                         value=json.loads(r[4]), version=r[6], ttl_seconds=r[7])
            for r in results
        }
    
    async def update_feature(self, tenant_id: str, entity_id: str, feature_name: str, value: FeatureValue) -> bool:
        await self._ensure_initialized()
        conn = self._get_connection()
        result = conn.execute("""
            UPDATE features SET value = ?, version = version + 1, updated_at = CURRENT_TIMESTAMP
            WHERE tenant_id = ? AND entity_id = ? AND feature_name = ?
        """, [json.dumps(value), tenant_id, entity_id, feature_name])
        return result.rowcount > 0
    
    async def delete_feature(self, tenant_id: str, entity_id: str, feature_name: str) -> bool:
        await self._ensure_initialized()
        conn = self._get_connection()
        result = conn.execute(
            "DELETE FROM features WHERE tenant_id = ? AND entity_id = ? AND feature_name = ?",
            [tenant_id, entity_id, feature_name]
        )
        return result.rowcount > 0
    
    async def batch_store(self, features: List[Feature]) -> List[str]:
        return [await self.store_feature(f) for f in features]
    
    async def batch_get(
        self, tenant_id: str, entity_ids: List[str], feature_names: List[str]
    ) -> Dict[str, Dict[str, Feature]]:
        result = {}
        for entity_id in entity_ids:
            result[entity_id] = await self.get_features_for_entity(tenant_id, entity_id, feature_names)
        return result
    
    async def list_feature_names(self, tenant_id: str) -> List[str]:
        await self._ensure_initialized()
        conn = self._get_connection()
        results = conn.execute(
            "SELECT DISTINCT feature_name FROM features WHERE tenant_id = ?", [tenant_id]
        ).fetchall()
        return [r[0] for r in results]
    
    async def get_feature_stats(self, tenant_id: str, feature_name: str) -> Dict[str, Any]:
        await self._ensure_initialized()
        conn = self._get_connection()
        result = conn.execute("""
            SELECT COUNT(*), MIN(created_at), MAX(updated_at) FROM features 
            WHERE tenant_id = ? AND feature_name = ?
        """, [tenant_id, feature_name]).fetchone()
        return {"count": result[0], "first_created": result[1], "last_updated": result[2]}
    
    async def cleanup_expired(self, tenant_id: Optional[str] = None) -> int:
        await self._ensure_initialized()
        conn = self._get_connection()
        if tenant_id:
            result = conn.execute("""
                DELETE FROM features WHERE tenant_id = ? AND ttl_seconds > 0 
                AND EPOCH(CURRENT_TIMESTAMP - created_at) > ttl_seconds
            """, [tenant_id])
        else:
            result = conn.execute("""
                DELETE FROM features WHERE ttl_seconds > 0 
                AND EPOCH(CURRENT_TIMESTAMP - created_at) > ttl_seconds
            """)
        return result.rowcount

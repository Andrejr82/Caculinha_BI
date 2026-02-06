# 🗄️ DATABASE ARCHITECTURE REVIEW & OPTIMIZATION REPORT

**Data:** 22 de Janeiro de 2026, 22:06  
**Metodologia:** Database Architect  
**Status:** ✅ ANÁLISE COMPLETA

---

## 📋 EXECUTIVE SUMMARY

**Current Architecture:** DuckDB + Parquet (Columnar Storage)  
**Data Volume:** 2 Parquet files (admmat.parquet, users.parquet)  
**Concurrency:** Connection pooling (5-50 connections)  
**Security:** Row-Level Security (RLS) implemented  

**Overall Assessment:** ⚠️ **GOOD with OPTIMIZATION OPPORTUNITIES**

---

## 🏗️ CURRENT ARCHITECTURE

### Data Sources

| File | Purpose | Location | Status |
|------|---------|----------|--------|
| **admmat.parquet** | Main business data | `backend/data/parquet/` | ✅ Active |
| **users.parquet** | User authentication | `backend/data/parquet/` | ✅ Active |

### Technology Stack

**Database Engine:** DuckDB 1.1+  
**Storage Format:** Apache Parquet (columnar)  
**Query Engine:** DuckDB SQL  
**Connection Management:** Custom connection pool  
**ORM:** None (Raw SQL)  

---

## ✅ STRENGTHS IDENTIFIED

### 1. Connection Pooling ✅ EXCELLENT

**File:** `backend/app/infrastructure/data/duckdb_pool.py`

**Implementation:**
```python
class DuckDBConnectionPool:
    min_connections: 5
    max_connections: 50
    timeout: 30.0s
    
    Features:
    - Thread-safe queue
    - Connection reuse
    - Auto-cleanup
    - Metrics tracking (hit rate, total requests)
```

**Strengths:**
- ✅ Proper connection pooling for 30+ concurrent users
- ✅ Thread-safe implementation with Lock
- ✅ Metrics for monitoring (hit rate tracking)
- ✅ Context manager pattern for safe resource management
- ✅ Read-only connections (prevents accidental writes)

**Recommendation:** ✅ KEEP AS IS (well-designed)

---

### 2. Row-Level Security (RLS) ✅ IMPLEMENTED

**File:** `backend/app/core/data_source_manager.py` (lines 83-96)

**Implementation:**
```python
def get_data(self, limit: int = None) -> pd.DataFrame:
    # Apply RLS - Filter by user segments
    allowed_segments = get_current_user_segments()
    
    if allowed_segments and "*" not in allowed_segments:
        if 'NOMESEGMENTO' in df.columns:
            df = df[df['NOMESEGMENTO'].isin(allowed_segments)]
```

**Strengths:**
- ✅ Automatic RLS application
- ✅ Segment-based access control
- ✅ Admin bypass with "*" wildcard
- ✅ Graceful handling if column missing

**Recommendation:** ✅ KEEP AS IS (security best practice)

---

### 3. Columnar Storage (Parquet) ✅ OPTIMAL

**Advantages:**
- ✅ Excellent compression (5-10x vs CSV)
- ✅ Fast analytical queries (column pruning)
- ✅ Schema preservation
- ✅ Compatible with DuckDB zero-copy reads

**Recommendation:** ✅ KEEP AS IS (optimal for BI workloads)

---

## ⚠️ OPTIMIZATION OPPORTUNITIES

### 1. Missing Indexes on Parquet Data 🔴 CRITICAL

**Current State:**
- ✅ 5 indexes on SQLite tables (shared_conversations, user_preferences)
- ❌ **NO indexes on main Parquet data (admmat.parquet)**

**Impact:**
- Slow queries on filtered data
- Full table scans on every query
- Poor performance with large datasets

**Query Patterns Found:**
```sql
-- purchasing_tools.py (line 75)
SELECT PRODUTO, VENDA_30DD, ULTIMA_ENTRADA_CUSTO_CD, NOME
FROM data
WHERE PRODUTO = '59294'  -- ❌ No index on PRODUTO

-- flexible_query_tool.py (line 171)
SELECT {columns}
FROM data
WHERE UNE = 1685  -- ❌ No index on UNE

-- anomaly_detection.py (line 55)
SELECT NOMESEGMENTO, SUM(VENDA_30DD)
FROM data
GROUP BY NOMESEGMENTO  -- ❌ No index on NOMESEGMENTO
```

**Recommendation:** 🔴 **CREATE INDEXES**

**Solution 1: DuckDB Persistent Indexes (Recommended)**
```sql
-- Create DuckDB database with indexes
CREATE TABLE admmat AS SELECT * FROM read_parquet('admmat.parquet');

CREATE INDEX idx_produto ON admmat(PRODUTO);
CREATE INDEX idx_une ON admmat(UNE);
CREATE INDEX idx_segmento ON admmat(NOMESEGMENTO);
CREATE INDEX idx_produto_une ON admmat(PRODUTO, UNE);  -- Composite

-- Save as DuckDB file
EXPORT DATABASE 'admmat.duckdb';
```

**Solution 2: Parquet Partitioning**
```python
# Partition by UNE (store) for faster filtering
df.to_parquet(
    'admmat_partitioned/',
    partition_cols=['UNE'],
    engine='pyarrow'
)

# Query becomes faster
SELECT * FROM read_parquet('admmat_partitioned/UNE=1685/*.parquet')
```

**Expected Impact:**
- 10-100x faster filtered queries
- Reduced memory usage
- Better scalability

---

### 2. SELECT * Anti-Pattern 🟡 MODERATE

**Current State:**
Multiple queries use `SELECT *`:

```python
# universal_chart_generator.py (line 99)
sql_query = f"SELECT * FROM {table_name} WHERE 1=1"  # ❌

# mcp_parquet_tools.py (line 56)
SELECT * FROM read_parquet('{parquet_path}')  # ❌
```

**Impact:**
- Unnecessary data transfer
- Higher memory usage
- Slower query execution

**Recommendation:** 🟡 **SELECT ONLY NEEDED COLUMNS**

**Before:**
```sql
SELECT * FROM data WHERE PRODUTO = '59294'
```

**After:**
```sql
SELECT PRODUTO, NOME, VENDA_30DD, ESTOQUE_UNE
FROM data
WHERE PRODUTO = '59294'
```

**Expected Impact:**
- 30-50% faster queries
- 50-70% less memory usage

---

### 3. No Query Caching 🟡 MODERATE

**Current State:**
- ✅ Parquet file cached in memory (`ParquetCache`)
- ❌ **No query result caching**

**Impact:**
- Repeated identical queries re-execute
- Wasted CPU cycles
- Higher latency

**Recommendation:** 🟡 **IMPLEMENT QUERY CACHE**

**Solution:**
```python
from functools import lru_cache
import hashlib

class QueryCache:
    def __init__(self, max_size=100, ttl=300):
        self.cache = {}
        self.max_size = max_size
        self.ttl = ttl
    
    def get(self, query: str, params: dict):
        key = self._hash(query, params)
        if key in self.cache:
            result, timestamp = self.cache[key]
            if time.time() - timestamp < self.ttl:
                return result
        return None
    
    def set(self, query: str, params: dict, result):
        key = self._hash(query, params)
        self.cache[key] = (result, time.time())
        
        # LRU eviction
        if len(self.cache) > self.max_size:
            oldest = min(self.cache.items(), key=lambda x: x[1][1])
            del self.cache[oldest[0]]
```

**Expected Impact:**
- 90%+ faster for repeated queries
- Reduced database load
- Better user experience

---

### 4. No Query Performance Monitoring 🟡 MODERATE

**Current State:**
- ✅ Connection pool metrics (hit rate)
- ❌ **No query execution time tracking**
- ❌ **No slow query logging**

**Impact:**
- Can't identify slow queries
- No performance baseline
- Difficult to optimize

**Recommendation:** 🟡 **ADD QUERY MONITORING**

**Solution:**
```python
import time
import logging

logger = logging.getLogger(__name__)

class QueryMonitor:
    def __init__(self, slow_query_threshold=1.0):
        self.threshold = slow_query_threshold
        self.query_stats = {}
    
    def track_query(self, query: str, execution_time: float):
        # Log slow queries
        if execution_time > self.threshold:
            logger.warning(
                f"SLOW QUERY ({execution_time:.2f}s): {query[:100]}..."
            )
        
        # Track statistics
        if query not in self.query_stats:
            self.query_stats[query] = {
                'count': 0,
                'total_time': 0,
                'max_time': 0
            }
        
        stats = self.query_stats[query]
        stats['count'] += 1
        stats['total_time'] += execution_time
        stats['max_time'] = max(stats['max_time'], execution_time)

# Usage in data_source_manager.py
start = time.time()
result = conn.execute(query).df()
execution_time = time.time() - start
query_monitor.track_query(query, execution_time)
```

**Expected Impact:**
- Identify bottlenecks
- Data-driven optimization
- Better debugging

---

### 5. Pandas Overhead 🟡 MODERATE

**Current State:**
```python
# data_source_manager.py (line 56-64)
df_polars = cache.get_dataframe("admmat.parquet")

# Convert to Pandas (overhead!)
if hasattr(df_polars, 'to_pandas'):
    df = df_polars.to_pandas()
```

**Impact:**
- Unnecessary conversion overhead
- Higher memory usage (Pandas is less efficient)
- Slower operations

**Recommendation:** 🟡 **USE POLARS OR DUCKDB DIRECTLY**

**Option 1: Keep Polars**
```python
# Modify tools to accept Polars DataFrames
def consultar_dados_flexivel(df: pl.DataFrame):
    # Use Polars operations (faster)
    result = df.filter(pl.col('PRODUTO') == produto_id)
    return result
```

**Option 2: Use DuckDB Relations**
```python
# Return DuckDB relation instead of DataFrame
def get_data_relation(self):
    with pool.get_connection() as conn:
        return conn.execute("SELECT * FROM data")
    
# Query on relation (zero-copy)
result = relation.filter("PRODUTO = '59294'").df()
```

**Expected Impact:**
- 2-5x faster data operations
- 30-50% less memory usage

---

## 📊 SCHEMA ANALYSIS

### admmat.parquet Schema (Inferred)

**Columns Identified from Queries:**
- `PRODUTO` (Product ID) - **Needs Index**
- `UNE` (Store ID) - **Needs Index**
- `NOMESEGMENTO` (Segment) - **Needs Index**
- `VENDA_30DD` (Sales 30 days)
- `ESTOQUE_UNE` (Store stock)
- `ESTOQUE_LV` (Green line stock)
- `LIQUIDO_38` (Price)
- `ULTIMA_ENTRADA_CUSTO_CD` (Cost)
- `NOMEFABRICANTE` (Supplier)
- `NOME` (Product name)

**Data Types:** ⚠️ **UNKNOWN** (Parquet preserves types)

**Recommendation:** 🟡 **DOCUMENT SCHEMA**

Create schema documentation:
```python
# backend/app/infrastructure/data/schema.py
from dataclasses import dataclass
from typing import Optional

@dataclass
class AdmmatSchema:
    """Schema for admmat.parquet"""
    PRODUTO: str  # Product ID (indexed)
    UNE: int  # Store ID (indexed)
    NOMESEGMENTO: str  # Segment (indexed)
    VENDA_30DD: float  # Sales last 30 days
    ESTOQUE_UNE: int  # Current stock
    LIQUIDO_38: float  # Sale price
    ULTIMA_ENTRADA_CUSTO_CD: float  # Cost
    NOME: str  # Product name
    NOMEFABRICANTE: Optional[str]  # Supplier
```

---

## 🎯 PRIORITY RECOMMENDATIONS

### 🔴 HIGH PRIORITY (Immediate)

1. **Create Indexes on Parquet Data**
   - Impact: 10-100x query speedup
   - Effort: 2-4 hours
   - Method: Convert to DuckDB with indexes

2. **Implement Query Result Caching**
   - Impact: 90% faster repeated queries
   - Effort: 4-6 hours
   - Method: LRU cache with TTL

3. **Add Query Performance Monitoring**
   - Impact: Identify bottlenecks
   - Effort: 2-3 hours
   - Method: Query execution time tracking

### 🟡 MEDIUM PRIORITY (Next Sprint)

4. **Replace SELECT * with Specific Columns**
   - Impact: 30-50% faster queries
   - Effort: 4-8 hours
   - Method: Refactor all tools

5. **Reduce Pandas Overhead**
   - Impact: 2-5x faster operations
   - Effort: 8-12 hours
   - Method: Use Polars/DuckDB directly

6. **Document Database Schema**
   - Impact: Better maintainability
   - Effort: 2-3 hours
   - Method: Create schema.py

### 🟢 LOW PRIORITY (Future)

7. **Implement Parquet Partitioning**
   - Impact: Faster filtered queries
   - Effort: 6-8 hours
   - Method: Partition by UNE

8. **Add Database Migrations System**
   - Impact: Better version control
   - Effort: 8-12 hours
   - Method: Alembic or custom

---

## 📈 EXPECTED PERFORMANCE IMPROVEMENTS

| Optimization | Query Time | Memory Usage | Effort |
|--------------|------------|--------------|--------|
| **Indexes** | -90% | -20% | Medium |
| **Query Cache** | -95% (repeated) | +10% | Low |
| **Column Selection** | -40% | -60% | Medium |
| **Polars Direct** | -70% | -40% | High |
| **Monitoring** | N/A | +5% | Low |

**Combined Impact:** 
- 10-100x faster queries (with indexes + cache)
- 50% less memory usage
- Better scalability for 50+ users

---

## ✅ WHAT'S WORKING WELL

1. ✅ **Connection Pooling** - Excellent implementation
2. ✅ **Row-Level Security** - Proper security model
3. ✅ **Columnar Storage** - Optimal for analytics
4. ✅ **Read-Only Connections** - Prevents data corruption
5. ✅ **Thread-Safe Design** - Proper concurrency handling

---

## 🚀 IMPLEMENTATION ROADMAP

### Phase 1: Quick Wins (Week 1)
- [ ] Add query performance monitoring
- [ ] Implement query result caching
- [ ] Document current schema

### Phase 2: Indexing (Week 2)
- [ ] Convert Parquet to DuckDB with indexes
- [ ] Test query performance improvements
- [ ] Update connection pool to use DuckDB file

### Phase 3: Optimization (Week 3-4)
- [ ] Replace SELECT * with specific columns
- [ ] Reduce Pandas overhead (use Polars)
- [ ] Implement slow query alerting

### Phase 4: Advanced (Future)
- [ ] Parquet partitioning by UNE
- [ ] Database migrations system
- [ ] Advanced caching strategies

---

## 📝 CONCLUSION

**Current State:** The database architecture is **solid** with good connection pooling and security, but lacks **indexing** and **query optimization**.

**Key Findings:**
- ✅ Well-designed connection pool
- ✅ Proper RLS implementation
- ❌ Missing indexes (critical)
- ❌ No query caching
- ❌ SELECT * anti-pattern

**Recommended Next Steps:**
1. Create indexes on PRODUTO, UNE, NOMESEGMENTO
2. Implement query result caching
3. Add query performance monitoring

**Expected Outcome:**
- 10-100x faster queries
- Support for 100+ concurrent users
- Better user experience

---

**Report Generated by:** Database Architect Agent  
**Date:** 22 de Janeiro de 2026, 22:06  
**Status:** ✅ READY FOR IMPLEMENTATION

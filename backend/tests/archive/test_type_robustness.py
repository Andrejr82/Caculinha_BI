"""
Test script for data type robustness fixes.
Validates that aggregations work with NULL and mixed types.

Run: python test_type_robustness.py
"""

import sys
sys.path.insert(0, '.')

from app.infrastructure.data.duckdb_adapter import duckdb_adapter
import pandas as pd
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_aggregation_with_null():
    """Test SUM aggregation on column that may have NULL values."""
    print("\n" + "="*60)
    print("TEST 1: Aggregation with NULL values")
    print("="*60)

    try:
        result = duckdb_adapter.execute_aggregation(
            agg_col='ESTOQUE_UNE',
            agg_func='sum',
            group_by=['UNE'],
            filters={'PRODUTO': 369947},
            limit=50
        )

        print(f"✅ SUCCESS: Aggregation returned {len(result)} rows")
        print(f"Sample data:\n{result.head(10)}")
        return True

    except Exception as e:
        print(f"❌ FAILED: {e}")
        return False


def test_load_data_with_problematic_columns():
    """Test loading data with type casting for numeric columns."""
    print("\n" + "="*60)
    print("TEST 2: Load data with type casting")
    print("="*60)

    try:
        result = duckdb_adapter.load_data(
            columns=['PRODUTO', 'UNE', 'NOME', 'ESTOQUE_UNE', 'VENDA_30DD'],
            filters={'PRODUTO': 369947},
            limit=20
        )

        print(f"✅ SUCCESS: Loaded {len(result)} rows")
        print(f"Column types:\n{result.dtypes}")
        print(f"\nSample data:\n{result.head(5)}")

        # Verify numeric columns are float
        assert result['ESTOQUE_UNE'].dtype in [float, 'float64'], "ESTOQUE_UNE should be float"
        assert result['VENDA_30DD'].dtype in [float, 'float64'], "VENDA_30DD should be float"

        print("✅ Type validation passed")
        return True

    except Exception as e:
        print(f"❌ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_aggregation_with_group_by():
    """Test aggregation grouped by UNE."""
    print("\n" + "="*60)
    print("TEST 3: Aggregation with GROUP BY")
    print("="*60)

    try:
        result = duckdb_adapter.execute_aggregation(
            agg_col='VENDA_30DD',
            agg_func='sum',
            group_by=['UNE'],
            filters={'PRODUTO': 369947},
            limit=50
        )

        print(f"✅ SUCCESS: Found product in {len(result)} UNEs")

        if not result.empty:
            total_sales = result['valor'].sum()
            print(f"Total sales across all UNEs: {total_sales:.2f}")
            print(f"\nTop 5 UNEs by sales:\n{result.head(5)}")
        else:
            print("⚠️  WARNING: No data found for product 369947")

        return True

    except Exception as e:
        print(f"❌ FAILED: {e}")
        return False


def test_count_aggregation():
    """Test COUNT aggregation (doesn't need numeric casting)."""
    print("\n" + "="*60)
    print("TEST 4: Count aggregation")
    print("="*60)

    try:
        result = duckdb_adapter.execute_aggregation(
            agg_col='PRODUTO',
            agg_func='count',
            group_by=['UNE'],
            filters={'PRODUTO': 369947},
            limit=50
        )

        print(f"✅ SUCCESS: Product found in {len(result)} UNEs")
        print(f"Sample:\n{result.head(10)}")
        return True

    except Exception as e:
        print(f"❌ FAILED: {e}")
        return False


def test_avg_aggregation():
    """Test AVG aggregation with type casting."""
    print("\n" + "="*60)
    print("TEST 5: Average aggregation")
    print("="*60)

    try:
        result = duckdb_adapter.execute_aggregation(
            agg_col='ESTOQUE_UNE',
            agg_func='avg',
            group_by=None,  # Scalar aggregation
            filters={'PRODUTO': 369947},
            limit=1
        )

        print(f"✅ SUCCESS: Calculated average")
        print(f"Result:\n{result}")
        return True

    except Exception as e:
        print(f"❌ FAILED: {e}")
        return False


def run_all_tests():
    """Run all test cases."""
    print("\n" + "="*80)
    print("🚀 STARTING DATA TYPE ROBUSTNESS TESTS")
    print("="*80)

    tests = [
        ("Aggregation with NULL", test_aggregation_with_null),
        ("Load data with casting", test_load_data_with_problematic_columns),
        ("GROUP BY aggregation", test_aggregation_with_group_by),
        ("COUNT aggregation", test_count_aggregation),
        ("AVG aggregation", test_avg_aggregation),
    ]

    results = []
    for name, test_func in tests:
        try:
            success = test_func()
            results.append((name, success))
        except Exception as e:
            print(f"\n❌ EXCEPTION in {name}: {e}")
            results.append((name, False))

    # Summary
    print("\n" + "="*80)
    print("📊 TEST SUMMARY")
    print("="*80)

    passed = sum(1 for _, success in results if success)
    total = len(results)

    for name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} - {name}")

    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 ALL TESTS PASSED! Type robustness fixes are working correctly.")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Please review the errors above.")
        return 1


if __name__ == "__main__":
    exit_code = run_all_tests()
    sys.exit(exit_code)

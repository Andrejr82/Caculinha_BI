import sys
import os

print("🚀 Starting Import Test...", file=sys.stderr)

imports_to_test = [
    "app.core.tools.une_tools",
    "app.core.tools.flexible_query_tool",
    "app.core.tools.metadata_tools",
    "app.core.data_source_manager",
    "app.core.tools.universal_chart_generator",
    "app.core.tools.chart_tools",
    "app.core.utils.field_mapper",
    "app.core.utils.serializers",
    "app.core.utils.tool_scoping",
    # Commented out ones should be skipped? No, test them to see if they crash.
    "app.core.tools.anomaly_detection",
    "app.core.tools.purchasing_tools",
    "app.core.tools.semantic_search_tool",
    "app.core.rag.hybrid_retriever"
]

for mod in imports_to_test:
    try:
        print(f"📦 Importing {mod}...", file=sys.stderr)
        __import__(mod, fromlist=[''])
        print(f"✅ {mod} OK", file=sys.stderr)
    except Exception as e:
        print(f"❌ {mod} FAILED: {e}", file=sys.stderr)
    except OSError as e: # Catch DLL errors
        print(f"❌ {mod} CRASHED (OS): {e}", file=sys.stderr)

print("🏁 Import Test Complete.", file=sys.stderr)

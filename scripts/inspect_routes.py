
import sys
import json
import os

# Add project root to python path
sys.path.append(os.getcwd())

from backend.main import app
from fastapi.routing import APIRoute

routes = []
for route in app.routes:
    if isinstance(route, APIRoute):
        routes.append({
            "path": route.path,
            "methods": list(route.methods),
            "name": route.name,
            "tags": route.tags
        })


with open('backend_routes_runtime.json', 'w') as f:
    json.dump(routes, f, indent=2)
print("Routes written to backend_routes_runtime.json")


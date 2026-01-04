from app.api import router
for route in router.routes:
    print(f"Path: {route.path}, Methods: {route.methods}")

# run the fastapi backend, and serve the built sveltekit app as static files
import uvicorn
from fastapi.staticfiles import StaticFiles

# importing backend.api will run any code inside backend.api (i think)
import backend.api

if __name__ == "__main__":
    try:
        backend.api.init()
        app = backend.api.app
        app.mount("/", StaticFiles(directory="build", html=True), name="frontend")
        uvicorn.run(app, host="127.0.0.1", port=8000)
    finally:
        backend.api.deinit()
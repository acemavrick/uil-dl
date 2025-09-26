# run the fastapi backend, and serve the built sveltekit app as static files
import uvicorn
from backend.api import app
from fastapi.staticfiles import StaticFiles

if __name__ == "__main__":
    app.mount("/", StaticFiles(directory="build", html=True), name="frontend")
    uvicorn.run(app, host="127.0.0.1", port=8000)
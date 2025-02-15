from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
import uvicorn

app = FastAPI()

app.mount("/", StaticFiles(directory="app/presentation/ui/web_app/public", html=True), name="webapp")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

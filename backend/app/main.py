from fastapi import FastAPI

from app.api.routes import auth
from app.api.routes import cases
from app.api.routes import messages
from app.api.routes import triage
from app.api.routes import users


app = FastAPI(
    title="Support Case Management API",
    version="1.0.0",
)


app.include_router(auth.router)
app.include_router(cases.router)
app.include_router(messages.router)
app.include_router(users.router)
app.include_router(triage.router)


@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "message": "Support Case Management API is running.",
    }
from fastapi import FastAPI


app = FastAPI(title="Support Case Management API")


@app.get("/")
def root() -> dict[str, str]:
    return {"status": "ok"}

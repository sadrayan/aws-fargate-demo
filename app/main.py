from fastapi import FastAPI

app = FastAPI(title="aws-fargate-demo")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/hello")
def hello() -> dict[str, str]:
    return {"message": "Hello from Fargate demo"}

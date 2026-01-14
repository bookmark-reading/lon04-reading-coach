"""Run the Reading Coach FastAPI application with uvicorn."""

import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "src.application.api:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )


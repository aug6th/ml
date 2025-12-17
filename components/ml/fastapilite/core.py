import os
from typing import Any, Dict, List, Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse

cors_settings = {
    "allow_origins": [
        "http://localhost:3000",
        "http://localhost:8000",
        "http://localhost:5173",
    ],
    "allow_credentials": True,
    "allow_methods": ["*"],
    "allow_headers": ["*"],
    "expose_headers": ["*"],
}


def create_app(
    title: str,
    description: str = None,
    version: str = None,
    docs_route: str = "/docs",
    openapi_tags: Optional[List[Dict[str, Any]]] = None,
    cors_override: Optional[Dict] = None,
    redirect_slashes: bool = True,
) -> FastAPI:
    """
    Create a FastAPI application instance

    Parameters:
    - title: The title of the app
    - description: A short description of the app
    - version: The version of the app
    - docs_route: The route for the documentation
    - openapi_tags: List of tags for OpenAPI schema
    - cors_override: Optional dictionary with CORS configuration to override default cors_settings

    Returns:
    A FastAPI app instance
    """
    virtual_path = os.environ.get("VIRTUAL_PATH", None)
    app = FastAPI(
        title=title,
        version=version or os.getenv("APP_VERSION", "1.0"),
        description=description or f"API for {title}",
        openapi_tags=openapi_tags,
        docs_url=docs_route,
        root_path=virtual_path,
        redirect_slashes=redirect_slashes,
    )

    cors_config = cors_override if cors_override is not None else cors_settings
    app.add_middleware(CORSMiddleware, **cors_config)

    def redirect_root():
        virtual_path = os.environ.get("VIRTUAL_PATH", "")
        full_docs_route = f"{virtual_path.rstrip('/')}/{docs_route.lstrip('/')}"
        return RedirectResponse(full_docs_route)

    def healthz():
        """Check if the app is healthy"""
        return JSONResponse(content={"status": "healthy"}, status_code=200)

    def readyz():
        """Check if the app is ready to serve traffic"""
        return JSONResponse(content={"status": "ready"}, status_code=200)

    app.get("/")(redirect_root)
    app.get("/healthz")(healthz)
    app.get("/readyz")(readyz)
    return app

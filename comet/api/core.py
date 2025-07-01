import random
import string
import secrets
import orjson

from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import RedirectResponse, Response
from fastapi.templating import Jinja2Templates
from fastapi.security import HTTPBasic, HTTPBasicCredentials

from comet.utils.models import settings, web_config, database
from comet.utils.general import config_check
from comet.debrid.manager import get_debrid_extension

templates = Jinja2Templates("comet/templates")
main = APIRouter()
security = HTTPBasic()


@main.get("/")
async def root():
    return RedirectResponse("/configure")


@main.get("/health")
async def health():
    return {"status": "ok"}


@main.get("/configure")
@main.get("/{b64config}/configure")
async def configure(request: Request):
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "CUSTOM_HEADER_HTML": settings.CUSTOM_HEADER_HTML
            if settings.CUSTOM_HEADER_HTML
            else "",
            "webConfig": web_config,
            "proxyDebridStream": settings.PROXY_DEBRID_STREAM,
        },
    )


@main.get("/manifest.json")
@main.get("/{b64config}/manifest.json")
async def manifest(request: Request, b64config: str = None):
    base_manifest = {
        "id": f"{settings.ADDON_ID}.{''.join(random.choice(string.ascii_letters) for _ in range(4))}",
        "description": "Decentralized shared streaming",
        "version": "1.0.0",
        "catalogs": [],
        "resources": [
            {
                "name": "stream",
                "types": ["movie", "series"],
                "idPrefixes": ["tt", "kitsu"],
            }
        ],
        "types": ["movie", "series", "anime", "other"],
        "logo": "https://i.postimg.cc/JnF0MVmb/temp-Image-Jd-JH5-B.avif",
        "background": "https://i.postimg.cc/4yLptFzP/popcorn.jpg",
        "behaviorHints": {"configurable": True, "configurationRequired": False},
    }

    config = config_check(b64config)
    if not config:
        base_manifest["name"] = "❌ | Comet"
        base_manifest["description"] = (
            f"⚠️ OBSOLETE CONFIGURATION, PLEASE RE-CONFIGURE ON {request.url.scheme}://{request.url.netloc} ⚠️"
        )
        return base_manifest

    debrid_extension = get_debrid_extension(config["debridService"])
    base_manifest["name"] = (
        f"{settings.ADDON_NAME}{(' | ' + debrid_extension) if debrid_extension is not None else ''}"
    )

    return base_manifest


class CustomORJSONResponse(Response):
    media_type = "application/json"

    def render(self, content):
        assert orjson is not None, "orjson must be installed"
        return orjson.dumps(content, option=orjson.OPT_INDENT_2)


def verify_dashboard_auth(credentials: HTTPBasicCredentials = Depends(security)):
    is_correct = secrets.compare_digest(
        credentials.password, settings.DASHBOARD_ADMIN_PASSWORD
    )

    if not is_correct:
        raise HTTPException(
            status_code=401,
            detail="Incorrect password",
            headers={"WWW-Authenticate": "Basic"},
        )

    return True


@main.get("/dashboard", response_class=CustomORJSONResponse)
async def dashboard(authenticated: bool = Depends(verify_dashboard_auth)):
    rows = await database.fetch_all("SELECT * FROM active_connections")
    return rows

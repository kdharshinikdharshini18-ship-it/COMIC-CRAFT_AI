from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates

from app.config import settings
from app.models import ComicRequest

from app.ai.gemini_flash import (
    generate_panel_outline,
)

from app.services.gemini_pro import (
    generate_story_content,
)

from app.services.image_generator import (
    generate_panel_image,
)

from app.services.layout_builder import (
    build_comic_layout,
)

from app.services.exporters import (
    create_comic_pdf,
)


router = APIRouter()


templates = Jinja2Templates(
    directory=str(
        settings.static_dir.parent / "templates"
    )
)


def _generate_comic(data: ComicRequest):

    # Step 1:
    # Generate the comic outline.
    outline = generate_panel_outline(data)

    # Step 2:
    # Generate narration and dialogue.
    story = generate_story_content(
        data,
        outline.panels,
    )

    # Step 3:
    # Generate images for every panel.
    image_urls = []

    for panel in outline.panels:
        image_url = generate_panel_image(
            panel.image_prompt,
            panel.panel_number,
            data.character_name,
            data.art_style,
        )

        image_urls.append(image_url)

    # Step 4:
    # Build final comic layout.
    layout = build_comic_layout(
        data,
        outline.panels,
        story,
        image_urls,
    )

    # Step 5:
    # Export PDF.
    pdf_url = create_comic_pdf(
        outline.title,
        layout,
    )

    return (
        outline.title,
        layout,
        pdf_url,
    )


@router.get(
    "/",
    response_class=HTMLResponse,
)
async def home(request: Request):

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "settings": settings,
            "error": None,
        },
    )


@router.post(
    "/generate",
    response_class=HTMLResponse,
)
async def generate(
    request: Request,
    story_prompt: str = Form(...),
    character_name: str = Form(...),
    setting: str = Form(...),
    tone: str = Form("adventurous"),
    art_style: str = Form("comic book"),
    panel_count: int = Form(5),
):

    try:

        data = ComicRequest(
            story_prompt=story_prompt,
            character_name=character_name,
            setting=setting,
            tone=tone,
            art_style=art_style,
            panel_count=panel_count,
        )

        title, layout, pdf_url = _generate_comic(
            data
        )

        return templates.TemplateResponse(
            request=request,
            name="comic_preview.html",
            context={
                "title": title,
                "layout": layout,
                "pdf_url": pdf_url,
            },
        )

    except Exception as exc:

        return templates.TemplateResponse(
            request=request,
            name="index.html",
            context={
                "settings": settings,
                "error": str(exc),
                "form": {
                    "story_prompt": story_prompt,
                    "character_name": character_name,
                    "setting": setting,
                    "tone": tone,
                    "art_style": art_style,
                    "panel_count": panel_count,
                },
            },
            status_code=500,
        )


@router.post("/generate-comic/json")
async def generate_json(
    data: ComicRequest,
):

    try:

        title, layout, pdf_url = _generate_comic(
            data
        )

        return JSONResponse(
            {
                "title": title,
                "panels": [
                    panel.model_dump()
                    for panel in layout
                ],
                "pdf_url": pdf_url,
            }
        )

    except Exception as exc:

        return JSONResponse(
            {
                "error": str(exc)
            },
            status_code=500,
        )


@router.get(
    "/export-success",
    response_class=HTMLResponse,
)
async def export_success(
    request: Request,
    pdf_url: str = "",
):

    return templates.TemplateResponse(
        request=request,
        name="export_success.html",
        context={
            "pdf_url": pdf_url
        },
    )


@router.post("/test-image")
async def test_image(
    prompt: str = Form(...),
):

    try:

        image_url = generate_panel_image(
            prompt,
            0,
            "Test Character",
            "comic book",
        )

        return {
            "image_url": image_url
        }

    except Exception as exc:

        return JSONResponse(
            {
                "error": str(exc)
            },
            status_code=500,
        )
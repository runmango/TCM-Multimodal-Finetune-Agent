from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, File, HTTPException, UploadFile

from app.core.paths import STATIC_DIR


router = APIRouter()

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp"}
MAX_FILE_SIZE = 5 * 1024 * 1024
TONGUE_UPLOAD_DIR = STATIC_DIR / "uploads" / "tongue"


@router.post("/tongue")
async def upload_tongue_image(file: UploadFile = File(...)) -> dict:
    suffix = Path(file.filename or "").suffix.lower()
    content_type = (file.content_type or "").lower()
    if suffix not in ALLOWED_EXTENSIONS or content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(status_code=400, detail="仅支持 jpg、jpeg、png、webp 格式的舌象图片。")

    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="上传文件为空。")
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="图片大小不能超过 5MB。")

    TONGUE_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    filename = "%s%s" % (uuid4().hex, suffix)
    target_path = TONGUE_UPLOAD_DIR / filename
    target_path.write_bytes(content)

    return {
        "url": "/static/uploads/tongue/%s" % filename,
        "filename": filename,
        "content_type": content_type,
        "size": len(content),
    }

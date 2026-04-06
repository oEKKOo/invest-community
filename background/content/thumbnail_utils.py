"""图片上传校验与缩略图生成（列表页小图、降低带宽）。"""
from __future__ import annotations

import os
from io import BytesIO

from django.core.files.base import ContentFile

# 与 Nginx client_max_body_size 等部署参数应对齐（略小于网关上限）
MAX_CONTENT_ATTACHMENT_BYTES = 12 * 1024 * 1024  # 12 MiB
MAX_COMMENT_ATTACHMENT_BYTES = 5 * 1024 * 1024  # 5 MiB
MAX_IMAGE_SIDE_PX = 8000

_IMAGE_EXT = {'.png', '.jpg', '.jpeg', '.webp'}


def _is_image_filename(name: str) -> bool:
    ext = os.path.splitext(name or '')[1].lower()
    return ext in _IMAGE_EXT


def validate_attachment_size(upload, max_bytes: int) -> None:
    size = getattr(upload, 'size', 0) or 0
    if size <= 0:
        raise ValueError('空文件')
    if size > max_bytes:
        mb = max_bytes // (1024 * 1024)
        raise ValueError(f'文件过大，最大允许 {mb}MB')


def validate_image_pixel_bounds(upload) -> None:
    """对图片检查宽高上限，避免极端分辨率拖垮 Pillow。"""
    from PIL import Image

    if not _is_image_filename(getattr(upload, 'name', '') or ''):
        return
    upload.seek(0)
    try:
        with Image.open(upload) as img:
            img.verify()
    except Exception as exc:
        raise ValueError('无法解析的图片文件') from exc
    upload.seek(0)
    try:
        with Image.open(upload) as img:
            w, h = img.size
    except Exception as exc:
        raise ValueError('无法读取图片尺寸') from exc
    finally:
        upload.seek(0)

    if w > MAX_IMAGE_SIDE_PX or h > MAX_IMAGE_SIDE_PX:
        raise ValueError(
            f'图片宽高过大，单边最大 {MAX_IMAGE_SIDE_PX}px（当前 {w}×{h}）'
        )


def generate_thumbnail_file(path: str, max_side: int = 400) -> ContentFile | None:
    """从已落盘的文件生成 JPEG 缩略图内容。"""
    from PIL import Image

    ext = os.path.splitext(path)[1].lower()
    if ext not in _IMAGE_EXT:
        return None
    try:
        with Image.open(path) as img:
            if img.mode not in ('RGB', 'L'):
                img = img.convert('RGB')
            img.thumbnail((max_side, max_side), Image.Resampling.LANCZOS)
            buf = BytesIO()
            img.save(buf, format='JPEG', quality=85, optimize=True)
            buf.seek(0)
            return ContentFile(buf.read(), name=f'thumb_{os.path.basename(path)}.jpg')
    except Exception:
        return None


def save_instance_thumbnail(instance, file_field: str = 'file', thumb_field: str = 'thumb') -> None:
    """为 ContentAttachment / CommentAttachment 生成并保存 thumb 字段。"""
    main = getattr(instance, file_field, None)
    if not main:
        return
    path = getattr(main, 'path', None)
    if not path or not os.path.exists(path):
        return
    thumb_content = generate_thumbnail_file(path)
    if not thumb_content:
        return
    tfield = getattr(instance, thumb_field)
    tfield.save(thumb_content.name, thumb_content, save=False)

from __future__ import annotations

import base64
import binascii
import io
import warnings
from typing import Literal

from PIL import Image, UnidentifiedImageError
from pydantic import BaseModel, Field, model_validator

from src.exam_types import (
    GENERAL,
    IELTS,
    IELTS_SUBTYPES,
    IELTS_TASK1,
    TOEFL,
    TOEFL_SUBTYPES,
)

MAX_IMAGE_BYTES = 5 * 1024 * 1024


class Credentials(BaseModel):
    username: str = Field(min_length=1, max_length=50, pattern=r"^[\w\-一-鿿]+$")
    password: str = Field(min_length=6, max_length=128)


class ReviewRequest(BaseModel):
    essay_text: str = Field(min_length=1, max_length=20000)
    exam_type: Literal[GENERAL, IELTS, TOEFL] = GENERAL
    exam_subtype: str | None = None
    essay_topic: str = Field(default="", max_length=2000)
    essay_image_b64: str | None = Field(default=None, max_length=4 * ((MAX_IMAGE_BYTES + 2) // 3))
    essay_image_mime: Literal["image/png", "image/jpeg", "image/webp"] | None = None

    @model_validator(mode="after")
    def validate_submission(self):
        if not 20 <= len(self.essay_text.split()) <= 1000:
            raise ValueError("作文需为 20–1000 词")
        subtypes = IELTS_SUBTYPES if self.exam_type == IELTS else TOEFL_SUBTYPES if self.exam_type == TOEFL else []
        if subtypes and self.exam_subtype not in subtypes:
            raise ValueError("请选择有效的任务类型")
        if not subtypes and self.exam_subtype:
            raise ValueError("通用作文无需任务子类型")
        if self.essay_image_b64:
            if self.exam_type != IELTS or self.exam_subtype != IELTS_TASK1:
                raise ValueError("仅 IELTS Task 1 支持题图")
            try:
                raw = base64.b64decode(self.essay_image_b64, validate=True)
                if len(raw) > MAX_IMAGE_BYTES:
                    raise ValueError("图片不能超过 5 MB")
                with warnings.catch_warnings():
                    warnings.simplefilter("error", Image.DecompressionBombWarning)
                    with Image.open(io.BytesIO(raw)) as image:
                        detected = Image.MIME.get(image.format)
                        if detected not in {"image/png", "image/jpeg", "image/webp"}:
                            raise ValueError("仅支持 PNG、JPEG、WebP")
                        if image.width * image.height > 20_000_000:
                            raise ValueError("图片分辨率过大")
                        image.verify()
                if self.essay_image_mime != detected:
                    raise ValueError("图片内容与声明格式不符")
            except (
                binascii.Error,
                UnidentifiedImageError,
                OSError,
                Image.DecompressionBombError,
                Image.DecompressionBombWarning,
            ) as exc:
                raise ValueError("图片文件损坏或格式无效") from exc
        elif self.essay_image_mime:
            raise ValueError("缺少图片内容")
        return self


class QuestionRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)
    exam_type: Literal[GENERAL, IELTS, TOEFL] = GENERAL

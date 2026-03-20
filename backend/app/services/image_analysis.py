import asyncio
import imghdr
import logging
from dataclasses import dataclass
from typing import Any, Dict, Optional

from backend.app.config.settings import settings

logger = logging.getLogger(__name__)

GENAI_AVAILABLE = False

try:
    from google import genai
    from google.genai import types

    GENAI_AVAILABLE = True
except ImportError:
    genai = None
    types = None


@dataclass
class ImageAnalysisResult:
    summary: str
    mode: str
    provider: str
    metadata: Dict[str, Any]


class ImageAnalysisService:
    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: Optional[str] = None,
    ):
        self.api_key = api_key or settings.GEMINI_API_KEY
        self.model_name = model_name or settings.IMAGE_ANALYSIS_MODEL_NAME
        self.client = None

        if GENAI_AVAILABLE and self.api_key:
            try:
                self.client = genai.Client(api_key=self.api_key)
            except Exception as exc:
                logger.warning("Falha ao inicializar cliente de análise de imagem: %s", exc)
                self.client = None

    async def analyze_image(
        self,
        image_bytes: bytes,
        mime_type: str,
        filename: str,
        prompt: str = "",
    ) -> ImageAnalysisResult:
        return await asyncio.to_thread(
            self._analyze_image_sync,
            image_bytes,
            mime_type,
            filename,
            prompt,
        )

    def _analyze_image_sync(
        self,
        image_bytes: bytes,
        mime_type: str,
        filename: str,
        prompt: str = "",
    ) -> ImageAnalysisResult:
        detected_format = imghdr.what(None, h=image_bytes)
        metadata: Dict[str, Any] = {
            "filename": filename,
            "mime_type": mime_type,
            "detected_format": detected_format or "unknown",
            "size_bytes": len(image_bytes),
        }

        default_prompt = (
            "Descreva a imagem em português de forma objetiva. "
            "Liste elementos visuais importantes, texto legível se houver, "
            "anomalias perceptíveis e possíveis implicações para o contexto de negócio."
        )
        effective_prompt = prompt.strip() or default_prompt

        if self.client is None or not GENAI_AVAILABLE or types is None:
            summary = (
                f"Imagem registrada para análise: {filename}. "
                f"Tipo detectado: {metadata['detected_format']}, MIME {mime_type}, "
                f"tamanho {len(image_bytes)} bytes. "
                "A análise visual detalhada depende do provider multimodal configurado."
            )
            return ImageAnalysisResult(
                summary=summary,
                mode="fallback_metadata",
                provider="local",
                metadata=metadata,
            )

        try:
            if hasattr(types.Part, "from_bytes"):
                image_part = types.Part.from_bytes(data=image_bytes, mime_type=mime_type)
            else:
                image_part = types.Part(
                    inline_data=types.Blob(data=image_bytes, mime_type=mime_type),
                )

            response = self.client.models.generate_content(
                model=self.model_name,
                contents=[effective_prompt, image_part],
            )
            summary = self._extract_response_text(response)
            if not summary.strip():
                raise ValueError("Resposta vazia do provider de visão")

            return ImageAnalysisResult(
                summary=summary.strip(),
                mode="vision_llm",
                provider="google_genai",
                metadata=metadata,
            )
        except Exception as exc:
            logger.warning("Falha na análise multimodal da imagem %s: %s", filename, exc)
            summary = (
                f"Imagem registrada para análise: {filename}. "
                f"Tipo detectado: {metadata['detected_format']}, MIME {mime_type}, "
                f"tamanho {len(image_bytes)} bytes. "
                "A análise visual detalhada falhou nesta tentativa; use estes metadados como fallback."
            )
            return ImageAnalysisResult(
                summary=summary,
                mode="vision_fallback_after_error",
                provider="local_fallback",
                metadata=metadata,
            )

    @staticmethod
    def _extract_response_text(response: Any) -> str:
        text = getattr(response, "text", None)
        if isinstance(text, str) and text.strip():
            return text

        candidates = getattr(response, "candidates", None) or []
        collected: list[str] = []
        for candidate in candidates:
            content = getattr(candidate, "content", None)
            parts = getattr(content, "parts", None) or []
            for part in parts:
                part_text = getattr(part, "text", None)
                if isinstance(part_text, str) and part_text.strip():
                    collected.append(part_text.strip())
        return "\n".join(collected).strip()

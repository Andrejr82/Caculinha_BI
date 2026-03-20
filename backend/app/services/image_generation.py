import asyncio
import base64
import html
from typing import Dict, Any


class ImageGenerationService:
    async def generate_image(self, prompt: str) -> Dict[str, Any]:
        return await asyncio.to_thread(self._generate_image_sync, prompt)

    def _generate_image_sync(self, prompt: str) -> Dict[str, Any]:
        normalized_prompt = " ".join(str(prompt or "").split())[:220] or "Conceito visual gerado pelo Caçulinha"
        escaped_prompt = html.escape(normalized_prompt)

        svg = f"""
<svg xmlns="http://www.w3.org/2000/svg" width="1024" height="1024" viewBox="0 0 1024 1024">
  <defs>
    <linearGradient id="bg" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#0f172a" />
      <stop offset="100%" stop-color="#1d4ed8" />
    </linearGradient>
  </defs>
  <rect width="1024" height="1024" fill="url(#bg)" rx="48" />
  <circle cx="860" cy="180" r="120" fill="#38bdf8" opacity="0.22" />
  <circle cx="220" cy="820" r="180" fill="#f59e0b" opacity="0.16" />
  <rect x="96" y="112" width="832" height="800" rx="40" fill="rgba(255,255,255,0.08)" stroke="rgba(255,255,255,0.18)" />
  <text x="128" y="220" fill="#e2e8f0" font-size="40" font-family="Segoe UI, Arial, sans-serif" font-weight="700">Conceito visual</text>
  <text x="128" y="290" fill="#bfdbfe" font-size="28" font-family="Segoe UI, Arial, sans-serif">Gerado como artefato visual do assistente</text>
  <foreignObject x="128" y="360" width="768" height="420">
    <div xmlns="http://www.w3.org/1999/xhtml" style="font-family:Segoe UI, Arial, sans-serif; color:#f8fafc; font-size:34px; line-height:1.35; font-weight:600;">
      {escaped_prompt}
    </div>
  </foreignObject>
  <text x="128" y="872" fill="#cbd5e1" font-size="22" font-family="Segoe UI, Arial, sans-serif">Modo fallback local SVG • pronto para provider visual quando disponível</text>
</svg>
""".strip()

        encoded_svg = base64.b64encode(svg.encode("utf-8")).decode("ascii")
        return {
            "url": f"data:image/svg+xml;base64,{encoded_svg}",
            "alt": normalized_prompt,
            "prompt": normalized_prompt,
            "provider": "local_svg_fallback",
            "format": "svg",
        }

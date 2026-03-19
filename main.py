import asyncio
import random

import requests

import astrbot.api.message_components as Comp
from astrbot.api import logger
from astrbot.api.event import AstrMessageEvent, filter
from astrbot.api.star import Context, Star, register
from astrbot.core.config import AstrBotConfig


@register("astrbot_plugin_mimo_tts", "MY-Final", "基于小米 MiMo API 的文本转语音插件", "1.0.0")
class MimoTTSPlugin(Star):
    def __init__(self, context: Context, config: AstrBotConfig):
        super().__init__(context)

        self.enable_tts = bool(config.get("enable_tts", True))
        self.api_key = str(config.get("api_key") or "")
        self.api_url = str(
            config.get("api_url") or "https://api.xiaomimimo.com/v1/chat/completions"
        )
        self.model = str(config.get("model") or "mimo-v2-tts")
        self.voice = str(config.get("voice") or "mimo_default")
        self.audio_format = str(config.get("audio_format") or "wav")

        try:
            self.timeout = max(5, int(config.get("timeout", 30)))
        except (TypeError, ValueError):
            self.timeout = 30

        try:
            self.tts_probability = max(
                0.0,
                min(100.0, float(config.get("tts_probability", 100))),
            )
        except (TypeError, ValueError):
            self.tts_probability = 100.0

        try:
            self.max_length = max(1, int(config.get("max_length", 120)))
        except (TypeError, ValueError):
            self.max_length = 120

        try:
            self.min_length = max(1, int(config.get("min_length", 1)))
        except (TypeError, ValueError):
            self.min_length = 1

        if self.enable_tts and not self.api_key:
            logger.warning("MiMo TTS 缺少 api_key，插件将无法合成语音")

    async def initialize(self):
        logger.info("MiMo TTS plugin 已启用")

    @filter.on_decorating_result()
    async def on_decorating_result(self, event: AstrMessageEvent):
        if not self.enable_tts:
            return
        if not self.api_key:
            return
        if not self._probability(self.tts_probability):
            return

        result = event.get_result()
        if not result or not result.chain:
            return

        text_parts = []
        for component in result.chain:
            if hasattr(component, "text") and component.text:
                text_parts.append(component.text)

        if not text_parts:
            return

        assistant_text = "".join(text_parts).strip()
        if len(assistant_text) < self.min_length or len(assistant_text) > self.max_length:
            return

        user_text = ""
        if hasattr(event, "message_str") and isinstance(event.message_str, str):
            user_text = event.message_str.strip()

        try:
            audio_b64 = await self.tts_synthesize(
                assistant_text=assistant_text,
                user_text=user_text,
            )
        except Exception as exc:
            logger.error(f"MiMo TTS 合成失败: {exc}")
            return

        if not audio_b64:
            return

        latest_result = event.get_result()
        if latest_result is None:
            return
        latest_result.chain = [Comp.Record.fromBase64(audio_b64)]

    def _probability(self, percent: float) -> bool:
        return random.random() < (percent / 100)

    def _build_payload(self, assistant_text: str, user_text: str) -> dict:
        messages = []
        if user_text:
            messages.append({"role": "user", "content": user_text})
        messages.append({"role": "assistant", "content": assistant_text})

        return {
            "model": self.model,
            "messages": messages,
            "audio": {
                "format": self.audio_format,
                "voice": self.voice,
            },
        }

    def _tts_synthesize_sync(self, assistant_text: str, user_text: str) -> str:
        headers = {
            "api-key": self.api_key,
            "Content-Type": "application/json",
        }
        payload = self._build_payload(assistant_text=assistant_text, user_text=user_text)

        response = requests.post(
            self.api_url,
            headers=headers,
            json=payload,
            timeout=self.timeout,
        )

        if response.status_code != 200:
            raise RuntimeError(
                f"HTTP {response.status_code}: {response.text[:300]}"
            )

        data = response.json()
        try:
            return data["choices"][0]["message"]["audio"]["data"]
        except (KeyError, IndexError, TypeError):
            raise RuntimeError(f"返回结构异常: {data}")

    async def tts_synthesize(self, assistant_text: str, user_text: str = "") -> str:
        if not assistant_text:
            return ""
        return await asyncio.to_thread(
            self._tts_synthesize_sync,
            assistant_text,
            user_text,
        )

    async def terminate(self):
        logger.info("MiMo TTS plugin 已停用")

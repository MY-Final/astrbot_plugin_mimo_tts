# astrbot_plugin_mimo_tts

AstrBot text-to-speech plugin powered by MiMo TTS API.

## Features

- Convert assistant text replies into voice messages automatically.
- Support MiMo voices such as `mimo_default`, `default_zh`, and `default_eh`.
- Optional probability and text length filters for TTS triggering.
- Configurable API endpoint, model, voice, format, and timeout.

## Configuration

This plugin reads config from `_conf_schema.json`:

- `enable_tts`: enable/disable plugin
- `api_key`: MiMo API key (required)
- `api_url`: API URL, default `https://api.xiaomimimo.com/v1/chat/completions`
- `model`: default `mimo-v2-tts`
- `voice`: default `mimo_default`
- `audio_format`: default `wav`
- `tts_probability`: 0-100 trigger probability
- `min_length` / `max_length`: assistant text length range
- `timeout`: HTTP timeout in seconds

## Reference

See `tts.md` for official API details and examples.

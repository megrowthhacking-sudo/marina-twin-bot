"""
Обёртка над Anthropic API: собирает system-блоки (core + активные страны) с
prompt caching (1 час) и делает вызов Messages API.
"""

import logging

from anthropic import Anthropic

import config
import kb

logger = logging.getLogger(__name__)

client = Anthropic(api_key=config.ANTHROPIC_API_KEY)

_kb = kb.load_core()


def build_system_blocks(active_countries: list[str]) -> list[dict]:
    blocks = [
        {
            "type": "text",
            "text": _kb.core_text,
            # Час — потому что сотрудники пишут не непрерывно; час даёт кэш-хиты
            # между сообщениями без переплаты за перечитывание ~350к токенов базы.
            "cache_control": {"type": "ephemeral", "ttl": "1h"},
        }
    ]
    if active_countries:
        country_text = "".join(_kb.country_text(code) for code in active_countries)
        blocks.append(
            {
                "type": "text",
                "text": country_text,
                "cache_control": {"type": "ephemeral", "ttl": "1h"},
            }
        )
    return blocks


def ask_marina_twin(history: list[dict], active_countries: list[str]) -> str:
    """history — список {"role": "user"/"assistant", "content": str}, уже включая
    последнее сообщение пользователя."""
    system_blocks = build_system_blocks(active_countries)

    response = client.messages.create(
        model=config.MODEL_NAME,
        max_tokens=config.MAX_OUTPUT_TOKENS,
        system=system_blocks,
        messages=[{"role": m["role"], "content": m["content"]} for m in history],
    )

    usage = response.usage
    logger.info(
        "Claude usage: input=%s cache_write=%s cache_read=%s output=%s",
        usage.input_tokens,
        getattr(usage, "cache_creation_input_tokens", None),
        getattr(usage, "cache_read_input_tokens", None),
        usage.output_tokens,
    )

    text_parts = [block.text for block in response.content if block.type == "text"]
    return "\n".join(text_parts).strip()

"""
Загрузка базы знаний Marina Twin и определение, о какой стране идёт речь в разговоре.

Архитектура:
- "core" — системный промпт + право РФ + скилы + наднациональное право ЕАЭС.
  Грузится всегда, для всех чатов, и кэшируется на стороне Claude API (ephemeral, 1 час).
- "country modules" — национальные модули по остальным странам СНГ/ЕАЭС.
  Подключаются в разговор только когда в сообщениях упоминается конкретная страна,
  и держатся "прилипшими" к чату, пока не появится другая страна (см. storage.py).
"""

import logging
import re
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)

KB_DIR = Path(__file__).parent / "kb"

# Порядок важен: сначала персона, потом базы. Это единый текст, который кэшируется
# одним cache_control breakpoint-ом.
CORE_FILES = [
    "MarinaTwin_00_SYSTEM_PROMPT.md",
    "MarinaTwin_KB_RU_LAW.md",
    "MarinaTwin_KB_SKILLS.md",
    "MarinaTwin_KB_LAW_EAEU.md",
    "MarinaTwin_OPS_ALTYN_ACCOUNTS_GATEWAYS.md",
    "MarinaTwin_OPS_ATLAS_PARTNERS_CONTRACTS.md",
    "MarinaTwin_KB_SKILLS_EXT.md",
]

# code страны -> (человекочитаемое имя, имя файла, ключевые слова/подстроки для распознавания
# в тексте сообщения; ищутся регистронезависимо, как подстроки в словах).
COUNTRY_MODULES = {
    "BELARUS": (
        "Беларусь",
        "MarinaTwin_KB_LAW_BELARUS.md",
        ["беларус", "белорус", "минск"],
    ),
    "KAZAKHSTAN": (
        "Казахстан",
        "MarinaTwin_KB_LAW_KAZAKHSTAN.md",
        ["казахст", "казах", "алматы", "астана", "нур-султан", "мфца", "aifc"],
    ),
    "ARMENIA": (
        "Армения",
        "MarinaTwin_KB_LAW_ARMENIA.md",
        ["армен", "ереван", "amd "],
    ),
    "KYRGYZSTAN": (
        "Киргизия",
        "MarinaTwin_KB_LAW_KYRGYZSTAN.md",
        ["киргиз", "кыргыз", "бишкек"],
    ),
    "UZBEKISTAN": (
        "Узбекистан",
        "MarinaTwin_KB_LAW_UZBEKISTAN.md",
        ["узбек", "ташкент"],
    ),
    "TAJIKISTAN": (
        "Таджикистан",
        "MarinaTwin_KB_LAW_TAJIKISTAN.md",
        ["таджик", "душанбе"],
    ),
    "TURKMENISTAN": (
        "Туркменистан",
        "MarinaTwin_KB_LAW_TURKMENISTAN.md",
        ["туркмен", "ашхабад"],
    ),
    "AZERBAIJAN": (
        "Азербайджан",
        "MarinaTwin_KB_LAW_AZERBAIJAN.md",
        ["азербайджан", "азерб", "баку"],
    ),
    "MOLDOVA": (
        "Молдова",
        "MarinaTwin_KB_LAW_MOLDOVA.md",
        ["молдов", "кишинев", "кишинёв", "приднестров", "гагауз"],
    ),
}

# Слова, при упоминании которых (и отсутствии слов других стран) чат явно "возвращается"
# в Россию — есть смысл сбросить прилипшие страновые модули, чтобы не таскать их зря.
RUSSIA_RESET_KEYWORDS = ["росси", " рф ", "рф,", "рф.", "российск"]

MAX_ACTIVE_COUNTRIES = 3  # не более N стран одновременно в контексте одного чата


@dataclass
class KnowledgeBase:
    core_text: str

    def __post_init__(self):
        self._country_cache: dict[str, str] = {}

    def country_text(self, code: str) -> str:
        if code not in self._country_cache:
            name, filename, _ = COUNTRY_MODULES[code]
            path = KB_DIR / filename
            content = path.read_text(encoding="utf-8")
            self._country_cache[code] = (
                f"\n\n=== {filename} (подключён: разговор о стране «{name}») ===\n\n"
                + content
            )
        return self._country_cache[code]


def load_core() -> KnowledgeBase:
    parts = []
    for filename in CORE_FILES:
        path = KB_DIR / filename
        if not path.exists():
            raise FileNotFoundError(f"Не найден обязательный файл базы знаний: {path}")
        text = path.read_text(encoding="utf-8")
        parts.append(f"\n\n=== {filename} ===\n\n{text}")
        logger.info("Загружен core-файл %s (%d символов)", filename, len(text))
    core_text = "".join(parts).lstrip("\n")
    logger.info("Core-база собрана: %d символов", len(core_text))
    return KnowledgeBase(core_text=core_text)


def detect_countries(text: str) -> set[str]:
    """Ищет упоминания стран СНГ/ЕАЭС (кроме РФ) в тексте сообщения."""
    lowered = f" {text.lower()} "
    found = set()
    for code, (_, _, keywords) in COUNTRY_MODULES.items():
        for kw in keywords:
            if kw in lowered:
                found.add(code)
                break
    return found


def mentions_russia_only(text: str) -> bool:
    lowered = f" {text.lower()} "
    has_russia = any(kw in lowered for kw in RUSSIA_RESET_KEYWORDS)
    has_other = bool(detect_countries(text))
    return has_russia and not has_other

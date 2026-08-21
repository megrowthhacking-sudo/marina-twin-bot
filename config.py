import os

TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]

MODEL_NAME = os.environ.get("MARINATWIN_MODEL", "claude-sonnet-5")
MAX_OUTPUT_TOKENS = int(os.environ.get("MARINATWIN_MAX_TOKENS", "4096"))

# Через запятую: telegram user_id сотрудников, которым разрешено писать боту.
# Пусто = доступ разрешён всем (годится только для локального теста!).
_allowed_raw = os.environ.get("MARINATWIN_ALLOWED_USER_IDS", "").strip()
ALLOWED_USER_IDS = {int(x) for x in _allowed_raw.split(",") if x.strip()} if _allowed_raw else None

# --- ClickUp: сбор задач из групповых чатов ---
# Личный API-токен (ClickUp → аватар → Settings → Apps → API Token). Формат pk_...
CLICKUP_API_TOKEN = os.environ.get("CLICKUP_API_TOKEN", "").strip() or None
# ID списка (List), куда падают все задачи из всех групп (MVP: один общий список).
# Смотри в URL списка в вебе ClickUp — там есть .../li/<ID>.
CLICKUP_LIST_ID = os.environ.get("CLICKUP_LIST_ID", "").strip() or None
# Как часто автоматически выгружать накопленные задачи из всех групп (минуты).
CLICKUP_FLUSH_INTERVAL_MINUTES = int(os.environ.get("CLICKUP_FLUSH_INTERVAL_MINUTES", "120"))
# Интеграция с ClickUp включена только если заданы оба значения.
CLICKUP_ENABLED = bool(CLICKUP_API_TOKEN and CLICKUP_LIST_ID)

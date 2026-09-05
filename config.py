import os

TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]

MODEL_NAME = os.environ.get("MARINATWIN_MODEL", "claude-sonnet-5")
MAX_OUTPUT_TOKENS = int(os.environ.get("MARINATWIN_MAX_TOKENS", "4096"))

# "Лёгкая" модель для фоновых/технических вызовов без базы знаний и без голоса
# Марины (разбор чата в JSON-задачи, пересказ уже готового ответа) — там, где
# не нужна полная Sonnet-модель. В ~2 раза дешевле по input и output токенам.
LIGHT_MODEL_NAME = os.environ.get("MARINATWIN_LIGHT_MODEL", "claude-haiku-4-5")

# Через запятую: telegram user_id сотрудников, которым разрешено писать боту.
# Пусто = доступ разрешён всем (годится только для локального теста!).
_allowed_raw = os.environ.get("MARINATWIN_ALLOWED_USER_IDS", "").strip()
ALLOWED_USER_IDS = {int(x) for x in _allowed_raw.split(",") if x.strip()} if _allowed_raw else None

# --- ClickUp: сбор задач из групповых чатов ---
# Личный API-токен (ClickUp → аватар → Settings → Apps → API Token). Формат pk_...
CLICKUP_API_TOKEN = os.environ.get("CLICKUP_API_TOKEN", "").strip() or None

# Проекты и их списки (List) в ClickUp.
#
# Чат закрепляется за проектом двумя способами: (1) кто-то в чате явно пишет
# "эта группа про задачи <проект>" (см. kb-detect в bot.py, ключевые слова ниже),
# (2) вызовом команды /tasks<project> прямо в чате. Оба способа запоминают проект
# за чатом — дальше периодическая автовыгрузка сама знает, куда слать задачи из
# этого чата, без повторных действий.
#
# "unsorted" — проект без ключевых слов, но теперь с собственной командой (/tasksmisc):
# чат можно явно закрепить за ним так же, как за остальными тремя. При этом он
# по-прежнему остаётся списком по умолчанию для чатов БЕЗ закреплённого проекта
# ("группа, где обсуждают всё подряд") — туда Marina Twin складывает задачи,
# для которых не смогла по контексту понять, к какому из трёх проектов они относятся.
CLICKUP_PROJECTS = {
    "atlas": {
        "env": "CLICKUP_LIST_ATLAS",
        "label": "Atlas",
        "command": "tasksatlas",
        "keywords": ("atlas", "атлас"),
    },
    "altyn": {
        "env": "CLICKUP_LIST_ALTYN",
        "label": "Алтын",
        "command": "tasksaltyn",
        "keywords": ("altyn", "алтын"),
    },
    "bestswift": {
        "env": "CLICKUP_LIST_BESTSWIFT",
        "label": "BestSwift",
        "command": "tasksbs",
        "keywords": ("bestswift", "best swift", "bs"),
    },
    "unsorted": {
        "env": "CLICKUP_LIST_UNSORTED",
        "label": "Разобрать",
        "command": "tasksmisc",
        "keywords": ("смешанная группа", "разобрать"),
    },
}
# {"atlas": "901820614918", "altyn": "901820614919", ...} — только реально заданные.
CLICKUP_LIST_IDS = {
    key: os.environ[project["env"]].strip()
    for key, project in CLICKUP_PROJECTS.items()
    if os.environ.get(project["env"], "").strip()
}

# Как часто автоматически выгружать накопленные задачи (минуты) — для всех чатов
# с непрочитанными сообщениями, не только закреплённых за проектом.
CLICKUP_FLUSH_INTERVAL_MINUTES = int(os.environ.get("CLICKUP_FLUSH_INTERVAL_MINUTES", "120"))

# Сколько минут ждать ответа на уточняющий вопрос "Atlas, Altyn или BestSwift?" в
# "смешанном" чате (см. _ask_classification_question в bot.py), прежде чем сдаться и
# сама положить задачу в "Разобрать". По умолчанию сутки.
CLICKUP_CLASSIFICATION_TIMEOUT_MINUTES = int(os.environ.get("CLICKUP_CLASSIFICATION_TIMEOUT_MINUTES", "1440"))
# Интеграция с ClickUp включена, если задан токен и хотя бы один список проекта.
CLICKUP_ENABLED = bool(CLICKUP_API_TOKEN and CLICKUP_LIST_IDS)
# Сопоставление имени ответственного (как его называют в переписке — см. task_extractor.py,
# поле assignee_name) с ClickUp user_id, чтобы автоматически проставлять Assignee на
# созданной задаче (см. _resolve_assignee_id в bot.py). Если имени нет в словаре —
# Assignee просто не проставляется, в заголовке задачи имя всё равно останется (см.
# task_extractor.py). Ключи — в нижнем регистре, сравнение регистронезависимое.
CLICKUP_ASSIGNEE_MAP = {
    "юрий тучнолюбов": 113538374,
    "yuri tuchnolubov": 113538374,
    "юрий": 113538374,
    "yuri": 113538374,
    "николай хребет": 113538064,
    "nikolay hrebet": 113538064,
    "хребет": 113538064,
    "николай": 113538064,
    "ник галт": 113538351,
    "nick galt": 113538351,
    "галт": 113538351,
    "ник": 113538351,
    "марина копылова": 113538088,
    "maryna kopylova": 113538088,
    "марина": 113538088,
    "дарья генералова": 113538057,
    "дария генералова": 113538057,
    "daria generalova": 113538057,
    "дарья": 113538057,
    "дария": 113538057,
    "daria": 113538057,
    "liliana g": 113538063,
    "лилиана": 113538063,
    "liliana": 113538063,
    "lili lili": 113538039,
    "лили лили": 113538039,
    "светлана": 113538038,
    "илья евдокимов": 113538037,
    "ilya evdokimov": 113538037,
    "илья": 113538037,
    "ilya": 113538037,
    "назгул": 113538036,
    "ольга абрамова": 113538035,
    "olga abramova": 113538035,
    "ольга": 113538035,
    "оля": 113538035,
    "olga": 113538035,
}

# Часовой пояс утреннего дайджеста (IANA-имя, например "Europe/Moscow" или
# "Asia/Almaty") и время, во сколько его слать владелице — по каждому проекту
# отдельным сообщением полный список открытых задач из ClickUp, срочные помечены 🔴
# (см. daily_digest_job в bot.py).
MARINATWIN_TIMEZONE = os.environ.get("MARINATWIN_TIMEZONE", "Europe/Moscow").strip() or "Europe/Moscow"
DAILY_DIGEST_HOUR = int(os.environ.get("DAILY_DIGEST_HOUR", "9"))
DAILY_DIGEST_MINUTE = int(os.environ.get("DAILY_DIGEST_MINUTE", "0"))

# Telegram user_id владелицы (Марины) — только ей пересылаются вопросы из групп,
# адресованные "Марине" (см. эскалацию в bot.py). Если не задан явно, но задан ровно
# один MARINATWIN_ALLOWED_USER_IDS — используем его. Иначе эскалация выключена.
_owner_raw = os.environ.get("MARINATWIN_OWNER_USER_ID", "").strip()
if _owner_raw:
    OWNER_USER_ID = int(_owner_raw)
elif ALLOWED_USER_IDS and len(ALLOWED_USER_IDS) == 1:
    OWNER_USER_ID = next(iter(ALLOWED_USER_IDS))
else:
    OWNER_USER_ID = None

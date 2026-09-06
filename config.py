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

# ID workspace (team) в ClickUp — нужен персональным командам по сотрудникам
# (/lili /olga /sveta /ilya /nazgul /alex /ub /marina, см. EMPLOYEE_COMMANDS ниже и
# bot.py::_send_employee_report), которые по прямой просьбе владелицы (06.09) ищут
# задачи ПО ВСЕМУ ClickUp (все пространства/папки/списки), а не только в 4 проектных
# списках (CLICKUP_LIST_IDS выше) — сотрудники нередко ведут задачи и в личных
# папках/пространствах вне этих 4 официальных проектов. Значение — числовой id
# воркспейса верхнего уровня (виден в URL ClickUp сразу после app.clickup.com/, или
# через ClickUp API GET /team). Команды по сотрудникам работают только если задан и
# CLICKUP_API_TOKEN, и это значение — см. CLICKUP_TEAM_WIDE_ENABLED ниже.
CLICKUP_TEAM_ID = os.environ.get("CLICKUP_TEAM_ID", "").strip() or None
CLICKUP_TEAM_WIDE_ENABLED = bool(CLICKUP_API_TOKEN and CLICKUP_TEAM_ID)
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

# Персональные команды по сотрудникам (по просьбе владелицы, 06.09): /lili /olga /sveta
# /ilya /nazgul /alex /ub /marina /nikolay /nick (двое последних добавлены позже той же
# части 06.09 — Николай Хребет и Ник Галт) — каждая выгружает в личку владелицы открытые
# задачи ЭТОГО человека по всему ClickUp workspace (см. CLICKUP_TEAM_WIDE_ENABLED выше и
# bot.py::_send_employee_report), а не по отдельным личным папкам ClickUp ("Саша"/"Ник"/...
# в иерархии воркспейса) — это ручной архив вне зоны ответственности бота. Ключ словаря =
# имя Telegram-команды без "/" (буквы/цифры/"_", кириллица Telegram не распознаёт как
# команду — поэтому "Назгул" стала "/nazgul"). "assignee_id" — ClickUp user_id для
# серверной фильтрации (см. clickup_client.get_open_tasks/get_open_tasks_team_wide); у
# Саши реального аккаунта ClickUp нет, поэтому для него assignee_id=None, а вместо этого
# задаётся "name_prefix" — задачи находятся по буквальному текстовому префиксу "Саша:" в
# начале названия задачи (так их заводит task_extractor.py, когда не может сопоставить
# упомянутое имя с реальным ClickUp-аккаунтом, см. CLICKUP_ASSIGNEE_MAP выше). Для КАЖДОГО
# ключа этого словаря bot.py автоматически заводит ещё и "weekly"-версию команды
# (например "/nikolayweekly") — см. CLICKUP_LIST_WEEKLY ниже.
# "telegram_username" (часть 30, по прямой просьбе владелицы) — @username сотрудника,
# КАК ЕГО ПРИСЛАЛА ВЛАДЕЛИЦА, в нижнем регистре и без "@" (сравнение с реальным
# update.effective_user.username идёт регистронезависимо, см.
# bot.py::_maybe_capture_employee_telegram_id). Сам по себе username НЕ годится для
# отправки сообщений (Telegram API требует числовой user_id, который бот узнаёт только
# из реального сообщения этого человека) — как только кто-то с таким username напишет
# что угодно в личку боту или в любую группу, где бот присутствует, его настоящий
# telegram_user_id автоматически сохранится в storage.employee_telegram_ids и кнопка
# "➡️ Переслать" начнёт работать для него сама, без правки кода/конфига.
EMPLOYEE_COMMANDS = {
    "lili": {"label": "Лили", "assignee_id": 113538039, "telegram_username": "ffforgetmenot"},
    "olga": {"label": "Ольга", "assignee_id": 113538035, "telegram_username": "yama_888"},
    "sveta": {"label": "Света", "assignee_id": 113538038, "telegram_username": "claire_claire_bs"},
    "ilya": {"label": "Илья", "assignee_id": 113538037, "telegram_username": "fesius_altyn"},
    "nazgul": {"label": "Назгул", "assignee_id": 113538036, "telegram_username": "asisst_0_0"},
    "ub": {"label": "Юрий Борисович", "assignee_id": 113538374},
    "alex": {"label": "Саша", "assignee_id": None, "name_prefix": "саша:"},
    "marina": {"label": "Марина", "assignee_id": 113538088},
    "nikolay": {"label": "Николай Хребет", "assignee_id": 113538064, "telegram_username": "nikolai_ip_lawyer"},
    "nick": {"label": "Ник Галт", "assignee_id": 113538351},
}

# Telegram user_id сотрудников — по прямой просьбе владелицы (часть 29): кнопка
# "➡️ Переслать" под отчётом/задачей должна уметь переслать её конкретному человеку в
# Telegram, а не только показывать в личке владелицы. Технически Telegram-бот может
# писать только тем, чей user_id ему уже известен (человек должен был хоть раз сам
# написать боту) — поэтому это НЕ автоматический разбор, а ручная настройка через
# отдельные env-переменные (владелица присылает id/@username, дальше их можно узнать
# через любого "id-бота" в Telegram, например @userinfobot). Пока переменная не задана
# для кого-то — этот человек просто не появляется в списке получателей "Переслать" (см.
# bot.py::_available_forward_recipients), без падения бота.
_EMPLOYEE_TELEGRAM_ID_ENV = {
    "lili": "TELEGRAM_ID_LILI",
    "olga": "TELEGRAM_ID_OLGA",
    "sveta": "TELEGRAM_ID_SVETA",
    "ilya": "TELEGRAM_ID_ILYA",
    "nazgul": "TELEGRAM_ID_NAZGUL",
    "ub": "TELEGRAM_ID_UB",
    "alex": "TELEGRAM_ID_ALEX",
    "marina": "TELEGRAM_ID_MARINA",
    "nikolay": "TELEGRAM_ID_NIKOLAY",
    "nick": "TELEGRAM_ID_NICK",
}
for _employee_key, _env_name in _EMPLOYEE_TELEGRAM_ID_ENV.items():
    _raw_tg_id = os.environ.get(_env_name, "").strip()
    if _raw_tg_id:
        try:
            EMPLOYEE_COMMANDS[_employee_key]["telegram_user_id"] = int(_raw_tg_id)
        except ValueError:
            pass

# Список ClickUp "WEEKLY TASKS" (id 901819932817) в пространстве "РАСПИСАНИЕ" — по прямой
# просьбе владелицы (06.09): для каждого человека из EMPLOYEE_COMMANDS выше заведена ещё
# и "weekly"-команда (например "/nikolayweekly", см. bot.py::_send_employee_weekly_report),
# которая ищет задачи этого человека НЕ по всему ClickUp, а ТОЛЬКО в этом одном общем
# списке — в отличие от команд без "weekly" (которые ищут по всему workspace, см.
# CLICKUP_TEAM_ID выше). Значение — id списка, найден через
# mcp__ClickUp__clickup_get_workspace_hierarchy (пространство "РАСПИСАНИЕ" содержит ровно
# один список верхнего уровня — "WEEKLY TASKS"; отдельные списки "WEEKLY TASKS (copy)" в
# других местах воркспейса — шаблоны, не эта же самая задача).
CLICKUP_LIST_WEEKLY = os.environ.get("CLICKUP_LIST_WEEKLY", "").strip() or None
CLICKUP_WEEKLY_ENABLED = bool(CLICKUP_API_TOKEN and CLICKUP_LIST_WEEKLY)

# "Явная постановка задачи" (по прямой просьбе владелицы, 06.09): "Поставь Свете задачу
# в WEEKLY в статус Понедельник с пометкой срочно ...". Чтобы понять, в какой ИМЕННО
# ClickUp-список положить такую задачу, бот сопоставляет названное владелицей
# пространство/список с одной из уже существующих записей — теми же 4 официальными
# проектами (CLICKUP_LIST_IDS/CLICKUP_PROJECTS выше), плюс отдельно списком WEEKLY TASKS
# (CLICKUP_LIST_WEEKLY) под ключом "weekly". Сознательно не отдельный источник истины —
# собран из уже существующих структур, чтобы новый проектный список не пришлось заводить
# дважды (см. bot.py::_resolve_task_target, task_command.py).
CLICKUP_TASK_TARGETS = {
    key: {
        "list_id": list_id,
        "label": CLICKUP_PROJECTS[key]["label"],
        "keywords": CLICKUP_PROJECTS[key]["keywords"],
    }
    for key, list_id in CLICKUP_LIST_IDS.items()
}
if CLICKUP_LIST_WEEKLY:
    CLICKUP_TASK_TARGETS["weekly"] = {
        "list_id": CLICKUP_LIST_WEEKLY,
        "label": "Weekly (Расписание)",
        "keywords": ("weekly", "виикли", "расписание", "неделя", "недельные"),
    }

# Настоящий ClickUp-тег для кнопки "🔥 Горит" (по прямой просьбе владелицы, часть 27 —
# заменяет прежнее чисто локальное поведение части 24, см. bot.py::_is_fire/
# clickup_client.ensure_tag_on_task): теперь эта кнопка реально ставит/снимает тег на
# карточке задачи в самом ClickUp (виден и в веб-интерфейсе ClickUp, не только в боте),
# а не просто переставляет порядок внутри бота.
CLICKUP_FIRE_TAG_NAME = "кричащая задача"

# Имена ClickUp-пространств (space) по id — сам ClickUp API не отдаёт имя пространства
# прямо в объекте задачи (только id, см. clickup_client.get_open_tasks_team_wide/get_task),
# поэтому для отображения "где стоит задача" (пространство/папка/список — по прямой
# просьбе владелицы, часть 27, см. bot.py::_format_task_location) сопоставление сделано
# вручную по данным живого запроса mcp__ClickUp__clickup_get_workspace_hierarchy, а не
# через отдельный API-вызов на каждую задачу.
CLICKUP_SPACE_NAMES = {
    "901812152944": "РАСПИСАНИЕ",
    "901811161221": "BOD TASKS",
    "901811161043": "ONBOARDING TASKS",
    "901811160404": "RU PAYMENT GATES",
    "901811161065": "МАРКЕТИНГ",
    "901811161056": "АДМИН ЗАДАЧИ НАШИ КОМПАНИИ",
    "901811160844": "ШАБЛОНЫ",
    "901812689518": "Twin",
}

# Команды по статусам списка WEEKLY TASKS (по прямой просьбе владелицы, часть 27, см.
# bot.py::_send_weekly_status_report) — каждая показывает ВСЕ открытые задачи списка
# WEEKLY TASKS с этим статусом, по всем ответственным сразу (в отличие от персональных
# команд по сотрудникам выше, эти НЕ фильтруются по одному человеку). Статусы сверены
# живым запросом mcp__ClickUp__clickup_get_list(list_id=CLICKUP_LIST_WEEKLY) — ключи
# словаря НЕ обязательно совпадают с именем статуса дословно: кириллические статусы "на
# согласовании"/"документы в разработке" и дни недели получили латинские имена команд,
# потому что Telegram не распознаёт кириллицу как имя команды (см. также
# EMPLOYEE_COMMANDS выше) — сам статус для фильтрации задан отдельно полем "status".
# "Отложенные" и "задачи 2026" добавлены отдельным заходом (по прямой просьбе владелицы:
# "/отложенные /main tasks") — Telegram не даёт ни кириллицу, ни пробел в имени команды,
# поэтому "отложенные" → /postponed, "задачи 2026" → /maintasks (рабочее толкование
# "main tasks" как статуса "задачи 2026"; статус "complete" по-прежнему не включён — это
# служебный закрывающий статус ClickU, не рабочая очередь).
CLICKUP_WEEKLY_STATUS_COMMANDS = {
    "unsorted": {"label": "Unsorted", "status": "unsorted"},
    "atlas": {"label": "Atlas", "status": "atlas"},
    "altyn": {"label": "Altyn", "status": "altyn"},
    "approval": {"label": "На согласовании", "status": "на согласовании"},
    "docsdev": {"label": "Документы в разработке", "status": "документы в разработке"},
    "monday": {"label": "Понедельник", "status": "понедельник"},
    "tuesday": {"label": "Вторник", "status": "вторник"},
    "wednesday": {"label": "Среда", "status": "среда"},
    "thursday": {"label": "Четверг", "status": "четверг"},
    "friday": {"label": "Пятница", "status": "пятница"},
    "saturday": {"label": "Суббота", "status": "суббота"},
    "sunday": {"label": "Воскресенье", "status": "воскресенье"},
    "postponed": {"label": "Отложенные", "status": "отложенные"},
    "maintasks": {"label": "Задачи 2026", "status": "задачи 2026"},
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

# --- Google Calendar: постановка встреч из личного диалога с владелицей ---
# GOOGLE_SERVICE_ACCOUNT_JSON — полное содержимое JSON-ключа сервисного аккаунта Google
# (Cloud Console → IAM → Service Accounts → Keys). Владелица делится своим личным
# календарём с email этого сервисного аккаунта (Settings → Share with specific people →
# "Make changes to events") — без OAuth-флоу и без истекающих токенов, надёжнее для
# постоянно работающего сервера. GOOGLE_CALENDAR_ID — обычно её собственный gmail-адрес
# (id основного календаря совпадает с адресом почты).
GOOGLE_SERVICE_ACCOUNT_JSON = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON", "").strip() or None
GOOGLE_CALENDAR_ID = os.environ.get("GOOGLE_CALENDAR_ID", "").strip() or None
GOOGLE_CALENDAR_ENABLED = bool(GOOGLE_SERVICE_ACCOUNT_JSON and GOOGLE_CALENDAR_ID)

# Как часто обновлять "память" групповых чатов — скользящую текстовую сводку того, что
# обсуждалось в каждом чате, чтобы черновики ответов Марине (см. escalation.draft_initial_answer,
# chat_memory.py, bot.py::periodic_memory_job) учитывали более раннюю переписку, а не только
# сам вопрос (по прямой просьбе владелицы, 06.09). Работает независимо от
# CLICKUP_FLUSH_INTERVAL_MINUTES выше — это отдельный процесс со своим курсором
# (storage.chat_memory), не связанный с выгрузкой задач в ClickUp. Раз в 30 минут по
# умолчанию — компромисс между свежестью памяти и лишними вызовами лёгкой модели в тихих
# чатах (сам job пропускает чаты без новых сообщений, см. get_chats_with_new_messages_for_memory).
MEMORY_UPDATE_INTERVAL_MINUTES = int(os.environ.get("MEMORY_UPDATE_INTERVAL_MINUTES", "30"))

# Список ClickUp (папка "Расписание Марина Twin", список "Встречи"), куда зеркалятся все
# подтверждённые встречи из Google Calendar — по просьбе владелицы, чтобы видеть своё
# расписание и в ClickUp тоже. Список создан отдельно от 4 проектных
# (config.CLICKUP_LIST_IDS) — приватность (видимость только владелице) настраивается в
# самом ClickUp через Guests & Permissions списка/папки, это не поле API. Если не задан —
# зеркалирование просто не происходит (событие в календаре всё равно создаётся).
CLICKUP_LIST_SCHEDULE = os.environ.get("CLICKUP_LIST_SCHEDULE", "").strip() or None

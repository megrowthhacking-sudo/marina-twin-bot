"""Подтверждение перед публикацией для /calendarclickup (03.10.2026, по прямой просьбе
владелицы): бот сначала присылает ПЛАН изменений календаря в личку с кнопками
"✅ Опубликовать" / "✏️ Изменить" / "❌ Отмена", и только после "Опубликовать" пишет в
Google Calendar (clickup_meeting_watch.apply_calendar_actions — единственное место записи).
"Изменить" — владелица присылает правку текстом, план обновляется и показывается снова с
теми же тремя кнопками, и так без ограничений; "Отмена" отменяет команду целиком.
Вынесено из bot.py в отдельный модуль, потому что bot.py запускается как __main__ и не
может быть импортирован отсюда: нужные ему хелперы передаются через bind() (вызывается в
bot.py перед build_application). Планы хранятся в памяти процесса (app.bot_data) и теряются
при рестарте — тогда кнопка отвечает "план уже не актуален"."""
import logging
import uuid
from datetime import datetime
from zoneinfo import ZoneInfo
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackQueryHandler, ContextTypes
import calendar_client
import clickup_meeting_watch
import config
logger = logging.getLogger("marina_twin_bot")
_d: dict = {}
def bind(*, period_bounds, period_labels, period_keyboard, format_event_line, split_for_telegram, message_limit) -> None:
    """Передаёт хелперы bot.py (см. комментарий в начале модуля)."""
    _d.update(
        period_bounds=period_bounds,
        period_labels=period_labels,
        period_keyboard=period_keyboard,
        format_event_line=format_event_line,
        split_for_telegram=split_for_telegram,
        message_limit=message_limit,
    )
def get_awaiting(context: ContextTypes.DEFAULT_TYPE):
    """plan_id плана, для которого владелица нажала "Изменить" и теперь присылает правку, либо None."""
    return context.application.bot_data.get(AWAITING_KEY)
def register(app) -> None:
    """Регистрирует обработчики кнопок. Вызывать ДО регистрации старого обработчика "^ccu:"
    в bot.py — побеждает первый подходящий."""
    app.add_handler(CallbackQueryHandler(period_callback, pattern=r"^ccu:"))
    app.add_handler(CallbackQueryHandler(plan_callback, pattern=r"^ccup:"))
PLANS_KEY = "ccu_plans"
AWAITING_KEY = "ccu_awaiting_edit"
MAX_PLANS = 5
def _ccu_plan_keyboard(plan_id: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("✅ Опубликовать", callback_data=f"ccup:pub:{plan_id}"),
                InlineKeyboardButton("✏️ Изменить", callback_data=f"ccup:edit:{plan_id}"),
            ],
            [InlineKeyboardButton("❌ Отмена", callback_data=f"ccup:cancel:{plan_id}")],
        ]
    )
def _ccu_format_event_lines(label: str, events: list[dict]) -> str:
    """Список событий календаря за период тем же форматом, что и /calendar, с обрезкой
    под лимит сообщения Telegram."""
    tz = ZoneInfo(config.MARINATWIN_TIMEZONE)
    if not events:
        return f"\U0001f4c5 {label}: событий нет."
    header = f"\U0001f4c5 {label} ({len(events)}):\n\n"
    body = "\n".join(_d["format_event_line"](e, tz) for e in events)
    if len(header) + len(body) > _d["message_limit"] - 400:
        budget = _d["message_limit"] - 400 - len(header) - 80
        truncated = body[:budget] if budget > 0 else ""
        cut = truncated.rfind("\n")
        if cut != -1:
            truncated = truncated[:cut]
        shown = truncated.count("\n") + 1 if truncated else 0
        body = f"{truncated}\n\n...и ещё {len(events) - shown} событий, не поместились — сузь период."
    return header + body
def _ccu_render_plan(actions: list[dict], label: str, scanned: int | None = None, editing: bool = False) -> str:
    """Текст плана для владелицы: что бот хочет сделать в календаре. Нумерация сквозная
    (в порядке create → rename → delete), по ней владелица может ссылаться в правках."""
    tz = ZoneInfo(config.MARINATWIN_TIMEZONE)
    head = f"\U0001f4cb План для календаря, период «{label}»"
    if scanned is not None:
        head += f" (проверено задач ClickUp: {scanned})"
    head += ". Пока НИЧЕГО не опубликовано."
    if editing:
        head = "✏️ Обновила план. " + head
    lines = [head]
    n = 0
    creates = [a for a in actions if a["type"] == "create"]
    renames = [a for a in actions if a["type"] == "rename"]
    deletes = [a for a in actions if a["type"] == "delete"]
    if creates:
        lines.append(f"\n➕ Добавить в календарь ({len(creates)}):")
        for a in creates:
            n += 1
            try:
                st = datetime.fromisoformat(a["start"]).astimezone(tz)
                en = datetime.fromisoformat(a["end"]).astimezone(tz)
                when = f"{st.strftime('%d.%m %H:%M')}–{en.strftime('%H:%M')}"
            except ValueError:
                when = a["start"]
            loc = f" \U0001f4cd{a['location']}" if a.get("location") else ""
            warn = ""
            if a.get("ambiguous_count"):
                warn = f" ⚠️ рядом уже {a['ambiguous_count']} событий на это время, старые не трогаю"
            lines.append(f"{n}. «{a['title']}» — {when}{loc}{warn}")
    if renames:
        lines.append(f"\n✏️ Переименовать в календаре ({len(renames)}):")
        for a in renames:
            n += 1
            lines.append(f"{n}. «{a['old_title']}» → «{a['new_title']}» — {a.get('when', '')}")
    if deletes:
        lines.append(f"\n\U0001f5d1 Удалить точные дубли ({len(deletes)}):")
        for a in deletes:
            n += 1
            lines.append(f"{n}. «{a['title']}» — {a.get('when', '')} (лишняя копия)")
    lines.append("\nОпубликовать это в календаре?")
    return "\n".join(lines)


def _ccu_render_result(label: str, res: dict) -> str:
    lines = [f"✅ Опубликовано, период «{label}»:"]
    if res["renamed"]:
        lines.append(f"\n✏️ Переименовано ({len(res['renamed'])}):")
        for r in res["renamed"]:
            lines.append(f"«{r['old_title']}» → «{r['new_title']}» — {r['when']}")
    if res["created"]:
        lines.append(f"\n➕ Добавлено ({len(res['created'])}):")
        for c in res["created"]:
            lines.append(f"«{c['title']}» — {c['when']}")
    if res["ambiguous"]:
        lines.append(f"\n⚠️ Неоднозначно, проверь на дубли ({len(res['ambiguous'])}):")
        for a in res["ambiguous"]:
            lines.append(f"«{a['title']}» — {a['when']} (рядом уже {a['count']} событий на это время)")
    if res["deleted"]:
        total = sum(d["removed"] for d in res["deleted"])
        lines.append(f"\n\U0001f5d1 Убрала точных дублей ({total}):")
        for d in res["deleted"]:
            lines.append(f"«{d['title']}» — {d['when']} (оставила 1, удалила {d['removed']})")
    if res["errors"]:
        lines.append(f"\n❌ Ошибок при обработке: {res['errors']}")
    if not (res["renamed"] or res["created"] or res["deleted"] or res["errors"]):
        lines.append("\nНичего не пришлось менять.")
    text = "\n".join(lines)
    if len(text) > _d["message_limit"] - 250:
        text = text[: _d["message_limit"] - 300] + "\n\n...отчёт обрезан."
    return text

def _ccu_store_plan(context: ContextTypes.DEFAULT_TYPE, plan: dict) -> str:
    plans = context.application.bot_data.setdefault(PLANS_KEY, {})
    plan_id = uuid.uuid4().hex[:10]
    plans[plan_id] = plan
    while len(plans) > MAX_PLANS:
        plans.pop(next(iter(plans)))
    return plan_id

async def _ccu_send_plan(context: ContextTypes.DEFAULT_TYPE, chat_id: int, plan_id: str, editing: bool = False) -> None:
    plan = context.application.bot_data[PLANS_KEY][plan_id]
    text = _ccu_render_plan(plan["actions"], plan["label"], plan.get("scanned"), editing=editing)
    chunks = _d["split_for_telegram"](text)
    for i, chunk in enumerate(chunks):
        is_last = i == len(chunks) - 1
        await context.bot.send_message(
            chat_id=chat_id, text=chunk, reply_markup=_ccu_plan_keyboard(plan_id) if is_last else None
        )

async def period_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Кнопки периода под /calendarclickup. С 03.10.2026 (по прямой просьбе владелицы)
    НИЧЕГО не пишет в календарь сразу: только строит план (clickup_meeting_watch.
    plan_clickup_calendar_sync + plan_calendar_dedupe — оба только читают) и присылает его
    владелице в личку с кнопками "✅ Опубликовать"/"✏️ Изменить"/"❌ Отмена" (см.
    plan_callback). Если менять нечего — просто показывает список
    событий периода."""
    query = update.callback_query
    await query.answer()
    chat = update.effective_chat
    if chat is None or chat.type != "private":
        return
    if config.OWNER_USER_ID is None or query.from_user.id != config.OWNER_USER_ID:
        return
    _, _, period = (query.data or "").partition(":")
    bounds = _d["period_bounds"](period)
    if not bounds:
        return
    start, end = bounds
    label = _d["period_labels"].get(period, period)
    context.application.bot_data[AWAITING_KEY] = None
    await query.edit_message_text(f"Смотрю ClickUp и календарь за период «{label}»... Ничего не публикую, только готовлю план.")
    try:
        sync_plan = await clickup_meeting_watch.plan_clickup_calendar_sync(start, end)
    except Exception:
        logger.exception("/calendarclickup: не удалось подготовить план сверки за период %s", period)
        await query.edit_message_text(
            f"Не смогла подготовить план за период «{label}» — попробуй ещё раз чуть позже.",
            reply_markup=_d["period_keyboard"](),
        )
        return
    try:
        dedupe_plan = await clickup_meeting_watch.plan_calendar_dedupe(start, end)
    except Exception:
        logger.exception("/calendarclickup: не удалось подготовить план зачистки дублей за период %s", period)
        dedupe_plan = {"scanned": 0, "actions": [], "errors": 1}
    actions = sync_plan["actions"] + dedupe_plan["actions"]
    extra = ""
    if sync_plan["errors"] or dedupe_plan["errors"]:
        extra = f"\n\n❌ Ошибок при подготовке плана: {sync_plan['errors'] + dedupe_plan['errors']}"
    if not actions:
        try:
            events = calendar_client.list_events(start.isoformat(), end.isoformat())
            listing = _ccu_format_event_lines(label, events)
        except Exception:
            logger.exception("Не удалось получить события календаря за период %s (/calendarclickup)", period)
            listing = "Не смогла получить список календаря — попробуй ещё раз."
        await query.edit_message_text(
            f"\U0001f4c5 Сверка за период «{label}» (проверено задач: {sync_plan['scanned']}): всё совпадает, менять нечего, дублей нет.{extra}\n\n{listing}",
            reply_markup=_d["period_keyboard"](),
        )
        return
    plan_id = _ccu_store_plan(
        context, {"actions": actions, "label": label, "scanned": sync_plan["scanned"], "start": start.isoformat(), "end": end.isoformat()}
    )
    await query.edit_message_text(f"План за период «{label}» готов — смотри ниже.{extra}")
    await _ccu_send_plan(context, chat.id, plan_id)


async def plan_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Кнопки под планом /calendarclickup: "ccup:pub:<id>" — публикует план в календарь
    (clickup_meeting_watch.apply_calendar_actions — единственное место записи), "ccup:edit:<id>"
    — ждёт от владелицы текст правки (см. apply_edit, повторяется бесконечно, пока она
    не нажмёт Опубликовать или Отмена), "ccup:cancel:<id>" — отменяет команду целиком."""
    query = update.callback_query
    await query.answer()
    chat = update.effective_chat
    if chat is None or chat.type != "private":
        return
    if config.OWNER_USER_ID is None or query.from_user.id != config.OWNER_USER_ID:
        return
    _, action, plan_id = (query.data or "").split(":", 2)
    plans = context.application.bot_data.setdefault(PLANS_KEY, {})
    plan = plans.get(plan_id)
    try:
        await query.edit_message_reply_markup(reply_markup=None)
    except Exception:
        pass
    if not plan:
        await context.bot.send_message(chat_id=chat.id, text="Этот план уже не актуален — запусти /calendarclickup заново.")
        return
    if action == "cancel":
        plans.pop(plan_id, None)
        if context.application.bot_data.get(AWAITING_KEY) == plan_id:
            context.application.bot_data[AWAITING_KEY] = None
        await context.bot.send_message(chat_id=chat.id, text="Хорошо, отменила. В календаре ничего не менялось.")
        return
    if action == "edit":
        context.application.bot_data[AWAITING_KEY] = plan_id
        await context.bot.send_message(
            chat_id=chat.id,
            text=(
                "✏️ Напиши, что изменить в плане (можно по номерам: «убери 2», «в 1 время 15:00», "
                "«переименуй 3 в ...», «добавь встречу ... завтра в 12:00») — пришлю обновлённый план."
            ),
        )
        return
    if action == "pub":
        plans.pop(plan_id, None)
        if context.application.bot_data.get(AWAITING_KEY) == plan_id:
            context.application.bot_data[AWAITING_KEY] = None
        await context.bot.send_message(chat_id=chat.id, text="Публикую в календарь...")
        res = clickup_meeting_watch.apply_calendar_actions(plan["actions"])
        report = _ccu_render_result(plan["label"], res)
        try:
            events = calendar_client.list_events(plan["start"], plan["end"])
            listing = _ccu_format_event_lines(plan["label"], events)
        except Exception:
            logger.exception("Не удалось получить события календаря после публикации (/calendarclickup)")
            listing = "Не смогла получить итоговый список календаря."
        for chunk in _d["split_for_telegram"](f"{report}\n\n{listing}"):
            await context.bot.send_message(chat_id=chat.id, text=chunk)


async def apply_edit(context: ContextTypes.DEFAULT_TYPE, user, plan_id: str, text: str) -> None:
    """Владелица нажала "✏️ Изменить" под планом /calendarclickup и прислала правку —
    перехватывается в handle_message. Применяет правку (clickup_meeting_watch.
    revise_calendar_plan) и снова показывает план с теми же тремя кнопками — до
    бесконечности, пока она не нажмёт "Опубликовать" или "Отмена". Если правку не поняла —
    режим ожидания правки не снимается, можно написать ещё раз."""
    plans = context.application.bot_data.setdefault(PLANS_KEY, {})
    plan = plans.get(plan_id)
    if not plan:
        context.application.bot_data[AWAITING_KEY] = None
        await context.bot.send_message(chat_id=user.id, text="Этот план уже не актуален — запусти /calendarclickup заново.")
        return
    try:
        revised = clickup_meeting_watch.revise_calendar_plan(plan["actions"], text)
    except Exception:
        logger.exception("Ошибка при разборе правки плана /calendarclickup")
        revised = None
    if revised is None:
        await context.bot.send_message(
            chat_id=user.id,
            text="Не поняла правку — напиши ещё раз, по номерам из плана (например «убери 2» или «в 1 время 15:00»).",
        )
        return
    context.application.bot_data[AWAITING_KEY] = None
    if not revised:
        plans.pop(plan_id, None)
        await context.bot.send_message(chat_id=user.id, text="В плане ничего не осталось — публиковать нечего, команда завершена.")
        return
    plan["actions"] = revised
    await _ccu_send_plan(context, user.id, plan_id, editing=True)

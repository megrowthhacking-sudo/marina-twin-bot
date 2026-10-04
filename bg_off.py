"""Отключение фоновых задач бота и замена их командами владелицы.

Снимает с job_queue 5 фоновых задач: daily_digest_job, periodic_memory_job,
check_and_send_reminders_job, morning_plan_job, check_new_clickup_meetings_job.
Вместо утреннего плана регистрируется команда /plan, которая по запросу вызывает
schedule_reminders.morning_plan_job — только для владелицы.

apply(app) вызывается в конце bot.py::build_application.
"""
import logging

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

import config
import schedule_reminders

logger = logging.getLogger(__name__)

_DISABLED_JOB_NAMES = (
    "daily_digest_job",
    "periodic_memory_job",
    "check_and_send_reminders_job",
    "morning_plan_job",
    "check_new_clickup_meetings_job",
)


async def handle_plan_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/plan — по запросу присылает утренний план (morning_plan_job). Только владелице."""
    user = update.effective_user
    message = update.message
    if message is None:
        return
    if config.OWNER_USER_ID is None or user is None or user.id != config.OWNER_USER_ID:
        await message.reply_text("Эта команда только для владелицы.")
        return
    await schedule_reminders.morning_plan_job(context)


def apply(app: Application) -> None:
    """Снимает 5 фоновых задач с job_queue и регистрирует команду /plan."""
    job_queue = app.job_queue
    if job_queue is not None:
        for job in job_queue.jobs():
            callback_name = getattr(job.callback, "__name__", None)
            if job.name in _DISABLED_JOB_NAMES or callback_name in _DISABLED_JOB_NAMES:
                job.schedule_removal()
                logger.info("Фоновая задача %s отключена", job.name or callback_name)
    app.add_handler(CommandHandler("plan", handle_plan_command))

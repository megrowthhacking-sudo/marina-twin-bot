"""
Реестры банков Алтына (Google Sheets) — статусы по банкам по каждому менеджеру
отдельно (по прямой просьбе владелицы, часть 32: "/altynilya /altynliliana /altynlena
/altynslava /altynsveta /altynsergey").

Источник — 2 гугл-таблицы, обе расшарены "по ссылке — все могут читать" (проверено:
mcp__Google_Drive__get_file_permissions вернул role=reader/type=anyone для обеих),
поэтому читаем БЕЗ отдельного сервисного аккаунта/токена — просто публичным CSV-экспортом
конкретного листа через Google Visualization API (gviz), по имени листа, без нужды
заранее знать числовой gid:
    https://docs.google.com/spreadsheets/d/<file_id>/gviz/tq?tqx=out:csv&sheet=<имя листа>

Таблицы и листы (см. ALTYN_REGISTRY_SHEETS ниже):
  - "Р/С для А Брокер" (10xe6RsRUL3rArogufKrJtzBB5-I7YEcxUWQUE_QZd1U):
      * "Открытие РС Алтын Брокер" — это то, что владелица называет "Брокер" (банки
        Алтын Брокера, открытие расчётного счёта).
      * "Подключение банков РФ Кошелек А" — это "Кошелек Алтын" (банки под Кошелёк
        Алтын, подключение методов СБП/МИР/ОСТ и т.д.).
  - "Банки РФ в работе" (1_zvu3BsA7ElW0tFiy396cqaqyYro-MV1) — более широкая "холодная"
    база банков РФ, из неё берём 3 листа с реальными менеджерами и статусами:
      * "Банки-участники СБП и PSP"
      * "Агенты"
      * "Подключенына подключении"
    (остальные листы этой книги — "База холодных контактов"/"доп контакты"/"статистика" —
    не содержат стабильной колонки "Менеджер" с актуальными статусами по банку и не
    выгружаются.)

Менеджер в разных листах может быть записан с вариациями ("Илья" / "Илья А", "Лена" /
"Лена Ч", "Слава" / "Слава А") — сопоставление идёт по ПРЕФИКСУ значения ячейки
(без учёта регистра, см. config.ALTYN_MANAGER_COMMANDS[...]["match"]).

Данные живые (тянутся при каждом вызове команды), сеть может отвалиться — при ошибке
функция кидает исключение, вызывающий код (bot.py) сам решает, как об этом сообщить
владелице (тот же паттерн, что и у clickup_client — см. bot.py::_send_project_report).
"""

import csv
import io
import logging
import urllib.parse

import requests

import config

logger = logging.getLogger(__name__)

_GVIZ_URL = "https://docs.google.com/spreadsheets/d/{file_id}/gviz/tq?tqx=out:csv&sheet={sheet}"
_TIMEOUT_SECONDS = 20


def _fetch_sheet_rows(file_id: str, sheet_name: str) -> list[list[str]]:
    """Тянет один лист гугл-таблицы как CSV (публичный gviz-экспорт, см. модульный
    докстринг) и возвращает список строк (каждая строка — список ячеек-строк).
    Кидает requests.RequestException при сетевой ошибке или не-200 ответе."""
    url = _GVIZ_URL.format(file_id=file_id, sheet=urllib.parse.quote(sheet_name))
    response = requests.get(url, timeout=_TIMEOUT_SECONDS)
    response.raise_for_status()
    return list(csv.reader(io.StringIO(response.text)))


def _manager_matches(cell_value: str | None, match_prefixes: list[str]) -> bool:
    if not cell_value:
        return False
    normalized = cell_value.strip().lower()
    return any(normalized.startswith(prefix) for prefix in match_prefixes)


def fetch_manager_report(manager_key: str) -> list[dict]:
    """Собирает по всем настроенным листам (config.ALTYN_REGISTRY_SHEETS) строки, где
    колонка "Менеджер" соответствует этому менеджеру (config.ALTYN_MANAGER_COMMANDS).
    Возвращает список {"sheet_label": ..., "bank": ..., "status": ..., "extra": ...} —
    "extra" — доп. колонка, если задана в описании листа (метод/дата/агент, см. columns
    в config.ALTYN_REGISTRY_SHEETS), иначе None. Порядок — как в исходной таблице.
    Кидает исключение при сетевой ошибке (см. _fetch_sheet_rows) — не глотает её, чтобы
    вызывающий код в bot.py мог сообщить владелице о проблеме, а не тихо показать пустой
    отчёт."""
    manager = config.ALTYN_MANAGER_COMMANDS[manager_key]
    match_prefixes = manager["match"]
    results: list[dict] = []

    for spreadsheet in config.ALTYN_REGISTRY_SHEETS.values():
        file_id = spreadsheet["file_id"]
        for sheet in spreadsheet["sheets"]:
            rows = _fetch_sheet_rows(file_id, sheet["name"])
            columns = sheet["columns"]
            bank_idx = columns["bank"]
            manager_idx = columns["manager"]
            status_idx = columns.get("status")
            extra_idx = columns.get("extra")

            for row in rows[1:]:
                if manager_idx >= len(row):
                    continue
                if not _manager_matches(row[manager_idx], match_prefixes):
                    continue
                bank = row[bank_idx].strip() if bank_idx < len(row) else ""
                if not bank:
                    continue
                status = row[status_idx].strip() if status_idx is not None and status_idx < len(row) else ""
                extra = row[extra_idx].strip() if extra_idx is not None and extra_idx < len(row) else ""
                results.append(
                    {
                        "sheet_label": sheet["label"],
                        "bank": bank,
                        "status": status,
                        "extra": extra,
                    }
                )

    return results


def format_manager_report(manager_label: str, rows: list[dict]) -> str:
    """Форматирует результат fetch_manager_report в текст для Telegram — по разделам
    (sheet_label), внутри раздела — нумерованный список "Банк — Статус (extra)"."""
    if not rows:
        return f"🏦 Алтын — {manager_label}: банков со статусом не нашла ни в одном реестре."

    header = f"🏦 Алтын — {manager_label} ({len(rows)}):"
    sections: dict[str, list[dict]] = {}
    for row in rows:
        sections.setdefault(row["sheet_label"], []).append(row)

    parts = [header]
    for sheet_label, sheet_rows in sections.items():
        lines = [f"\n{sheet_label}:"]
        for i, row in enumerate(sheet_rows, start=1):
            line = f"{i}. {row['bank']}"
            if row["status"]:
                line += f" — {row['status']}"
            if row["extra"]:
                line += f" ({row['extra']})"
            lines.append(line)
        parts.append("\n".join(lines))

    return "\n".join(parts)

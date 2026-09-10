from __future__ import annotations

from datetime import date, datetime
from typing import Optional

from database.common import dump_dt, parse_dt
from model.report import AIModelConfig, ReportTemplate, WeeklyReport


def _parse_date(value) -> Optional[date]:
    if not value:
        return None
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    return date.fromisoformat(str(value)[:10])


def _row_template(row) -> ReportTemplate:
    return ReportTemplate(
        id=row["id"],
        name=row["name"],
        content=row["content"],
        is_default=bool(row["is_default"]),
        created_at=parse_dt(row["created_at"]),
        updated_at=parse_dt(row["updated_at"]),
    )


def _row_model(row) -> AIModelConfig:
    return AIModelConfig(
        id=row["id"],
        name=row["name"],
        provider=row["provider"] or "openai-compatible",
        api_base=row["api_base"] or "",
        model_name=row["model_name"] or "",
        encrypted_api_key=row["encrypted_api_key"] or "",
        temperature=float(row["temperature"] or 0.3),
        max_tokens=int(row["max_tokens"] or 4000),
        enabled=bool(row["enabled"]),
        created_at=parse_dt(row["created_at"]),
        updated_at=parse_dt(row["updated_at"]),
    )


def _row_report(row) -> WeeklyReport:
    return WeeklyReport(
        id=row["id"],
        title=row["title"] or "",
        start_date=_parse_date(row["start_date"]),
        end_date=_parse_date(row["end_date"]),
        template_id=row["template_id"],
        model_config_id=row["model_config_id"],
        content=row["content"] or "",
        created_at=parse_dt(row["created_at"]),
        updated_at=parse_dt(row["updated_at"]),
    )


class ReportRepository:
    def __init__(self, connection):
        self._conn = connection

    def list_templates(self) -> list[ReportTemplate]:
        rows = self._conn.execute("SELECT * FROM report_template ORDER BY is_default DESC, id").fetchall()
        return [_row_template(row) for row in rows]

    def get_template(self, template_id: int) -> Optional[ReportTemplate]:
        row = self._conn.execute("SELECT * FROM report_template WHERE id = ?", (template_id,)).fetchone()
        return _row_template(row) if row else None

    def default_template(self) -> Optional[ReportTemplate]:
        row = self._conn.execute(
            "SELECT * FROM report_template ORDER BY is_default DESC, id LIMIT 1"
        ).fetchone()
        return _row_template(row) if row else None

    def save_template(self, template: ReportTemplate) -> ReportTemplate:
        now = datetime.now()
        if template.is_default:
            self._conn.execute("UPDATE report_template SET is_default = 0")
        if template.id is None:
            cursor = self._conn.execute(
                """
                INSERT INTO report_template (name, content, is_default, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (template.name, template.content, 1 if template.is_default else 0, dump_dt(now), dump_dt(now)),
            )
            template.id = cursor.lastrowid
        else:
            self._conn.execute(
                """
                UPDATE report_template SET name = ?, content = ?, is_default = ?, updated_at = ?
                WHERE id = ?
                """,
                (template.name, template.content, 1 if template.is_default else 0, dump_dt(now), template.id),
            )
        self._conn.commit()
        saved = self.get_template(template.id)
        assert saved is not None
        return saved

    def delete_template(self, template_id: int) -> None:
        self._conn.execute("DELETE FROM report_template WHERE id = ?", (template_id,))
        self._conn.commit()

    def list_models(self) -> list[AIModelConfig]:
        rows = self._conn.execute("SELECT * FROM ai_model_config ORDER BY id").fetchall()
        return [_row_model(row) for row in rows]

    def get_model(self, model_id: int) -> Optional[AIModelConfig]:
        row = self._conn.execute("SELECT * FROM ai_model_config WHERE id = ?", (model_id,)).fetchone()
        return _row_model(row) if row else None

    def save_model(self, config: AIModelConfig) -> AIModelConfig:
        now = datetime.now()
        if config.id is None:
            cursor = self._conn.execute(
                """
                INSERT INTO ai_model_config (
                    name, provider, api_base, model_name, encrypted_api_key,
                    temperature, max_tokens, enabled, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    config.name,
                    config.provider,
                    config.api_base,
                    config.model_name,
                    config.encrypted_api_key,
                    config.temperature,
                    config.max_tokens,
                    1 if config.enabled else 0,
                    dump_dt(now),
                    dump_dt(now),
                ),
            )
            config.id = cursor.lastrowid
        else:
            self._conn.execute(
                """
                UPDATE ai_model_config SET
                    name = ?, provider = ?, api_base = ?, model_name = ?,
                    encrypted_api_key = ?, temperature = ?, max_tokens = ?,
                    enabled = ?, updated_at = ?
                WHERE id = ?
                """,
                (
                    config.name,
                    config.provider,
                    config.api_base,
                    config.model_name,
                    config.encrypted_api_key,
                    config.temperature,
                    config.max_tokens,
                    1 if config.enabled else 0,
                    dump_dt(now),
                    config.id,
                ),
            )
        self._conn.commit()
        saved = self.get_model(config.id)
        assert saved is not None
        return saved

    def delete_model(self, model_id: int) -> None:
        self._conn.execute("DELETE FROM ai_model_config WHERE id = ?", (model_id,))
        self._conn.commit()

    def list_reports(self) -> list[WeeklyReport]:
        rows = self._conn.execute("SELECT * FROM weekly_report ORDER BY created_at DESC").fetchall()
        return [_row_report(row) for row in rows]

    def get_report(self, report_id: int) -> Optional[WeeklyReport]:
        row = self._conn.execute("SELECT * FROM weekly_report WHERE id = ?", (report_id,)).fetchone()
        return _row_report(row) if row else None

    def save_report(self, report: WeeklyReport) -> WeeklyReport:
        now = datetime.now()
        start = report.start_date.isoformat() if report.start_date else None
        end = report.end_date.isoformat() if report.end_date else None
        if report.id is None:
            cursor = self._conn.execute(
                """
                INSERT INTO weekly_report (
                    title, start_date, end_date, template_id, model_config_id,
                    content, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    report.title,
                    start,
                    end,
                    report.template_id,
                    report.model_config_id,
                    report.content,
                    dump_dt(now),
                    dump_dt(now),
                ),
            )
            report.id = cursor.lastrowid
        else:
            self._conn.execute(
                """
                UPDATE weekly_report SET
                    title = ?, start_date = ?, end_date = ?, template_id = ?,
                    model_config_id = ?, content = ?, updated_at = ?
                WHERE id = ?
                """,
                (
                    report.title,
                    start,
                    end,
                    report.template_id,
                    report.model_config_id,
                    report.content,
                    dump_dt(now),
                    report.id,
                ),
            )
        self._conn.commit()
        saved = self.get_report(report.id)
        assert saved is not None
        return saved

    def delete_report(self, report_id: int) -> None:
        self._conn.execute("DELETE FROM weekly_report WHERE id = ?", (report_id,))
        self._conn.commit()

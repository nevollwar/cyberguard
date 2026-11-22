import json
import sqlite3
from datetime import datetime
from pathlib import Path

from src.core.exceptions import StorageError
from src.data.storage.sqlite_db import get_connection, init_db


def add_history_record(
    source_type: str,
    source_name: str,
    model_id: str,
    model_name: str,
    total_count: int,
    normal_count: int,
    attack_count: int,
    normal_percent: float,
    attack_percent: float,
    result_summary: dict | list | None = None,
    exported_csv_path: str | None = None,
    db_path: Path | None = None,
) -> int:
    init_db(db_path)
    created_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    summary_json = json.dumps(result_summary, ensure_ascii=False) if result_summary is not None else None

    conn = get_connection(db_path)
    try:
        with conn:
            cursor = conn.execute(
                '''
                INSERT INTO classification_history (
                    created_at, source_type, source_name, model_id, model_name,
                    total_count, normal_count, attack_count,
                    normal_percent, attack_percent,
                    result_summary_json, exported_csv_path
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''',
                (
                    created_at,
                    source_type,
                    source_name,
                    model_id,
                    model_name,
                    int(total_count),
                    int(normal_count),
                    int(attack_count),
                    float(normal_percent),
                    float(attack_percent),
                    summary_json,
                    exported_csv_path,
                ),
            )
            return int(cursor.lastrowid)
    except sqlite3.Error as exc:
        raise StorageError(f'Не удалось сохранить запись в историю: {exc}') from exc
    finally:
        conn.close()


def _row_to_dict(row: sqlite3.Row) -> dict:
    item = dict(row)
    raw_json = item.get('result_summary_json')
    if raw_json:
        try:
            item['result_summary'] = json.loads(raw_json)
        except json.JSONDecodeError:
            item['result_summary'] = None
    else:
        item['result_summary'] = None
    return item


def get_history_records(limit: int = 50, db_path: Path | None = None) -> list[dict]:
    init_db(db_path)
    conn = get_connection(db_path)
    try:
        rows = conn.execute(
            'SELECT * FROM classification_history ORDER BY id DESC LIMIT ?',
            (int(limit),),
        ).fetchall()
        return [_row_to_dict(row) for row in rows]
    except sqlite3.Error as exc:
        raise StorageError(f'Не удалось прочитать историю классификаций: {exc}') from exc
    finally:
        conn.close()


def get_history_record_by_id(record_id: int, db_path: Path | None = None) -> dict | None:
    init_db(db_path)
    conn = get_connection(db_path)
    try:
        row = conn.execute(
            'SELECT * FROM classification_history WHERE id = ?',
            (int(record_id),),
        ).fetchone()
        return _row_to_dict(row) if row is not None else None
    except sqlite3.Error as exc:
        raise StorageError(f'Не удалось получить запись истории №{record_id}: {exc}') from exc
    finally:
        conn.close()


def clear_history(db_path: Path | None = None) -> int:
    init_db(db_path)
    conn = get_connection(db_path)
    try:
        with conn:
            cursor = conn.execute('DELETE FROM classification_history')
            return int(cursor.rowcount)
    except sqlite3.Error as exc:
        raise StorageError(f'Не удалось очистить историю классификаций: {exc}') from exc
    finally:
        conn.close()
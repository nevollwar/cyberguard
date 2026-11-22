import sqlite3
from datetime import datetime
from pathlib import Path

from src.core.exceptions import StorageError
from src.data.storage.sqlite_db import get_connection, init_db


def get_setting(key: str, default: str | None = None, db_path: Path | None = None) -> str | None:
    init_db(db_path)
    conn = get_connection(db_path)
    try:
        row = conn.execute(
            'SELECT value FROM app_settings WHERE key = ?',
            (key,),
        ).fetchone()
        return str(row['value']) if row is not None else default
    except sqlite3.Error as exc:
        raise StorageError(f'Не удалось прочитать настройку "{key}": {exc}') from exc
    finally:
        conn.close()


def set_setting(key: str, value: str, db_path: Path | None = None) -> None:
    init_db(db_path)
    updated_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    conn = get_connection(db_path)
    try:
        with conn:
            conn.execute(
                '''
                INSERT INTO app_settings (key, value, updated_at)
                VALUES (?, ?, ?)
                ON CONFLICT(key) DO UPDATE SET
                    value = excluded.value,
                    updated_at = excluded.updated_at
                ''',
                (key, str(value), updated_at),
            )
    except sqlite3.Error as exc:
        raise StorageError(f'Не удалось сохранить настройку "{key}": {exc}') from exc
    finally:
        conn.close()


def get_all_settings(db_path: Path | None = None) -> dict[str, str]:
    init_db(db_path)
    conn = get_connection(db_path)
    try:
        rows = conn.execute('SELECT key, value FROM app_settings ORDER BY key').fetchall()
        return {str(row['key']): str(row['value']) for row in rows}
    except sqlite3.Error as exc:
        raise StorageError(f'Не удалось загрузить настройки приложения: {exc}') from exc
    finally:
        conn.close()


def get_active_model_id(db_path: Path | None = None) -> str | None:
    return get_setting('active_model_id', default=None, db_path=db_path)


def set_active_model_id(model_id: str, db_path: Path | None = None) -> None:
    set_setting('active_model_id', model_id, db_path=db_path)
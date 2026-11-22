import logging
from pathlib import Path
from src.core.config import load_config


def get_logger(name: str = 'cyberguard', log_file: Path | None = None, level: str | None = None) -> logging.Logger:
    logger = logging.getLogger(name)

    # Не добавляем обработчики повторно, чтобы строки в логах не дублировались
    if logger.handlers:
        return logger

    config = load_config()
    target_level = (level or config.log_level).upper()
    target_log_file = log_file or (config.logs_dir / 'cyberguard.log')
    target_log_file.parent.mkdir(parents=True, exist_ok=True)

    logger.setLevel(getattr(logging, target_level, logging.INFO))
    formatter = logging.Formatter('%(asctime)s | %(levelname)s | %(name)s | %(message)s')

    # Запись логов в файл в кодировке UTF-8
    file_handler = logging.FileHandler(target_log_file, encoding='utf-8')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # Дублирование логов в консоль для удобной отладки
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    logger.propagate = False
    return logger
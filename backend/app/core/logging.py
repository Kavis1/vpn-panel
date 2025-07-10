"""
Модуль логирования для приложения.
"""
import logging
import sys
from pathlib import Path

# Создаем логгер
logger = logging.getLogger("vpn-panel")

# Настраиваем уровень логирования
logger.setLevel(logging.INFO)

# Создаем обработчик для вывода в консоль
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.INFO)

# Создаем форматтер
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
console_handler.setFormatter(formatter)

# Добавляем обработчик к логгеру
if not logger.handlers:
    logger.addHandler(console_handler)

# Экспортируем логгер
__all__ = ['logger']
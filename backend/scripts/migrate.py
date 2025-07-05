#!/usr/bin/env python3
"""
Скрипт для управления миграциями базы данных.
Использование:
    python -m scripts.migrate [команда] [аргументы]

Доступные команды:
    init      - Инициализировать миграции
    revision  - Создать новую миграцию
    upgrade   - Применить миграции
    downgrade - Откатить миграции
    current   - Показать текущую ревизию
    history   - Показать историю миграций
    heads     - Показать хеды веток
"""
import os
import sys
import subprocess
from pathlib import Path

# Путь к корневой директории проекта
BASE_DIR = Path(__file__).parent.parent

# Путь к директории с миграциями
MIGRATIONS_DIR = BASE_DIR / "app" / "db" / "migrations"


def run_alembic_command(*args):
    """Запускает команду alembic с указанными аргументами."""
    # Устанавливаем переменные окружения
    env = os.environ.copy()
    env["PYTHONPATH"] = str(BASE_DIR)
    
    # Формируем команду
    cmd = [sys.executable, "-m", "alembic"] + list(args)
    
    # Запускаем команду
    result = subprocess.run(cmd, cwd=str(BASE_DIR), env=env)
    return result.returncode


def init_migrations():
    """Инициализирует директорию для миграций."""
    if MIGRATIONS_DIR.exists():
        print(f"Директория миграций уже существует: {MIGRATIONS_DIR}")
        return 1
    
    print(f"Инициализация миграций в {MIGRATIONS_DIR}...")
    return run_alembic_command("init", "app/db/migrations")


def create_revision(message=None):
    """Создает новую миграцию."""
    if not MIGRATIONS_DIR.exists():
        print("Ошибка: директория миграций не найдена. Сначала выполните инициализацию.")
        return 1
    
    args = ["revision", "--autogenerate"]
    if message:
        args.extend(["-m", message])
    
    return run_alembic_command(*args)


def upgrade(revision="head"):
    """Применяет миграции."""
    if not MIGRATIONS_DIR.exists():
        print("Ошибка: директория миграций не найдена. Сначала выполните инициализацию.")
        return 1
    
    return run_alembic_command("upgrade", revision)


def downgrade(revision):
    """Откатывает миграции."""
    if not MIGRATIONS_DIR.exists():
        print("Ошибка: директория миграций не найдена. Сначала выполните инициализацию.")
        return 1
    
    return run_alembic_command("downgrade", revision)


def show_current():
    """Показывает текущую ревизию."""
    if not MIGRATIONS_DIR.exists():
        print("Ошибка: директория миграций не найдена. Сначала выполните инициализацию.")
        return 1
    
    return run_alembic_command("current")


def show_history():
    """Показывает историю миграций."""
    if not MIGRATIONS_DIR.exists():
        print("Ошибка: директория миграций не найдена. Сначала выполните инициализацию.")
        return 1
    
    return run_alembic_command("history")


def show_heads():
    """Показывает хеды веток."""
    if not MIGRATIONS_DIR.exists():
        print("Ошибка: директория миграций не найдена. Сначала выполните инициализацию.")
        return 1
    
    return run_alembic_command("heads")


def main():
    """Основная функция."""
    if len(sys.argv) < 2:
        print(__doc__)
        return 1
    
    command = sys.argv[1].lower()
    args = sys.argv[2:]
    
    if command == "init":
        return init_migrations()
    elif command == "revision":
        message = args[0] if args else None
        return create_revision(message)
    elif command == "upgrade":
        revision = args[0] if args else "head"
        return upgrade(revision)
    elif command == "downgrade":
        if not args:
            print("Укажите ревизию для отката (например, -1 для отката последней миграции)")
            return 1
        return downgrade(args[0])
    elif command == "current":
        return show_current()
    elif command == "history":
        return show_history()
    elif command == "heads":
        return show_heads()
    else:
        print(f"Неизвестная команда: {command}")
        print(__doc__)
        return 1


if __name__ == "__main__":
    sys.exit(main())

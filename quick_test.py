#!/usr/bin/env python3
"""
Быстрый тест для проверки основных проблем в VPN Panel.
"""
import sys
import os
from pathlib import Path

# Добавляем backend в путь
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

def test_imports():
    """Тестирует основные импорты."""
    print("🔍 Проверка импортов...")
    
    try:
        # Тест базовых импортов
        from app.main import app
        print("✅ Основное приложение импортируется")
        
        from app import schemas, models, crud
        print("✅ Схемы, модели и CRUD импортируются")
        
        from app.api.deps import get_db, get_current_user
        print("✅ Зависимости API импортируются")
        
        return True
    except Exception as e:
        print(f"❌ Ошибка импорта: {e}")
        return False

def test_pydantic_warnings():
    """Проверяет предупреждения Pydantic."""
    print("\n🔍 Проверка совместимости Pydantic...")
    
    issues = []
    
    # Проверяем использование orm_mode
    schema_files = list(Path("backend/app/schemas").glob("*.py"))
    for file in schema_files:
        content = file.read_text(encoding='utf-8')
        if 'orm_mode = True' in content:
            issues.append(f"❌ {file.name}: использует устаревший 'orm_mode'")
    
    if issues:
        print("Найдены проблемы совместимости:")
        for issue in issues:
            print(f"  {issue}")
        return False
    else:
        print("✅ Проблем совместимости не найдено")
        return True

def test_hardcoded_credentials():
    """Проверяет hardcoded credentials."""
    print("\n🔍 Проверка hardcoded credentials...")
    
    issues = []
    
    # Проверяем .env файлы
    env_files = [
        Path("backend/.env"),
        Path(".env.example")
    ]
    
    for env_file in env_files:
        if env_file.exists():
            content = env_file.read_text()
            if 'admin' in content.lower() and 'password' in content.lower():
                issues.append(f"❌ {env_file}: содержит тестовые credentials")
    
    if issues:
        print("Найдены проблемы безопасности:")
        for issue in issues:
            print(f"  {issue}")
        return False
    else:
        print("✅ Hardcoded credentials не найдены")
        return True

def test_absolute_paths():
    """Проверяет абсолютные пути."""
    print("\n🔍 Проверка абсолютных путей...")
    
    issues = []
    
    # Проверяем Python файлы
    py_files = list(Path("backend").rglob("*.py"))
    for file in py_files:
        try:
            content = file.read_text(encoding='utf-8')
            if '/var/log' in content or '/usr/local' in content:
                issues.append(f"❌ {file.relative_to(Path('backend'))}: содержит абсолютные пути")
        except:
            continue
    
    if issues:
        print("Найдены абсолютные пути:")
        for issue in issues:
            print(f"  {issue}")
        return False
    else:
        print("✅ Абсолютные пути исправлены")
        return True

def main():
    """Основная функция тестирования."""
    print("🚀 Быстрая проверка VPN Panel")
    print("=" * 50)
    
    tests = [
        test_imports,
        test_pydantic_warnings,
        test_hardcoded_credentials,
        test_absolute_paths
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print("\n" + "=" * 50)
    print(f"📊 Результат: {passed}/{total} тестов прошли")
    
    if passed == total:
        print("🎉 Все проверки пройдены!")
        return True
    else:
        print("⚠️  Найдены проблемы, требующие исправления")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
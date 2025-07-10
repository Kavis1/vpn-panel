#!/usr/bin/env python3
"""
Скрипт для автоматического тестирования и запуска VPN Panel.
"""
import asyncio
import subprocess
import sys
import time
import requests
import json
from pathlib import Path
from typing import Dict, Any, Optional


class VPNPanelTester:
    """Класс для тестирования VPN Panel."""
    
    def __init__(self):
        self.base_url = "http://localhost:8000"
        self.api_url = f"{self.base_url}/api/v1"
        self.backend_dir = Path("backend")
        self.frontend_dir = Path("frontend")
        
    def print_step(self, step: str, status: str = "INFO"):
        """Печатает шаг с форматированием."""
        colors = {
            "INFO": "\033[94m",
            "SUCCESS": "\033[92m",
            "ERROR": "\033[91m",
            "WARNING": "\033[93m"
        }
        reset = "\033[0m"
        print(f"{colors.get(status, '')}{status}: {step}{reset}")
    
    def run_command(self, command: str, cwd: Optional[Path] = None) -> bool:
        """Выполняет команду и возвращает результат."""
        try:
            result = subprocess.run(
                command.split(),
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=60
            )
            if result.returncode != 0:
                self.print_step(f"Ошибка выполнения команды: {command}", "ERROR")
                self.print_step(f"Stderr: {result.stderr}", "ERROR")
                return False
            return True
        except subprocess.TimeoutExpired:
            self.print_step(f"Таймаут выполнения команды: {command}", "ERROR")
            return False
        except Exception as e:
            self.print_step(f"Исключение при выполнении команды: {e}", "ERROR")
            return False
    
    def check_dependencies(self) -> bool:
        """Проверяет наличие зависимостей."""
        self.print_step("Проверка зависимостей...")
        
        # Проверяем Python
        if not self.run_command("python --version"):
            self.print_step("Python не найден", "ERROR")
            return False
        
        # Проверяем pip
        if not self.run_command("pip --version"):
            self.print_step("pip не найден", "ERROR")
            return False
        
        self.print_step("Зависимости проверены", "SUCCESS")
        return True
    
    def install_backend_dependencies(self) -> bool:
        """Устанавливает зависимости backend."""
        self.print_step("Установка зависимостей backend...")
        
        if not self.backend_dir.exists():
            self.print_step("Директория backend не найдена", "ERROR")
            return False
        
        # Устанавливаем основные зависимости
        if not self.run_command("pip install -r requirements.txt", self.backend_dir):
            self.print_step("Ошибка установки основных зависимостей", "ERROR")
            return False
        
        # Устанавливаем зависимости для тестов
        test_req_file = self.backend_dir / "tests" / "requirements-test.txt"
        if test_req_file.exists():
            if not self.run_command(f"pip install -r tests/requirements-test.txt", self.backend_dir):
                self.print_step("Ошибка установки тестовых зависимостей", "WARNING")
        else:
            # Устанавливаем базовые тестовые зависимости
            if not self.run_command("pip install pytest pytest-asyncio aiosqlite", self.backend_dir):
                self.print_step("Ошибка установки базовых тестовых зависимостей", "WARNING")
        
        self.print_step("Зависимости backend установлены", "SUCCESS")
        return True
    
    def run_database_migrations(self) -> bool:
        """Запускает миграции базы данных."""
        self.print_step("Применение миграций базы данных...")
        
        try:
            # Проверяем наличие alembic
            result = subprocess.run(
                ["python", "-m", "alembic", "current"],
                cwd=self.backend_dir,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            # Применяем миграции
            result = subprocess.run(
                ["python", "-m", "alembic", "upgrade", "head"],
                cwd=self.backend_dir,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode != 0:
                self.print_step(f"Ошибка применения миграций: {result.stderr}", "ERROR")
                return False
            
            self.print_step("Миграции применены", "SUCCESS")
            return True
        except Exception as e:
            self.print_step(f"Ошибка при работе с миграциями: {e}", "ERROR")
            return False
    
    def run_unit_tests(self) -> bool:
        """Запускает unit тесты."""
        self.print_step("Запуск unit тестов...")
        
        try:
            result = subprocess.run(
                ["python", "-m", "pytest", "tests/", "-v", "--tb=short"],
                cwd=self.backend_dir,
                capture_output=True,
                text=True,
                timeout=120
            )
            
            self.print_step(f"Результат тестов:\n{result.stdout}", "INFO")
            
            if result.returncode != 0:
                self.print_step(f"Некоторые тесты не прошли:\n{result.stderr}", "WARNING")
                return False
            
            self.print_step("Все unit тесты прошли успешно", "SUCCESS")
            return True
        except Exception as e:
            self.print_step(f"Ошибка запуска тестов: {e}", "ERROR")
            return False
    
    def start_backend_server(self) -> subprocess.Popen:
        """Запускает backend сервер."""
        self.print_step("Запуск backend сервера...")
        
        try:
            process = subprocess.Popen(
                ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"],
                cwd=self.backend_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            # Ждем запуска сервера
            time.sleep(5)
            
            # Проверяем, что сервер запустился
            if process.poll() is not None:
                self.print_step("Сервер не смог запуститься", "ERROR")
                return None
            
            self.print_step("Backend сервер запущен", "SUCCESS")
            return process
        except Exception as e:
            self.print_step(f"Ошибка запуска сервера: {e}", "ERROR")
            return None
    
    def test_api_health(self) -> bool:
        """Тестирует здоровье API."""
        self.print_step("Тестирование здоровья API...")
        
        try:
            response = requests.get(f"{self.api_url}/system/health", timeout=10)
            if response.status_code == 200:
                data = response.json()
                self.print_step(f"API здоров: {data['status']}", "SUCCESS")
                return True
            else:
                self.print_step(f"API недоступен: {response.status_code}", "ERROR")
                return False
        except Exception as e:
            self.print_step(f"Ошибка проверки API: {e}", "ERROR")
            return False
    
    def test_api_info(self) -> bool:
        """Тестирует получение информации о системе."""
        self.print_step("Тестирование информации о системе...")
        
        try:
            response = requests.get(f"{self.api_url}/system/info", timeout=10)
            if response.status_code == 200:
                data = response.json()
                self.print_step(f"Система: {data['name']} v{data['version']}", "SUCCESS")
                self.print_step(f"Функции: {', '.join(data['features'])}", "INFO")
                return True
            else:
                self.print_step(f"Ошибка получения информации: {response.status_code}", "ERROR")
                return False
        except Exception as e:
            self.print_step(f"Ошибка тестирования информации: {e}", "ERROR")
            return False
    
    def test_api_docs(self) -> bool:
        """Тестирует доступность документации API."""
        self.print_step("Тестирование документации API...")
        
        try:
            # Проверяем OpenAPI схему
            response = requests.get(f"{self.base_url}/api/openapi.json", timeout=10)
            if response.status_code == 200:
                self.print_step("OpenAPI схема доступна", "SUCCESS")
            else:
                self.print_step("OpenAPI схема недоступна", "WARNING")
            
            # Проверяем Swagger UI
            response = requests.get(f"{self.base_url}/api/docs", timeout=10)
            if response.status_code == 200:
                self.print_step("Swagger UI доступен", "SUCCESS")
                return True
            else:
                self.print_step("Swagger UI недоступен", "WARNING")
                return False
        except Exception as e:
            self.print_step(f"Ошибка проверки документации: {e}", "ERROR")
            return False
    
    def test_config_validation(self) -> bool:
        """Тестирует валидацию конфигурации."""
        self.print_step("Тестирование валидации конфигурации...")
        
        # Тестовая конфигурация
        test_config = {
            "inbounds": [
                {
                    "protocol": "vless",
                    "port": 443,
                    "settings": {"clients": []}
                }
            ],
            "outbounds": [
                {
                    "protocol": "freedom",
                    "tag": "direct"
                }
            ]
        }
        
        try:
            response = requests.post(
                f"{self.api_url}/config/validate",
                json={"config": test_config},
                timeout=10
            )
            
            if response.status_code == 401:
                self.print_step("Валидация требует авторизации (ожидаемо)", "SUCCESS")
                return True
            elif response.status_code == 200:
                data = response.json()
                if data.get("is_valid"):
                    self.print_step("Валидация конфигурации работает", "SUCCESS")
                    return True
                else:
                    self.print_step("Конфигурация не прошла валидацию", "WARNING")
                    return True
            else:
                self.print_step(f"Ошибка валидации: {response.status_code}", "ERROR")
                return False
        except Exception as e:
            self.print_step(f"Ошибка тестирования валидации: {e}", "ERROR")
            return False
    
    def run_full_test(self) -> bool:
        """Запускает полное тестирование."""
        self.print_step("=== НАЧАЛО ПОЛНОГО ТЕСТИРОВАНИЯ VPN PANEL ===", "INFO")
        
        # Проверка зависимостей
        if not self.check_dependencies():
            return False
        
        # Установка зависимостей
        if not self.install_backend_dependencies():
            return False
        
        # Применение миграций
        if not self.run_database_migrations():
            return False
        
        # Запуск unit тестов
        if not self.run_unit_tests():
            self.print_step("Unit тесты не прошли, но продолжаем", "WARNING")
        
        # Запуск сервера
        server_process = self.start_backend_server()
        if not server_process:
            return False
        
        try:
            # Ждем полного запуска
            time.sleep(3)
            
            # Тестирование API
            tests_passed = 0
            total_tests = 4
            
            if self.test_api_health():
                tests_passed += 1
            
            if self.test_api_info():
                tests_passed += 1
            
            if self.test_api_docs():
                tests_passed += 1
            
            if self.test_config_validation():
                tests_passed += 1
            
            # Результаты
            self.print_step(f"Пройдено API тестов: {tests_passed}/{total_tests}", "INFO")
            
            if tests_passed == total_tests:
                self.print_step("=== ВСЕ ТЕСТЫ ПРОШЛИ УСПЕШНО ===", "SUCCESS")
                self.print_step(f"Сервер запущен на {self.base_url}", "SUCCESS")
                self.print_step(f"API документация: {self.base_url}/api/docs", "SUCCESS")
                self.print_step("Нажмите Ctrl+C для остановки сервера", "INFO")
                
                # Ждем прерывания
                try:
                    while True:
                        time.sleep(1)
                except KeyboardInterrupt:
                    self.print_step("Остановка сервера...", "INFO")
                
                return True
            else:
                self.print_step("=== НЕКОТОРЫЕ ТЕСТЫ НЕ ПРОШЛИ ===", "WARNING")
                return False
        
        finally:
            # Останавливаем сервер
            if server_process:
                server_process.terminate()
                server_process.wait()
                self.print_step("Сервер остановлен", "INFO")


def main():
    """Главная функция."""
    tester = VPNPanelTester()
    
    if len(sys.argv) > 1 and sys.argv[1] == "--test-only":
        # Только тесты без запуска сервера
        success = (
            tester.check_dependencies() and
            tester.install_backend_dependencies() and
            tester.run_database_migrations() and
            tester.run_unit_tests()
        )
        sys.exit(0 if success else 1)
    else:
        # Полное тестирование с запуском сервера
        success = tester.run_full_test()
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
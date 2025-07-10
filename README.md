# VPN Panel Management System

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.95.0-009688.svg?logo=fastapi)](https://fastapi.tiangolo.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-13+-4169E1?logo=postgresql&logoColor=white)](https://www.postgresql.org/)

Универсальная панель управления VPN-сервисами, объединяющая лучшие функции из Hiddify-Manager, Marzban, Remnawave и Marzban-node.

## 🚀 Быстрая установка

### Рекомендуемый способ: Установка через Docker (все в одном)

```bash
# Установка VPN Panel (включая автоматическую установку Docker)
curl -s https://raw.githubusercontent.com/Kavis1/vpn-panel/main/deploy/install_docker.sh | sudo bash
```

### Альтернативные способы установки

#### Установка Master-сервера (вручную)
```bash
bash <(curl -s https://raw.githubusercontent.com/Kavis1/vpn-panel/main/deploy/install_master.sh)
```

#### Установка Node-сервера (VPN нода)
```bash
bash <(curl -s https://raw.githubusercontent.com/Kavis1/vpn-panel/main/deploy/install_node.sh)
```

После установки панель будет доступна по IP-адресу сервера на порту 8000.

### Подробная документация по установке

См. [DOCKER-INSTALL.md](DOCKER-INSTALL.md) для подробной инструкции по установке через Docker.

---

## 🚀 Возможности

- **Управление пользователями**
  - Регистрация и аутентификация пользователей
  - Ролевая модель доступа (администраторы, модераторы, пользователи)
  - Двухфакторная аутентификация (2FA)
  - HWID-лимиты устройств (Remnawave)

- **Поддержка протоколов**
  - VLESS с XTLS (включая XTLS-SDK)
  - Shadowsocks
  - Trojan
  - Vmess
  - WebSocket + TLS

- **Управление нодами**
  - Мульти-нодовая архитектура
  - Автоматическая синхронизация конфигурации
  - Мониторинг состояния нод
  - Балансировка нагрузки

- **Безопасность**
  - Шифрование трафика
  - Ограничение доступа по IP
  - Защита от DDoS
  - Детальное логирование

- **Аналитика и мониторинг**
  - Статистика по трафику
  - Графики использования
  - Уведомления о событиях
  - Экспорт данных

- **API**
  - Полноценный REST API
  - WebSocket для реального времени
  - Документация Swagger/OpenAPI

## 🛠 Технологический стек

### Бэкенд
- **Язык**: Python 3.10+
- **Фреймворк**: FastAPI
- **Асинхронность**: asyncio
- **База данных**: PostgreSQL / SQLite
- **ORM**: SQLAlchemy 2.0 (асинхронный режим)
- **Аутентификация**: JWT, OAuth2
- **Фоновая обработка**: Celery + Redis

### Фронтенд (в разработке)
- **Фреймворк**: React.js / Vue.js
- **UI-библиотеки**: Ant Design / Material-UI
- **Состояние**: Redux / Vuex
- **Графика**: Chart.js / D3.js

### Инфраструктура
- **VPN**: Xray-core
- **Контейнеризация**: Docker, Docker Compose
- **CI/CD**: GitHub Actions
- **Мониторинг**: Prometheus, Grafana
- **Логирование**: ELK Stack (Elasticsearch, Logstash, Kibana)

## 🚀 Быстрый старт

### Требования

- Python 3.10 или новее
- PostgreSQL 13+ или SQLite 3.35+
- Xray-core последней версии
- Node.js 16+ (для фронтенда)

### Установка (разработка)

1. **Клонирование репозитория**
   ```bash
   git clone https://github.com/your-username/vpn-panel.git
   cd vpn-panel
   ```

2. **Настройка виртуального окружения**
   ```bash
   # Создание виртуального окружения
   python -m venv venv
   
   # Активация (Linux/macOS)
   source venv/bin/activate
   
   # Активация (Windows)
   .\venv\Scripts\activate
   ```

3. **Установка зависимостей**
   ```bash
   # Установка зависимостей
   pip install -r requirements.txt
   
   # Установка зависимостей для разработки
   pip install -r requirements-dev.txt
   ```

4. **Настройка переменных окружения**
   ```bash
   # Копирование примера конфигурации
   cp .env.example .env
   
   # Редактирование конфигурации
   nano .env
   ```

5. **Инициализация базы данных**
   ```bash
   # Применение миграций
   alembic upgrade head
   
   # Создание суперпользователя
   python -m app.scripts.create_admin
   ```

6. **Запуск сервера разработки**
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

7. **Доступ к API документации**
   - Swagger UI: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc

### Развертывание (продакшн)

Для развертывания в продакшн среде используйте скрипты из директории `deploy/`:

1. **Мастер-сервер**
   ```bash
   ./deploy/install_master.sh
   ```

2. **Нода**
   ```bash
   ./deploy/install_node.sh
   ```

## 📚 Документация

Полная документация доступна в директории [docs/](docs/):

- [Главная страница](docs/index.md)
- [Установка](docs/installation/README.md)
- [Настройка](docs/configuration/README.md)
- [Руководство администратора](docs/admin/README.md)
- [Руководство пользователя](docs/user/README.md)
- [API документация](docs/api/README.md)
- [Разработка](docs/development/README.md)

## 🤝 Участие в проекте

Вклады приветствуются! Пожалуйста, прочитайте [CONTRIBUTING.md](CONTRIBUTING.md) для получения подробной информации о процессе отправки pull request'ов.

## 📄 Лицензия

Этот проект распространяется под лицензией MIT. См. [LICENSE](LICENSE) для получения дополнительной информации.

## ✨ Благодарности

- Команде Xray-core за отличный VPN-сервер
- Разработчикам FastAPI за потрясающий фреймворк
- Сообществам Hiddify, Marzban и Remnawave за вдохновение

5. Запустите приложение:
   ```bash
   uvicorn app.main:app --reload
   ```

## Лицензия

MIT

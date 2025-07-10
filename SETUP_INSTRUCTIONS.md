# 🚀 Инструкции по установке и запуску VPN Panel

## ⚠️ Требования

### 1. Установка Python
**Python не обнаружен в системе!** Необходимо установить Python 3.10+

#### Windows:
1. Скачайте Python с официального сайта: https://www.python.org/downloads/
2. При установке **обязательно** отметьте "Add Python to PATH"
3. Перезапустите командную строку

#### Проверка установки:
```bash
python --version
pip --version
```

### 2. Установка Node.js (для frontend)
1. Скачайте Node.js: https://nodejs.org/
2. Установите LTS версию
3. Проверьте: `node --version` и `npm --version`

---

## 🔧 Установка зависимостей

### Backend:
```bash
cd backend
pip install -r requirements.txt
```

### Frontend:
```bash
cd frontend
npm install
```

---

## 💾 Настройка базы данных

### 1. Создание .env файла:
```bash
cd backend
cp .env.example .env
```

### 2. Применение миграций:
```bash
cd backend
python -m alembic upgrade head
```

---

## 🧪 Запуск тестов

```bash
cd backend
pip install -r tests/requirements-test.txt
python -m pytest tests/ -v
```

---

## 🚀 Запуск проекта

### Автоматический запуск (после установки Python):
```bash
python test_and_run.py
```

### Ручной запуск:

#### Backend:
```bash
cd backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

#### Frontend (в отдельном терминале):
```bash
cd frontend
npm start
```

---

## 🌐 Доступ к приложению

- **Frontend:** http://localhost:3000
- **Backend API:** http://localhost:8000
- **API Документация:** http://localhost:8000/api/docs
- **OpenAPI Schema:** http://localhost:8000/api/openapi.json

---

## 🔍 Проверка работоспособности

### 1. Проверка API:
```bash
curl http://localhost:8000/api/v1/system/health
```

### 2. Проверка информации о системе:
```bash
curl http://localhost:8000/api/v1/system/info
```

### 3. Проверка документации:
Откройте в браузере: http://localhost:8000/api/docs

---

## 📊 Структура проекта

```
vpn-panel/
├── backend/                 # FastAPI backend
│   ├── app/
│   │   ├── api/            # API endpoints
│   │   ├── models/         # SQLAlchemy модели
│   │   ├── schemas/        # Pydantic схемы
│   │   ├── services/       # Бизнес-логика
│   │   └── crud/           # CRUD операции
│   ├── tests/              # Тесты
│   └── requirements.txt    # Зависимости Python
├── frontend/               # React frontend
│   ├── src/
│   │   ├── components/     # React компоненты
│   │   ├── services/       # API сервисы
│   │   └── types/          # TypeScript типы
│   └── package.json        # Зависимости Node.js
└── test_and_run.py        # Автоматический тестер
```

---

## 🛠️ Устранение проблем

### Проблема: "python не найден"
**Решение:** Установите Python и добавьте в PATH

### Проблема: Конфликт зависимостей
**Решение:** Обновлены requirements.txt, используйте виртуальное окружение:
```bash
python -m venv venv
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate
pip install -r requirements.txt
```

### Проблема: Ошибка миграций
**Решение:** Убедитесь, что база данных доступна и .env настроен

### Проблема: Порт занят
**Решение:** Измените порт в команде запуска:
```bash
python -m uvicorn app.main:app --port 8001
```

---

## 📋 Чек-лист запуска

- [ ] Python 3.10+ установлен
- [ ] Node.js установлен
- [ ] Зависимости backend установлены
- [ ] Зависимости frontend установлены
- [ ] .env файл создан
- [ ] Миграции применены
- [ ] Тесты проходят
- [ ] Backend запущен на :8000
- [ ] Frontend запущен на :3000
- [ ] API документация доступна

---

## 🎯 После успешного запуска

1. **Откройте API документацию:** http://localhost:8000/api/docs
2. **Проверьте здоровье системы:** GET /api/v1/system/health
3. **Изучите доступные endpoints**
4. **Протестируйте функциональность**

---

**🎉 Проект готов к использованию!**
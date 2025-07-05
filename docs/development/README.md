# Руководство разработчика

В этом разделе описаны инструкции для разработчиков, желающих внести свой вклад в проект.

## Начало работы

1. **Клонирование репозитория**
   ```bash
   git clone https://github.com/Kavis1/vpn-panel.git
   cd vpn-panel
   ```

2. **Настройка окружения**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/macOS
   .\venv\Scripts\activate  # Windows
   pip install -r requirements-dev.txt
   ```

3. **Настройка переменных окружения**
   ```bash
   cp .env.example .env
   # Отредактируйте .env по необходимости
   ```

4. **Запуск миграций**
   ```bash
   alembic upgrade head
   ```

## Структура проекта

```
vpn-panel/
├── backend/               # Backend приложение
│   ├── app/              # Основной код приложения
│   ├── tests/            # Тесты
│   └── alembic/          # Миграции базы данных
├── frontend/             # Frontend приложение
├── deploy/               # Скрипты развертывания
└── docs/                 # Документация
```

## Стиль кода

- **Python**: PEP 8, максимальная длина строки 120 символов
- **JavaScript/TypeScript**: ESLint + Prettier
- **Коммиты**: Conventional Commits
- **Документация**: Google Style Docstrings

## Процесс разработки

1. Создайте новую ветку от `main`:
   ```bash
   git checkout -b feature/feature-name
   ```

2. Внесите изменения и протестируйте их

3. Запустите тесты:
   ```bash
   pytest
   ```

4. Создайте коммит:
   ```bash
   git add .
   git commit -m "feat: добавить новую функциональность"
   ```

5. Отправьте изменения и создайте Pull Request

## Тестирование

- Модульные тесты: `pytest tests/unit`
- Интеграционные тесты: `pytest tests/integration`
- Все тесты: `pytest`

## Внесение изменений

1. Обсудите предлагаемые изменения в issue
2. Создайте ветку для своей работы
3. Напишите тесты для новых функций
4. Обновите документацию
5. Отправьте Pull Request

## Требования к коду

- Код должен быть покрыт тестами
- Документируйте публичные API
- Следуйте принципам SOLID
- Избегайте дублирования кода

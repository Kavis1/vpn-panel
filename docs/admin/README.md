# Руководство администратора

В этом разделе описаны функции администрирования VPN Panel.

## Основные возможности

- [Управление пользователями](./users.md)
- [Управление нодами](./nodes.md)
- [Мониторинг системы](./monitoring.md)
- [Резервное копирование и восстановление](./backup.md)
- [Настройки системы](./settings.md)

## Первые шаги

1. **Настройка системы**
   - Проверьте настройки в файле `.env`
   - Убедитесь, что все сервисы запущены

2. **Создание администратора**
   ```bash
   python manage.py create_admin --username admin --email admin@example.com --password ваш_пароль
   ```

3. **Добавление нод**
   - Перейдите в раздел Nodes
   - Нажмите "Добавить ноду"
   - Заполните информацию о ноде

## Безопасность

- Регулярно обновляйте систему
- Используйте сложные пароли
- Включите двухфакторную аутентификацию
- Ограничьте доступ к панели управления по IP

## Мониторинг

Используйте встроенные инструменты мониторинга для отслеживания:
- Нагрузки на сервер
- Использования трафика
- Статуса нод
- Активных подключений

## Устранение неполадок

- Проверьте логи в `logs/`
- Убедитесь, что все сервисы запущены
- Проверьте подключение к базе данных
- Проверьте настройки брандмауэра

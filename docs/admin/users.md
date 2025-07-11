# Users

## Создание пользователя

### Через веб-интерфейс:
1. Перейдите в раздел "Пользователи"
2. Нажмите кнопку "Добавить пользователя"
3. Заполните обязательные поля:
   - Имя пользователя
   - Email
   - Пароль (или сгенерируйте автоматически)
   - Роль (пользователь, модератор, администратор)
   - Лимит устройств (HWID)
   - Лимит трафика (ГБ)
4. Нажмите "Сохранить"

### Через API:
```http
POST /api/v1/users/
Content-Type: application/json
Authorization: Bearer <ваш_токен>

{
  "username": "newuser",
  "email": "user@example.com",
  "password": "securepassword123",
  "role": "user",
  "device_limit": 5,
  "data_limit": 100
}
```

## Редактирование пользователя

### Через веб-интерфейс:
1. Найдите пользователя в списке
2. Нажмите на иконку редактирования
3. Внесите необходимые изменения
4. Нажмите "Сохранить"

### Через API:
```http
PUT /api/v1/users/{user_id}
Content-Type: application/json
Authorization: Bearer <ваш_токен>

{
  "device_limit": 10,
  "data_limit": 200,
  "status": "active"
}
```

## Блокировка/разблокировка пользователя

### Через веб-интерфейс:
1. Найдите пользователя в списке
2. Переключите переключатель "Статус"
3. Подтвердите действие

### Через API:
```http
PATCH /api/v1/users/{user_id}/status
Content-Type: application/json
Authorization: Bearer <ваш_токен>

{
  "status": "banned"
}
```

## Сброс пароля

### Через веб-интерфейс:
1. Найдите пользователя в списке
2. Нажмите "Сбросить пароль"
3. Введите новый пароль или сгенерируйте автоматически
4. Нажмите "Подтвердить"

### Через API:
```http
POST /api/v1/users/{user_id}/reset-password
Content-Type: application/json
Authorization: Bearer <ваш_токен>

{
  "new_password": "newsecurepassword123"
}
```

## Просмотр статистики пользователя

### Через веб-интерфейс:
1. Перейдите в профиль пользователя
2. Откройте вкладку "Статистика"
3. Выберите период для отображения данных

### Через API:
```http
GET /api/v1/users/{user_id}/stats?period=30d
Authorization: Bearer <ваш_токен>
```

## Управление устройствами пользователя

### Просмотр списка устройств:
```http
GET /api/v1/users/{user_id}/devices
Authorization: Bearer <ваш_токен>
```

### Удаление устройства:
```http
DELETE /api/v1/users/{user_id}/devices/{device_id}
Authorization: Bearer <ваш_токен>
```

## Роли и права доступа

- **Администратор**: Полный доступ ко всем функциям системы
- **Модератор**: Управление пользователями, просмотр статистики
- **Пользователь**: Доступ только к своему профилю и настройкам

## Частые вопросы

**Q: Как сбросить пароль пользователя, если он забыл старый?**
A: Администратор может сбросить пароль через интерфейс управления пользователями.

**Q: Как ограничить количество устройств для пользователя?**
A: В настройках пользователя укажите нужное значение в поле "Лимит устройств (HWID)".

**Q: Как посмотреть историю активности пользователя?**
A: В профиле пользователя перейдите во вкладку "История активности".

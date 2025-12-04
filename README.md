# Set Game Server

Серверная реализация карточной игры "Сет" (Set) на Python (FastAPI), полностью соответствующая протоколу [com.krushiler.set-game-server](https://github.com/Krushiler/com.krushiler.set-game-server).

## Функционал

Сервер реализует REST API для:
1. **Регистрации игроков** (nickname + password → accessToken)
2. **Управления игровыми комнатами** (создание, просмотр списка, вход в игру)
3. **Просмотра игрового поля** (список карт на столе)
4. **Взятия сета** (проверка 3-х карт по правилам Set, начисление/снятие очков)
5. **Добавления карт** (добавить 3 карты на стол)
6. **Просмотра рейтинга** (очки всех игроков в текущей игре)

## Установка и запуск

### Требования
- Python 3.8+
- FastAPI
- Uvicorn

### Шаги

1. Клонируйте репозиторий:
   ```bash
   git clone <repository-url>
   cd Computer_Network-main
   ```

2. Установите зависимости:
   ```bash
   pip install fastapi uvicorn
   ```

3. Запустите сервер:
   ```bash
   uvicorn main:app --reload
   ```
   Сервер запустится по адресу: `http://127.0.0.1:8000`

## Использование API

Автоматическая документация: `http://127.0.0.1:8000/docs`

### Формат ответов

Все ответы следуют единому формату:

**Успех:**
```json
{
    "success": true,
    "exception": null,
    "... дополнительные поля ..."
}
```

**Ошибка:**
```json
{
    "success": false,
    "exception": {
        "message": "Описание ошибки"
    }
}
```

### 1. Регистрация игрока

**URL:** `POST /user/register`

**Тело запроса:**
```json
{
    "nickname": "Player1",
    "password": "mypassword"
}
```

**Ответ:**
```json
{
    "success": true,
    "exception": null,
    "nickname": "Player1",
    "accessToken": "P3Z7su6UI888hKOE"
}
```

**Пример curl:**
```bash
curl -X POST http://127.0.0.1:8000/user/register \
  -H "Content-Type: application/json" \
  -d '{"nickname": "Player1", "password": "pass123"}'
```

### 2. Создание игровой комнаты

**URL:** `POST /set/room/create`

**Тело запроса:**
```json
{
    "accessToken": "P3Z7su6UI888hKOE"
}
```

**Ответ:**
```json
{
    "success": true,
    "exception": null,
    "gameId": 0
}
```

**Пример curl:**
```bash
curl -X POST http://127.0.0.1:8000/set/room/create \
  -H "Content-Type: application/json" \
  -d '{"accessToken": "YOUR_TOKEN"}'
```

### 3. Список игровых комнат

**URL:** `POST /set/room/list`

**Тело запроса:**
```json
{
    "accessToken": "P3Z7su6UI888hKOE"
}
```

**Ответ:**
```json
{
    "success": true,
    "exception": null,
    "games": [
        {"id": 0},
        {"id": 1}
    ]
}
```

### 4. Вход в игровую комнату

**URL:** `POST /set/room/enter`

**Тело запроса:**
```json
{
    "accessToken": "P3Z7su6UI888hKOE",
    "gameId": 0
}
```

**Ответ:**
```json
{
    "success": true,
    "exception": null,
    "gameId": 0
}
```

### 5. Просмотр игрового поля

**URL:** `POST /set/field`

**Тело запроса:**
```json
{
    "accessToken": "P3Z7su6UI888hKOE"
}
```

**Ответ:**
```json
{
    "success": true,
    "exception": null,
    "cards": [
        {
            "id": 6,
            "color": 1,
            "shape": 2,
            "fill": 3,
            "count": 1
        },
        ...
    ],
    "status": "ongoing",
    "score": 0
}
```

**Статусы игры:**
- `ongoing` - игра продолжается
- `ended` - игра завершена

**Карты Set:**
- `color`: 1, 2, 3 (красный, зелёный, фиолетовый)
- `shape`: 1, 2, 3 (овал, ромб, волна)
- `fill`: 1, 2, 3 (пустой, заштрихованный, заполненный)
- `count`: 1, 2, 3 (количество фигур на карте)

### 6. Взятие сета

**URL:** `POST /set/pick`

**Тело запроса:**
```json
{
    "accessToken": "P3Z7su6UI888hKOE",
    "cards": [11, 7, 29]
}
```

**Ответ:**
```json
{
    "success": true,
    "exception": null,
    "isSet": true,
    "score": 1
}
```

**Правила:**
- За правильный сет: +1 очко
- За неправильный сет: -1 очко
- При правильном сете: карты заменяются новыми (если в колоде есть карты)

### 7. Добавление карт на стол

**URL:** `POST /set/add`

**Тело запроса:**
```json
{
    "accessToken": "P3Z7su6UI888hKOE"
}
```

**Ответ:**
```json
{
    "success": true,
    "exception": null
}
```

Добавляет 3 карты из колоды на игровое поле.

### 8. Таблица очков

**URL:** `POST /set/scores`

**Тело запроса:**
```json
{
    "accessToken": "P3Z7su6UI888hKOE"
}
```

**Ответ:**
```json
{
    "success": true,
    "exception": null,
    "users": [
        {
            "name": "Player1",
            "score": 5
        },
        {
            "name": "Player2",
            "score": 3
        }
    ]
}
```

Игроки отсортированы по убыванию очков.

## Правила игры Set

**Цель:** найти "сет" - набор из 3 карт, где каждое свойство (цвет, форма, заливка, количество) либо **одинаковое** у всех трёх карт, либо **разное** у всех трёх.

**Примеры:**
- ✅ Правильный сет: все три карты имеют одинаковый цвет, разную форму, разную заливку, разное количество
- ❌ Неправильный сет: две карты красные, одна зелёная (цвет не все одинаковые и не все разные)

## Тестирование

Запустите автоматический тест:
```bash
python test_server.py
```

Скрипт проверит все функции сервера:
1. Регистрацию нескольких игроков
2. Создание и просмотр игровых комнат
3. Вход в игру
4. Получение карт
5. Попытку взять сет
6. Просмотр таблицы очков

## Структура проекта

```
.
├── main.py          # Основной файл сервера
├── test_server.py   # Автоматические тесты
├── README.md        # Документация
└── .gitignore       # Git ignore файл
```

## Соответствие протоколу

Сервер полностью реализует протокол [com.krushiler.set-game-server](https://github.com/Krushiler/com.krushiler.set-game-server/blob/master/Readme.md):

- ✅ `/user/register` - регистрация с nickname и password
- ✅ `/set/room/create` - создание игровой комнаты
- ✅ `/set/room/list` - список активных игр
- ✅ `/set/room/enter` - вход в игру
- ✅ `/set/field` - получение карт на поле
- ✅ `/set/pick` - попытка взять сет
- ✅ `/set/add` - добавление карт на поле
- ✅ `/set/scores` - таблица очков игроков
- ✅ Стандартный формат ответов с `success`, `exception`, `accessToken`
- ✅ Правильная логика игры Set
- ✅ Поддержка нескольких игровых комнат
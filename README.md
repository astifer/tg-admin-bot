# Telegram bot for your chat administration

## Функционал

Бот администратор. Отвечайте на сообщение человека, чтобы применить к нему меры. А вот и они:

-   ```/mute 5``` замутить человека и запретить писать ему на несколько минут
-   ```/unmute``` отменить мут человека
-   ```/kick``` удалить человека из чата

В дополнение, каждое сообщение проходит валидацию мл моделью на предмет токсичности, мата и грубости. Если сообщение не проходит проверку, сообщение удаляется

## Что под капотом

Существуют два основных сервиса: бот и сервис с млькой, оба обернуты в докере. Весь проект в целом собирается с с помощью ```docker-compose```. 

- Бот написан на асинхронной библиотеке ```aiogram```, логика прописана [тут](./bot/bot.py)
- Модель - это маленькая модель ```bert``` 

Так как эти два сервиса должны как-то общатся, работает брокер сообщений ```RabitMQ```, в котором прописаны две противонаправленные очереди для отправки сообщения и вероятности токсичности сообщения

## Как это запустить локально

Обычный докер компоуз, в [файле](./docker-compose.yaml) прописаны основные переменные, порты и сервисы

```docker-compose up -d --build```

## Тесты и линтер

Проект покрывается тестами 

Проект пройден через линтер ```flake8```

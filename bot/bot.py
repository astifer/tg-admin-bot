import asyncio
import logging
import functools
import pika
from typing import Any, Callable, Dict, Awaitable, Union
from datetime import datetime, timedelta

from aiogram import BaseMiddleware, Bot, Dispatcher, types, Router
from aiogram.filters import BaseFilter
from aiogram.filters.command import Command, CommandObject
from aiogram.types import Message, Update
from aiogram.types.chat_permissions import ChatPermissions
from aiogram.types.chat_member_owner import ChatMemberOwner

from config_reader import config


logging.basicConfig(level=logging.INFO)

bot = Bot(token=config.BOT_TOKEN.get_secret_value())
dp = Dispatcher()
router = Router()

admins = 'creator', 'administrator'

usual_permissions = ChatPermissions(
    can_send_messages=True,
    can_send_media_messages=True,
    can_send_other_messages=True,
    can_add_web_page_previews=True,
)

mute_permissions = ChatPermissions(
    can_send_messages=False,
    can_send_media_messages=False,
    can_send_other_messages=False,
    can_add_web_page_previews=False,
)


class ChatTypeFilter(BaseFilter):
    def __init__(self, chat_type: Union[str, list]):
        self.chat_type = chat_type

    async def __call__(self, message: Message) -> bool:
        if isinstance(self.chat_type, str):
            return message.chat.type == self.chat_type
        else:
            return message.chat.type in self.chat_type


def set_privileges(privilege):
    """
    Декоратор для установки уровня доступа к функции.
    Так же он удаляет сообщения.
    """

    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            message = args[0]
            if privilege == 'administrator':
                response = await bot.get_chat_member(message.chat.id, message.from_user.id)
                if response.status in admins:
                    await func(*args, **kwargs)
            elif privilege == 'creator':
                response = await bot.get_chat_member(message.chat.id, message.from_user.id)
                if response.status == 'creator':
                    await func(*args, **kwargs)
            else:
                await message.reply("У вас недостаточно прав для использования этой команды.")
                await message.delete()

        return wrapper

    return decorator


class AntiToxic(BaseMiddleware):
    def __init__(
            self,
            bot: Bot,
            rabbitmq_host: str,
            rabbitmq_port: int,
            rabbitmq_queue_check: str,
            rabbitmq_queue_result: str
    ):
        self.bot = bot
        self.rabbitmq_host = rabbitmq_host
        self.rabbitmq_port = rabbitmq_port
        self.rabbitmq_queue_check = rabbitmq_queue_check
        self.rabbitmq_queue_result = rabbitmq_queue_result

        credentials = pika.credentials.PlainCredentials(
            username=config.RABBITMQ_DEFAULT_USER.get_secret_value(),
            password=config.RABBITMQ_DEFAULT_PASS.get_secret_value(),
        )
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(
                host=self.rabbitmq_host,
                port=self.rabbitmq_port,
                credentials=credentials,
                # heartbeat=600,
                # blocked_connection_timeout=300,
            )
        )
        self.channel = connection.channel()
        self.channel_res = connection.channel()
        self.channel.queue_declare(queue=self.rabbitmq_queue_check)
        self.channel_res.queue_declare(queue=self.rabbitmq_queue_result)

    async def __call__(
        self,
        handler: Callable[[Union[Message, Update], Dict[str, Any]], Awaitable[Any]],
        event: Union[Message, Update],
        data: Dict[str, Any]
    ) -> Any:
        # Кладем в очередь для проверки, если у сообщения есть текст
        if event.message.text:
            self.channel.basic_publish(
                    exchange='',
                    routing_key=self.rabbitmq_queue_check,
                    body=event.message.text
            )

            await asyncio.sleep(1)
            # Берем результат проверки сообщения на токсичность
            method, properties, body = self.channel_res.basic_get(
                queue=self.rabbitmq_queue_result,
                auto_ack=True
            )
            message = "empty"
            if body:
                message = body.decode()

            logging.info(message)
            if (message == 'True'):  # Токсичное сообщение
                await self.bot.delete_message(
                    event.message.chat.id,
                    event.message.message_id
                )
                await self.bot.send_message(
                    event.message.chat.id,
                    "Токсичное сообщение удалено"
                )
                # result = await restrict_user(
                #     self.bot,
                #     event.message.chat.id,
                #     event.message.from_user.id,
                #     1440
                # )
        return await handler(event, data)

    async def on_shutdown(self, dispatcher: Dispatcher):
        if self.channel:
            self.channel.stop_consuming()
            self.channel.close()
            self.connection.close()


async def restrict_user(bot: Bot, chat_id: int, user_id: int, duration: int):
    duration = min(1440, duration)
    duration = max(1, duration)

    new_time = datetime.now() + timedelta(minutes=duration)
    result = await bot.restrict_chat_member(
        chat_id=chat_id,
        user_id=user_id,
        permissions=mute_permissions,
        until_date=new_time,
    )
    return result


@router.message(Command("unmute"), ChatTypeFilter(chat_type="supergroup"))
@set_privileges('administrator')
async def unmute_user(message: types.Message, command: types.Message):
    """     Снимает все ограничения с пользователя.

    Args:
        message (types.Message): полученное сообщение /unmute
        command (types.Message): параметры, переданные через пробел
    """
    if message.reply_to_message:
        user_id = message.reply_to_message.from_user.id
        chat_id = message.chat.id
        goal_type = await bot.get_chat_member(chat_id, user_id)
        goal_is_owner = isinstance(
            goal_type,
            ChatMemberOwner
        )
        if not goal_is_owner and bot.id != user_id:
            new_time = datetime.now() + timedelta(seconds=10)
            await bot.restrict_chat_member(
                chat_id,
                user_id,
                permissions=usual_permissions,
                until_date=new_time
            )
            await message.answer(
                f'{message.reply_to_message.from_user.full_name} разблокирован'
            )
        elif user_id == bot.id:
            await message.answer(
                'Со мной все в порядке!'
            )
        elif goal_is_owner:
            await message.answer(
                'Ко владельцу чата не применимы команды'
            )
    else:
        await message.reply(
            'Вы должны написать команду, '
            'отвечая на чье-то сообщение'
        )


@router.message(Command("mute"),  ChatTypeFilter(chat_type="supergroup"))
@set_privileges('administrator')
async def mute_user(message: types.Message, command: CommandObject):
    """    Запрещает отправлять сообщения пользователю.


    Args:
        message (types.Message): полученное сообщение /mute
        command (CommandObject): параметры, переданные через пробел
    """
    if message.reply_to_message:
        try:
            duration = 60 if not command.args else int(command.args.split()[0])
        except ValueError:
            await message.reply('Укажите через пробел количество минут')

        original_message = message.reply_to_message
        chat_id = original_message.chat.id
        user_id = original_message.from_user.id
        chat_admins = await bot.get_chat_administrators(chat_id)
        goal_not_in_admins = True
        for admins in chat_admins:
            if admins.user.id == user_id:
                goal_not_in_admins = False

        if goal_not_in_admins and user_id != bot.id:
            result = await restrict_user(bot, chat_id, user_id, duration)
            if result:
                await message.answer(
                    f'{original_message.from_user.full_name} '
                    f'заблокирован на {duration} минут'
                )
            else:
                await message.answer(
                    f'Я не могу заблокировать '
                    f'{original_message.from_user.full_name}'
                )
        elif user_id == bot.id:
            await message.answer(
                'Со мной все в порядке!'
            )
        elif not goal_not_in_admins:
            await message.answer(
                'Я не могу заблокировать администратора'
            )
    else:
        await message.reply(
            'Вы должны написать команду, '
            'отвечая на чье-то сообщение'
            )


@router.message(Command("kick"), ChatTypeFilter(chat_type="supergroup"))
@set_privileges('administrator')
async def kick_user(message: types.Message):
    """    Выгоняет пользователя из чата

    Args:
        message (types.Message): полученное сообщение /kick
    """

    if message.reply_to_message:
        original_message = message.reply_to_message
        chat_id = original_message.chat.id
        user_id = original_message.from_user.id
        chat_admins = await bot.get_chat_administrators(chat_id)
        goal_not_in_admins = True
        for admins in chat_admins:
            if admins.user.id == user_id:
                goal_not_in_admins = False
        if goal_not_in_admins and user_id != bot.id:
            result = await bot.ban_chat_member(
                chat_id=chat_id,
                user_id=user_id,
                until_date=datetime.now() + timedelta(minutes=60)
            )
            if not result:
                await message.answer(
                    f'Я не могу выгнать '
                    f'{original_message.from_user.full_name}'
                )
        elif user_id == bot.id:
            await message.answer(
                'Со мной все в порядке!'
            )
        else:
            await message.answer(
                'Я не могу выгнать администратора'
            )
    else:
        await message.reply(
            'Вы должны написать команду, '
            'отвечая на чье-то сообщение'
        )


async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    dp.update.outer_middleware(AntiToxic(
        bot=bot,
        rabbitmq_host="rabbitmq",
        rabbitmq_port=5672,
        rabbitmq_queue_check="check",
        rabbitmq_queue_result="result"
    ))
    dp.include_router(router)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

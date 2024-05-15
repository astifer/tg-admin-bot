import asyncio
import logging
from aiogram import Bot, Dispatcher, types, Router
from aiogram.filters.command import Command, CommandObject
from aiogram.types.chat_permissions import ChatPermissions
from aiogram.types.chat_member_owner import ChatMemberOwner
from aiogram.types.chat_member_administrator import ChatMemberAdministrator
from datetime import datetime, timedelta

from config_reader import config


logging.basicConfig(level=logging.INFO)

bot = Bot(token=config.BOT_TOKEN.get_secret_value())

dp = Dispatcher()
router = Router()

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


@router.message(Command("unmute"))
async def unmute_user(message: types.Message, command: types.Message):
    """     Снимает все ограничения с пользователя.

    Args:
        message (types.Message): полученное сообщение /unmute
        command (types.Message): параметры, переданные через пробел
    """
    if message.reply_to_message:
        user_id = message.reply_to_message.from_user.id
        chat_id = message.chat.id
        author_id = message.from_user.id
        goal_type = await bot.get_chat_member(chat_id, user_id)
        author_type = await bot.get_chat_member(chat_id, author_id)
        author_is_admin = isinstance(
            author_type,
            (ChatMemberOwner, ChatMemberAdministrator)
        )
        goal_is_owner = isinstance(
            goal_type,
            ChatMemberOwner
        )
        if author_is_admin and not goal_is_owner and bot.id != user_id:
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


@router.message(Command("mute"))
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
        reporter_id = message.from_user.id
        chat_admins = await bot.get_chat_administrators(chat_id)
        goal_not_in_admins = True
        reporter_in_admins = False
        for admins in chat_admins:
            if admins.user.id == reporter_id:
                reporter_in_admins = True
            if admins.user.id == user_id:
                goal_not_in_admins = False

        if reporter_in_admins and goal_not_in_admins and user_id != bot.id:
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
        elif not reporter_in_admins:
            await message.answer(
                'Вы не администратор'
            )
    else:
        await message.reply(
            'Вы должны написать команду, '
            'отвечая на чье-то сообщение'
            )


@router.message(Command("kick"))
async def kick_user(message: types.Message):
    """    Выгоняет пользователя из чата

    Args:
        message (types.Message): полученное сообщение /kick
    """

    if message.reply_to_message:
        original_message = message.reply_to_message
        chat_id = original_message.chat.id
        user_id = original_message.from_user.id
        reporter_id = message.from_user.id
        chat_admins = await bot.get_chat_administrators(chat_id)
        goal_not_in_admins = True
        reporter_in_admins = False
        for admins in chat_admins:
            if admins.user.id == reporter_id:
                reporter_in_admins = True
            if admins.user.id == user_id:
                goal_not_in_admins = False
        if reporter_in_admins and goal_not_in_admins and user_id != bot.id:
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
        elif not reporter_in_admins:
            await message.answer(
                'Вы не администратор'
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
dp.include_router(router)


async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

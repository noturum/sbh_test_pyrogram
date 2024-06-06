import asyncio
import os
from datetime import datetime
from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.errors import (UserDeactivated,
                             UserDeactivatedBan)
from DataBase import (db_controller,
                      Chats,
                      Status)
from asyncio import TaskGroup
from time import sleep
try:
    API_ID = os.getenv('API_ID')
    assert API_ID , 'Check .env'
    API_HASH = os.getenv('API_HASH')
    assert API_HASH
except AssertionError:
    exit(1)

app = Client("def", api_id=API_ID, api_hash=API_HASH)
triger_word = 'triger'
timeout = 60*60
first_time = 6
second_time = 39
third_time = 60*26


async def send_message(text, chat):
    try:
        if text != chat.last_message:
            await app.send_message(chat.id_chat, text)
            chat.last_message = text
            await db_controller.save(chat)

    except (UserDeactivatedBan, UserDeactivated):
        chat.status = Status.DEAD
        db_controller.save(chat)


@app.on_message(filters.text & filters.private)
async def msg_handlr(client: Client, message: Message):
    id_chat = message.from_user.id
    created_at = datetime.now()
    if model := await db_controller.get_by_id(id_chat):
        split_word = message.text.split(' ')
        model = model[0]
        if ("прекрасно" or 'ожидать') in split_word:

            model.status = Status.FINISHED
            await db_controller.save(model)
        elif triger_word in split_word:
            model.triger = True
            await db_controller.save(model)
    else:
        model = Chats(id_chat=id_chat,
                      created_at=created_at,
                      status=Status.ALIVE)
        await db_controller.save(model)


async def main():
    async with TaskGroup() as group:
        group.create_task(app.start())
        group.create_task(db_controller.bootstrap())
    while 1:
        chats = await db_controller.get_all()
        print(chats)
        for chat in chats:
            delta_min = (datetime.now() - chat.created_at).seconds / 60
            if delta_min >= first_time:
                if delta_min >= second_time:
                    if delta_min >= third_time:
                        await send_message('msg3', chat)
                        chat.status = Status.FINISHED
                        await db_controller.save(chat)
                    elif not chat.triger:
                        await send_message('msg2', chat)
                else:
                    await send_message('msg1', chat)

        sleep(timeout) # таймаут на чек, раз в минуту

asyncio.get_event_loop().run_until_complete(main())

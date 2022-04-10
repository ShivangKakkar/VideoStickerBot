import os
from pystark import Stark
from database import database
from pystark.config import ENV
from pyrogram.types import Message
from plugins.bot_api import BotAPI

OWNER_ID = ENV().OWNER_ID


@Stark.cmd('packs', description="Get List of Your Packs")
async def packs_func(_, msg: Message):
    if msg.from_user.id not in OWNER_ID:
        user_id = msg.from_user.id
        packs = (await database.get('users', msg.from_user.id)).get("packs")
        if not packs:
            await msg.reply('You have no packs yet. Create one by sending a Video or GIF', quote=True)
            return
        if packs == 1:
            string = '**Your Pack** \n\n'
        else:
            string = '**Your Packs** \n\n'
        number = 0
        for n in range(1, packs+1):
            number += 1
            if n == 1:
                string += f"{number}) https://t.me/addstickers/{BotAPI.PACK_NAME.format(user_id)}\n"
            else:
                string += f"{number}) https://t.me/addstickers/{BotAPI.NEW_PACK_NAME.format(n, user_id)}\n"
        await msg.reply(string, quote=True)
        return
    users = await database.all('users')
    string = '**Total Packs Created** : {} \n\n'
    number = 0
    for x in users:
        if x['packs']:
            packs = x['packs']
            for n in range(1, packs+1):
                number += 1
                if n == 1:
                    string += f"{number}) https://t.me/addstickers/{BotAPI.PACK_NAME.format(x['user_id'])}\n"
                else:
                    string += f"{number}) https://t.me/addstickers/{BotAPI.NEW_PACK_NAME.format(n, x['user_id'])}\n"
    string = string.format(number)
    if len(string) > 4096:
        with open('packs.txt', 'w') as f:
            f.write(string)
        await msg.reply_document('packs.txt', quote=True)
        os.remove('packs.txt')
    else:
        await msg.reply(string, quote=True)

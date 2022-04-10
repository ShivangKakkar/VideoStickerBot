import os
from database import database
from plugins.helpers import Helpers
from pystark import Stark, Message, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery


@Stark.cmd(private_only=True, extra_filters=filters.video | filters.animation)
async def main(_, msg: Message):
    status = await msg.reply("Doing what I do best...")
    stark = Helpers(msg, status)
    await process(msg, stark, status)
    if os.path.exists(stark.input_file):
        os.remove(stark.input_file)
    if os.path.exists(stark.output_file):
        os.remove(stark.output_file)


async def process(msg: Message, stark: Helpers, status: Message):
    await msg.download(stark.input_file)
    std = await stark.subshell()
    if os.path.exists(stark.output_file):
        await stark.correct_the_size()  # File is too big error
        await status.edit('Getting your pack...')
        success, pack_name, title = await stark.get_default_pack()
        should_ask = await database.get('users', stark.user_id, 'ask_emojis')
        if should_ask:
            emojis = await stark.ask_for_emojis()
            if not emojis:
                return
        else:
            data = await database.get('users', msg.from_user.id, "default_emojis")
            if data:
                emojis = data
            else:
                emojis = '❤️'
        params = await stark.params(pack_name, emojis, title)
        file = open(stark.output_file, 'rb')
        if success:
            success = await stark.add_to_pack(params, file)
            if not success:
                return
        else:
            success = await stark.new_pack(params, file)
            if not success:
                return
        sticker = await stark.get_pack(params, file)
        await status.delete()
        if sticker:
            button = [[InlineKeyboardButton('Get WEBM File', callback_data='current_webm')]]
            await msg.reply_sticker(
                sticker,
                reply_to_message_id=msg.message_id,
                reply_markup=InlineKeyboardMarkup(button)
            )
        file.close()
        await stark.session.aclose()
    else:
        await stark.ffmpeg_error(std)
        return


@Stark.callback('current_webm')
async def get_webm(_, callback: CallbackQuery):
    await Helpers.send_webm(callback.message)
    await callback.answer()


@Stark.cmd(private_only=True, extra_filters=filters.sticker, group=1)
async def existing_sticker_func(_, msg: Message):
    if msg.sticker.is_video:
        data = await database.get('users', msg.from_user.id)
        if data['kang_mode']:
            status = await msg.reply("Doing what I do best [Kanging]... ")
            sticker_file = await msg.download(f'kangs/{msg.from_user.id}_{msg.message_id}.webm')
            stark = Helpers(msg, status)
            await status.edit('Getting your pack...')
            success, pack_name, title = await stark.get_default_pack()
            should_ask = await database.get('users', stark.user_id, 'ask_emojis')
            if should_ask:
                emojis = await stark.ask_for_emojis()
                if not emojis:
                    return
            else:
                data = await database.get('users', msg.from_user.id, "default_emojis")
                if data:
                    emojis = data
                else:
                    emojis = '❤️'
            params = await stark.params(pack_name, emojis, title)
            file = open(sticker_file, 'rb')
            if success:
                success = await stark.add_to_pack(params, file)
                if not success:
                    return
            else:
                success = await stark.new_pack(params, file)
                if not success:
                    return
            sticker = await stark.get_pack(params, file)
            await status.delete()
            if sticker:
                await msg.reply_sticker(
                    sticker,
                    reply_to_message_id=msg.message_id,
                )
            file.close()
            os.remove(sticker_file)
            await stark.session.aclose()
        elif data['get_webm']:
            await Helpers.send_webm(msg)

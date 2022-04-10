from pystark import Stark
from pyrogram import filters
from database import database
from plugins.helpers import Helpers
from pyrogram.types import CallbackQuery
from plugins.settings import user_settings, default_emojis_settings


@Stark.callback('emojis')
async def emojis_cb_func(_, query: CallbackQuery):
    await change_bool('ask_emojis', query)


@Stark.callback('webm')
async def webm_cb_func(_, query: CallbackQuery):
    await change_bool('get_webm', query)


@Stark.callback('kang_mode')
async def kang_cb_func(_, query: CallbackQuery):
    await change_bool('kang_mode', query)


@Stark.callback('default_emojis')
async def default_emojis_cb_func(_, query: CallbackQuery):
    user_id = query.from_user.id
    text, markup = await default_emojis_settings(user_id)
    if text:
        await query.edit_message_text(text, reply_markup=markup)
        await query.answer()
    else:
        await query.answer('Not Found')


@Stark.callback('change_default_emojis')
async def change_default_emojis_cb_func(bot: Stark, query: CallbackQuery):
    user_id = query.from_user.id
    await query.answer()
    emojis_msg = await bot.ask(user_id, 'Please send me the emojis', filters=filters.text & filters.incoming)
    emojis = await Helpers.extract_emojis(emojis_msg)
    if not emojis:
        await emojis_msg.reply('No valid emojis found. Process Exited', quote=True)
        return
    await database.set('users', user_id, {"default_emojis": emojis})
    await emojis_msg.reply('Emojis set successfully.', quote=True)
    text, markup = await user_settings(user_id)
    await query.message.reply(text, reply_markup=markup)


@Stark.callback('remove_default_emojis')
async def remove_default_emojis_cb_func(_, query: CallbackQuery):
    data = await database.get('users', query.from_user.id, 'default_emojis')
    if data:
        await database.set('users', query.from_user.id, {'default_emojis': None})
        await query.answer('Removed Successfully!', show_alert=True)
        text, markup = await user_settings(query.from_user.id)
        await query.edit_message_text(text, reply_markup=markup)
    else:
        await query.answer("Default Emojis weren't set anyway", show_alert=True)


# ------------------------------------------------ #

@Stark.callback('back')
async def back_func(_, query: CallbackQuery):
    text, markup = await user_settings(query.from_user.id)
    await query.message.edit(text, reply_markup=markup)
    await query.answer('', show_alert=True)


# ------------------------------------------------ #

async def change_bool(key, query):
    user_id = query.from_user.id
    data = await database.get('users', user_id, key)
    if data:
        await database.set('users', user_id, {key: False})
    else:
        await database.set('users', user_id, {key: True})
    text, markup = await user_settings(user_id)
    if text == query.message.text:
        await query.answer('An old message. Deleting...')
        await query.message.delete()
        return
    if not text:
        await query.answer('An error occurred. Try a second time, If it persists ask in support chat')
        return
    await query.edit_message_text(text, reply_markup=markup)
    await query.answer()

from pyrogram import emoji
from database import database
from pystark import Stark, Message
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup


@Stark.cmd('settings', description='Configure personal bot settings.', private_only=True)
async def settings(_, msg: Message):
    text, markup = await user_settings(msg.from_user.id)
    await msg.react(text, reply_markup=markup)


async def user_settings(user_id):
    data = await database.get('users', user_id)
    if not data:
        return False, False
    tick = ' ✔'
    cross = ' ✖️ '
    ask_emojis = "Ask for Emojis"
    ask_emojis_msg = f"Set to True if you want the bot to ask for emojis that will be set to the video sticker while adding to pack. If set to False, all stickers will use default emoji, which is - {emoji.RED_HEART}"
    get_webm = "Get WEBM"
    get_webm_msg = f"Set to True if you want to get webm files when you send any existing video sticker. This way, you can add stickers from other people's packs using @Stickers. If False, bot will ignore the sticker."
    kang_mode = "Kang Mode"
    kang_mode_msg = "Set to True if you want to add stickers to your pack by just sending a video sticker from some existing pack. This way, you can add stickers from other people's packs to your pack. If False, bot will ignore the sticker."
    default_emojis = "Default Emojis"
    default_emojis_msg = f"Set default emojis to be used in your stickers. If nothing is set, {emoji.RED_HEART} will be used."
    text = f'**Settings** \n\n'
    ask_emojis_db = data['ask_emojis']
    get_webm_db = data['get_webm']
    kang_mode_db = data['kang_mode']
    default_emojis_db = data['default_emojis']
    general_text = "**{}** : {} \n{} \n\n"
    if ask_emojis_db:
        text += general_text.format(ask_emojis, 'True', ask_emojis_msg)
        ask_emojis += tick
    else:
        text += general_text.format(ask_emojis, 'False', ask_emojis_msg)
        ask_emojis += cross
    if get_webm_db:
        text += general_text.format(get_webm, 'True', get_webm_msg)
        get_webm += tick
    else:
        text += general_text.format(get_webm, 'False', get_webm_msg)
        get_webm += cross
    if kang_mode_db:
        text += general_text.format(kang_mode, 'True', kang_mode_msg)
        kang_mode += tick
    else:
        text += general_text.format(kang_mode, 'False', kang_mode_msg)
        kang_mode += cross
    if default_emojis_db:
        text += general_text.format(default_emojis, default_emojis_db, default_emojis_msg)
        default_emojis += ' - SET'
    else:
        text += general_text.format(default_emojis, 'Not Set', default_emojis_msg)
        default_emojis += ' - NOT SET'
    text += 'Use below buttons to change values. A tick means True and cross means False'
    markup = InlineKeyboardMarkup([
        [InlineKeyboardButton(ask_emojis, callback_data="emojis")],
        [InlineKeyboardButton(default_emojis, callback_data="default_emojis")],
        [InlineKeyboardButton(kang_mode, callback_data="kang_mode")],
        [InlineKeyboardButton(get_webm, callback_data="webm")],
    ])
    return text, markup


async def default_emojis_settings(user_id):
    data = await database.get('users', user_id)
    if not data:
        return False, False
    data = data['default_emojis']
    if data:
        markup = InlineKeyboardMarkup([
            [InlineKeyboardButton('Change Emojis', callback_data="change_default_emojis")],
            [InlineKeyboardButton('Remove Default Emojis', callback_data="remove_default_emojis")],
            [InlineKeyboardButton('<-- Go Back', callback_data="back")],
        ])
        text = f'Current Default Emojis are `{data}` \n\nUse below buttons to change or remove them'
    else:
        markup = InlineKeyboardMarkup([
            [InlineKeyboardButton('Add Emojis', callback_data="change_default_emojis")],
            [InlineKeyboardButton('<-- Go Back', callback_data="back")],
        ])
        text = 'Currently no Emojis are set. Use below button to add them.'
    return text, markup

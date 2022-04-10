import os
import emoji
import asyncio
from pystark import filters
from database import database
from plugins.bot_api import BotAPI
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message


class Helpers(BotAPI):

    def __init__(self, message: Message, status: Message):
        super().__init__(message, status)
        self.ffprobe = """ffprobe -v error -select_streams v -show_entries {} -of csv=p=0:s=x {}"""

    async def user_settings(self) -> tuple[bool, bool] | tuple[str, InlineKeyboardMarkup]:
        data = await database.get('users', self.user_id)
        if not data:
            return False, False
        tick = '✔'
        cross = '✖️ '
        ask_emojis = 'Ask for Emojis '
        text = f'**Settings** \n\n'
        ask_emojis_db = data['ask_emojis']
        if ask_emojis_db:
            ask_emojis += tick
            text += f"**Ask For Emojis** : True"
        else:
            ask_emojis += cross
            text += f"**Ask For Emojis** : False"
        markup = InlineKeyboardMarkup([
            [InlineKeyboardButton(ask_emojis, callback_data="emojis")]
        ])
        return text, markup

    @staticmethod
    async def extract_emojis(text: str | Message) -> str:
        if isinstance(text, Message):
            text = text.text
        emojis = ''.join(char for char in text if char in emoji.EMOJI_DATA)
        return emojis

    async def ask_for_emojis(self):
        emojis_msg = await self.client.ask(
            self.user_id,
            "Please send me emojis to add in this sticker.",
            filters=filters.text & filters.incoming
        )
        status = await emojis_msg.reply('Inspecting Input...')
        emojis = await self.extract_emojis(emojis_msg)
        if not emojis:
            await status.edit('Invalid Emojis. Process Cancelled.')
            return None
        await self.status.delete()
        self.status = status
        return emojis

    async def subshell(self, cmd: str = '') -> str:
        if not cmd:
            cmd = await self.get_ffmpeg_cmd()
        proc = await asyncio.create_subprocess_shell(cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
        stdout, stderr = await proc.communicate()
        return stderr.decode('utf-8') if stderr else stdout.decode('utf-8')

    async def get_ffmpeg_cmd(self):
        cmd = """ffmpeg -ss 00:00:00 -to 00:00:03 -t 3 -i {} -fs 256000 -c:v libvpx-vp9 -b:v 0 -vf "scale=512:-2" -an {}"""
        # -metadata:s:v:0 alpha_mode="1" a -> ALPHA CHANNEL
        # -b:a 128k -c:a libopus -> AUDIO
        dim = await self.get_dimensions()
        if not dim:
            cmd = cmd.replace("512:-2", "-2:512")
        return cmd.format(self.input_file, self.output_file)

    async def get_dimensions(self):
        cmd = self.ffprobe.format('stream=width,height', self.input_file)
        info = await self.subshell(cmd)
        dim = info.split('x')
        dim = [int(x) for x in dim]
        if dim[0] < dim[1]:
            return False
        else:
            return True

    async def correct_the_size(self):
        cmd = self.ffprobe.format('format=size', self.output_file)
        try:
            info = await self.subshell(cmd)
            info = int(info)
        except Exception as e:
            print("Shit")
            return str(e)
        kib = info // 1024
        if kib > 256:
            await self.status.edit('Resizing Video to fit Telegram Limits...')
            new_output = self.output_file.replace('.webm', '2.webm')
            cmd = f"ffmpeg -i {self.output_file} -b:v 555k {new_output}"
            await self.subshell(cmd)
            os.remove(self.output_file)
            self.output_file = new_output
        return False

    async def get_default_pack(self) -> tuple[bool, str, str]:
        packs = await database.get('users', self.user_id, 'packs')
        if packs <= 1:
            if not packs:
                boo = False
            else:
                boo = True
            return boo, self.PACK_NAME.format(self.user_id), self.PACK_TITLE
        else:
            return True, self.NEW_PACK_NAME.format(packs, self.user_id), self.NEW_PACK_TITLE.format(packs)

    @staticmethod
    async def send_webm(message: Message):
        await message.reply_chat_action('upload_video')
        file = f"downloads/{message.from_user.id}_{message.message_id}.webm"
        await message.download(file)
        await message.reply_document(file, quote=True)
        if os.path.exists(file):
            os.remove(file)

import httpx
import typing
import requests
from pystark import Message
from database import database
from pystark.config import ENV
from plugins.exceptions import TooManyRequests, AlreadyOccupied, UnknownException, StickersTooMuch, StickerPackInvalid


class BotAPI:
    base_url = f"https://api.telegram.org/bot{ENV.BOT_TOKEN}/"
    new_pack_url = f"{base_url}createNewStickerSet"
    get_pack_url = f"{base_url}getStickerSet"
    add_to_pack_url = f"{base_url}addStickerToSet"
    ERROR = "Oops, an error occurred. My owner has been notified. \n\nFor queries visit @StarkBotsChat"
    username = requests.get(base_url + "getMe").json()["result"]["username"].title()
    PACK_NAME = "fpack_{}_by_" + username
    NEW_PACK_NAME = "fpack{}_{}_by_" + username
    PACK_TITLE = 'Pack By @' + username
    NEW_PACK_TITLE = 'Pack {} By @' + username
    LOG_CHAT = ENV().LOG_CHAT

    def __init__(self, message: Message, status: Message):
        self.session = httpx.AsyncClient()
        self.user_id = message.from_user.id
        self.message = message
        self.directory = 'downloads'
        self.input_file = f"{self.directory}/{self.user_id}_{message.message_id}"
        self.output_file = f"{self.input_file}_output.webm"
        self.client = message._client
        self.status = status

    async def params(self, pack_name, emojis, title):
        # if not pack_name:
        #     pack_name = self.PACK_NAME.format(self.user_id)
        # if not title:
        #     title = self.PACK_TITLE
        params = {
            'user_id': self.user_id,
            'name': pack_name,
            'emojis': emojis,
            'title': title
        }
        return params

    async def new_pack(self, params: dict, file: typing.BinaryIO):
        return await self.interact('new', params, file)

    async def add_to_pack(self, params: dict, file: typing.BinaryIO):
        return await self.interact('add', params, file)

    async def get_pack(self, params: dict, file: typing.BinaryIO) -> str:
        return await self.interact('get', params, file)

    async def interact(self, method, params, file: typing.BinaryIO) -> str | bool:
        if method == 'get':
            url = self.get_pack_url
        elif method == 'new':
            url = self.new_pack_url
        else:
            url = self.add_to_pack_url
        data = await self.session.post(url=url, params=params, files={'webm_sticker': file})
        resp = data.json()
        try:
            await self.error(resp, params['name'])
        except TooManyRequests as e:
            msg = self.message
            err = f"Error from Telegram \n\n{e.desc} \n\nFor queries visit @StarkBotsChat"
            await msg.reply(err, quote=True)
            await self.client.send_message(
                self.LOG_CHAT,
                f"'#TooManyRequests \n\n**Info** : {resp} \n\n**User** : {msg.from_user.mention} [`{msg.from_user.id}`] \n\n**Supposed Pack** : t.me/addstickers/{e.pack}"
            )
        except AlreadyOccupied:
            await self.add_to_pack(params, file)
        except StickerPackInvalid:
            await self.new_pack(params, file)
        except StickersTooMuch:
            total_packs = await database.get('users', self.user_id, 'packs')
            if not total_packs:  # Just in Case
                total_packs = 1
            await self.status.edit('Oh. Your pack {} is full. Lemme create a new one for you :)'.format(total_packs))
            total_packs += 1
            pack_name = self.NEW_PACK_NAME.format(total_packs, self.user_id)
            params.update({'name': pack_name})
            params.update({'title': self.NEW_PACK_TITLE.format(total_packs)})
            await self.new_pack(params, file)
            await database.set('users',  self.user_id, {'packs': total_packs})
        except UnknownException as e:
            msg = self.message
            await msg.reply(self.ERROR)
            err = await self.client.send_message(
                self.LOG_CHAT,
                f"'#ERROR \n\n**Info** : {resp} \n\n**User** : {msg.from_user.mention} [`{msg.from_user.id}`] \n\n**Supposed Pack** : t.me/addstickers/{e.pack}"
            )
            await err.reply_document(self.output_file)
            await err.reply(f"PARAMS : {params} \n\nMETHOD : {method}")
            await msg.forward(self.LOG_CHAT, disable_notification=True)
            return False
        finally:
            if method == 'get':
                if resp['ok']:
                    return resp['result']['stickers'][-1]['file_id']
                else:
                    return False
        return True

    @staticmethod
    async def error(resp, pack_name):
        if not resp['ok']:
            desc = resp['description']
            if 'Too Many Requests' in desc:
                # print('Raise TooManyRequests')
                raise TooManyRequests(desc, pack_name)
            elif 'STICKERS_TOO_MUCH' in desc:
                # print('Raise StickersTooMuch')
                raise StickersTooMuch(desc, pack_name)
            elif 'STICKERSET_INVALID' in desc:
                # print('Raise StickerPackInvalid')
                raise StickerPackInvalid(desc, pack_name)
            elif 'name is already occupied' in desc:
                # print('Raise AlreadyOccupied')
                raise AlreadyOccupied(desc, pack_name)
            else:
                # print('Raise UnknownException')
                raise UnknownException(desc, pack_name)

    async def ffmpeg_error(self, stderr: str):
        print(stderr)
        msg = self.message
        await msg.reply(self.ERROR)
        await self.client.send_message(self.LOG_CHAT, f"#ERROR #FFMPEG \n\n{stderr} \n\n**User** : {msg.from_user.mention} [`{msg.from_user.id}`]")
        await msg.forward(self.LOG_CHAT, disable_notification=True)

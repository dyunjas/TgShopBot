from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

class TgSender:
    def __init__(self, token: str):
        self.bot = Bot(
            token=token,
            default=DefaultBotProperties(parse_mode=ParseMode.HTML, link_preview_is_disabled=True),
        )

    async def send_login_code(self, tg_id: int, code: str):
        await self.bot.send_message(
            chat_id=tg_id,
            text=(
                f"🔐 <b>Код для входа:</b> <code>{code}</code>\n\n"
                "Если вы не запрашивали - просто игнорируйте."
            ),
        )

    async def close(self):
        await self.bot.session.close()

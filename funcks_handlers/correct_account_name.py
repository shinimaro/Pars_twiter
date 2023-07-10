import string

from aiogram.filters import BaseFilter

from aiogram.types import Message
from databases.database import Database


async def correct_account(name: str):

    if name[0] != '@':
        return None
    name = name[1:]
    if len(name) <= 3 or ' ' in name:
        return None

    db = Database()
    await db.connect()
    stock_account = await db.stock_account('@' + name)
    await db.disconnect()

    if stock_account:
        return False

    for n in name:
        if n not in string.ascii_letters + '_' + string.digits:
            return None

    return True



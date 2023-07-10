import asyncio

from aiogram.utils.keyboard import InlineKeyboardBuilder as BD
from aiogram.types import InlineKeyboardButton as IB

from databases.database import Database
from wordbank.wordlist import WORDS_TASKS, BACK_LEXICON


async def tasks_list():
    set_tasks = BD()

    db = Database()

    await db.connect()
    tasks_dict = await db.task_list()

    for task_id in tasks_dict:
        words = []
        t = tasks_dict[task_id]
        price = f'🔥${await db.give_price(task_id)}р$ '

        # Эту часть стоит убрать, она считает общее количество постов
        posts = await db.give_posts(task_id)
        if posts == 1:
            posts = f' на пост'
        elif 1 < posts < 5:
            posts = f' на {posts} поста'
        elif posts >= 5:
            posts = f' на {posts} постов'


        if 'лайк' in t:
            if t.count('лайк') == 1:
                words.append('Лайк')
            elif 1 < t.count('лайк') < 5:
                words.append(f'{t.count("лайк")} лайка')
            elif t.count('лайк') >= 5:
                words.append(f'{t.count("лайк")} лайков')

        if 'ретвит' in t:
            if t.count('ретвит') == 1:
                if 'лайк' not in t:
                    words.append('Ретвит')
                else:
                    words.append('ретвит')
            elif 2 < t.count('ретвит') < 5:
                words.append(f'{t.count("ретвит")} ретвита')
            elif t.count('ретвит') >= 5:
                words.append(f'{t.count("лайк")} ретвитов')

        if 'коммент' in t:
            if t.count('коммент') == 1:
                if 'ретвит' not in t and 'лайк' not in t:
                    words.append('Коммент')
                else:
                    words.append('коммент')
            elif 2 < t.count('коммент') < 5:
                words.append(f'{t.count("коммент")} коммента')
            elif t.count('коммент') >= 5:
                words.append(f'{t.count("лайк")} комментов')

        set_tasks.row(
            IB(text=price + ', '.join(words) + posts, callback_data=f'task_{task_id}'),
            width=1
        )

    set_tasks.row(
        IB(text=BACK_LEXICON, callback_data='back_to_main_menu')
    )
    await db.disconnect()
    return set_tasks.as_markup()




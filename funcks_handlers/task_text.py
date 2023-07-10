from databases.database import Database
from wordbank.wordlist import WORDS_PERFORMANCE_TASK

async def task_text(tg_id, task_id=None):
    db = Database()
    await db.connect()
    doing_dict = await db.actions(task_id)
    accounts = await db.amount_accounts(tg_id)
    text = ''

    c = 0
    for i in doing_dict:
        list = []
        link = ''
        for j in doing_dict[i]:
            if j.startswith('https://'):
                link = j
                continue
            elif j == 'Лайк':
                list.append(j)
            elif j == 'ретвит':
                if 'Лайк' not in doing_dict[i]:
                    list.append(j.title())
                else:
                    list.append(j)
            elif j == 'коммент':
                if 'Лайк' not in doing_dict[i] and 'ретвит' not in doing_dict[i]:
                    list.append(j.title())
                else:
                    list.append(j)
        c += 1
        text += f'👉 {c}. {", ".join(list)} этого поста - {link}\n'
    text += '\n'

    if accounts == 1:
        main_text = WORDS_PERFORMANCE_TASK['main_text']['option_2']
    elif accounts > 1:
        main_text = WORDS_PERFORMANCE_TASK['main_text']['option_3']
        if task_id:
            quantity = await db.quantity_completed(tg_id, task_id)
            if quantity:
                if quantity == 1:
                    main_text += '\n\nТы уже выполнил это задание с 1 аккаунта'
                if quantity > 1:
                    main_text += '\n\nТы уже выполнил это задание с {0} аккаунтов'.format(quantity)
    else:
        main_text = WORDS_PERFORMANCE_TASK['main_text']['option_1']

    text += main_text
    await db.disconnect()
    return text




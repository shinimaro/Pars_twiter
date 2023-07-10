import asyncpg
import datetime
from config import load_config, Config

config: Config = load_config()

class Database:
    def __init__(self):
        self.host = config.database.db_host
        self.database = config.database.db_name
        self.user = config.database.db_user
        self.password = config.database.db_password
        self.pool = None

    async def connect(self):
        self.pool = await asyncpg.create_pool(
            host=self.host,
            database=self.database,
            user=self.user,
            password=self.password)

    async def disconnect(self):
        if self.pool:
            await self.pool.close()

    async def execute(self, query, *args):
        async with self.pool.acquire() as connection:
            return await connection.execute(query, *args)


    # Получить список всех действий для выполнения задания
    async def set_actions(self, url_id):
        async with self.pool.acquire() as connection:
            async with connection.transaction():
                actions = await connection.fetch('SELECT likeus, retweetus, commentus FROM twit_action WHERE url_id = $1 ', url_id)
                return actions

    # Взять цену за задание в таске
    async def give_price(self, task_id):
        async with self.pool.acquire() as connection:
            async with connection.transaction():
                price = await connection.fetchrow('SELECT price FROM tasks WHERE task_id = $1', task_id)
                if price is not None:
                    return price['price']
                else:
                    return 0

    # Запрос всех заданий, которые есть
    async def task_list(self):
        async with self.pool.acquire() as connection:
            async with connection.transaction():
                # Проверка на соответствие времени (если не время публиковаться, либо вышел срок, то убираем его из активных)
                await connection.execute("UPDATE tasks SET status = CASE WHEN CURRENT_TIMESTAMP > publish AND CURRENT_TIMESTAMP < ends_data THEN 'active' ELSE 'inactive' END")

                # Формирование тасков
                tasks = await connection.fetch("SELECT task_id, url_id FROM con_table WHERE task_id IN (SELECT task_id FROM tasks WHERE status = 'active') ORDER BY (SELECT price FROM tasks WHERE tasks.task_id = con_table.task_id) DESC")
                dictus = {}
                for record in tasks:
                    task_id = record["task_id"]
                    url_id = record["url_id"]
                    if task_id not in dictus:
                        dictus[task_id] = [url_id]
                    elif url_id not in dictus[task_id]:
                        dictus[task_id].append(url_id)

                general_dict = {}
                for num in dictus:
                    general_dict[num] = []
                    for n in dictus[num]:
                        for action in await self.set_actions(n):
                            if action['likeus']:
                                general_dict[num].append('лайк')
                            if action['retweetus']:
                                general_dict[num].append('ретвит')
                            if action['commentus']:
                                general_dict[num].append('коммент')


                return general_dict

    # Получить количество заданий в таске
    async def give_posts(self, task_id):
        async with self.pool.acquire() as connection:
            async with connection.transaction():
                posts = await connection.fetchrow('SELECT COUNT(url_id) as count FROM con_table WHERE task_id = $1', task_id)
                if posts is not None:
                    return posts['count']
                return 0

    # Получить количество аккаунтов пользователя
    async def amount_accounts(self, tg_id):
        async with self.pool.acquire() as connection:
            async with connection.transaction():
                accounts = await connection.fetchrow('SELECT COUNT(acc_name) as count FROM accounts WHERE user_id = (SELECT user_id FROM users WHERE tg_id = $1)', tg_id)
                return accounts['count']

    # Получить то, что нужно сделать с постом
    async def actions(self, task_id):
        async with self.pool.acquire() as connection:
            async with connection.transaction():
                actions = await connection.fetch('SELECT url_id FROM con_table WHERE task_id = $1 GROUP BY url_id', task_id)
                actions = [int(i['url_id']) for i in actions]
                dict_actions = {}
                for url_id in actions:
                    info_action = await connection.fetch('SELECT linker, likeus, retweetus, commentus FROM twit_action WHERE url_id = $1', url_id)
                    for i in info_action:
                        dict_actions[url_id] = [i['linker']]
                        if i['likeus']:
                            dict_actions[url_id].append('Лайк')
                        if i['retweetus']:
                            dict_actions[url_id].append('ретвит')
                        if i['commentus']:
                            dict_actions[url_id].append('коммент')

                return dict_actions

    # Функция, подсчитывающая, сколько раз уже человек выполнил задание
    async def quantity_completed(self, tg_id, task_id):
        async with self.pool.acquire() as connection:
            async with connection.transaction():
                quantity = await connection.fetchrow('SELECT COUNT(acc_name) as count FROM completed_tasks WHERE user_id = (SELECT user_id FROM users WHERE tg_id = $1) AND task_id = $2 GROUP BY user_id', tg_id, task_id)
                if quantity is not None:
                    return quantity['count']
                return False

    # Функция для подсчёта количества аккаунтов юзера
    async def quantity_accounts(self, tg_id):
        async with self.pool.acquire() as connection:
            async with connection.transaction():
                quantity = await connection.fetchrow('SELECT COUNT(acc_name) as count FROM accounts WHERE user_id = (SELECT user_id FROM users WHERE tg_id = $1)', tg_id)
                return quantity['count']


    # Функция для выгрузки всех аккаунтов юзера
    async def set_accounts(self, tg_id):
        async with self.pool.acquire() as connection:
            async with connection.transaction():
                accs = await connection.fetch('SELECT acc_name FROM accounts WHERE user_id = (SELECT user_id FROM users WHERE tg_id = $1) ORDER BY acc_name', tg_id)
                if accs is not None:
                    return accs
                return False

    # Функция для проверки на то, нет ли уже
    async def stock_account(self, account):
        async with self.pool.acquire() as connection:
            async with connection.transaction():
                accounts = await connection.fetchrow('SELECT acc_name FROM accounts WHERE acc_name = $1', account)
                if accounts:
                    return True
                return False

    # Функция для сбора всех действий на определённом таске
    async def viewing_task(self, task_id):
        async with self.pool.acquire() as connection:
            async with connection.transaction():
                result = await connection.fetch('SELECT linker, likeus, retweetus, commentus FROM twit_action WHERE url_id IN (SELECT url_id FROM con_table WHERE task_id = $1)', task_id)
                return result

    # Пользователь выполнил задание
    async def completed_task(self, tg_id, account, task_id, price):
        async with self.pool.acquire() as connection:
            async with connection.transaction():
                user_id = await connection.fetchrow('SELECT user_id FROM users WHERE tg_id = $1', tg_id)
                user_id = user_id['user_id']
                await connection.execute("INSERT INTO completed_tasks(user_id, acc_name, task_id) VALUES ($1, $2, $3)", user_id, account, task_id)
                await connection.execute("UPDATE users SET balance = balance + $1 WHERE tg_id = $2", price, tg_id)

    # Функуция для добавления нового аккаунт
    async def insert_account(self, tg_id, account):
        async with self.pool.acquire() as connection:
            async with connection.transaction():
                user_id = await connection.fetchrow('SELECT user_id FROM users WHERE tg_id = $1', tg_id)
                user_id = user_id['user_id']
                await connection.execute("INSERT INTO accounts(user_id, acc_name) VALUES ($1, $2)", user_id, account)

    # Проверка на то, что пользователь не выполнял этот таск с этого аккаунта
    async def check_account(self, account, task_id):
        async with self.pool.acquire() as connection:
            async with connection.transaction():
                result = await connection.fetchrow("SELECT acc_name FROM completed_tasks WHERE acc_name = $1 AND task_id = $2", account, task_id)
                if result is None:
                    return True
                return False

    # Взять все данные для профиля
    async def check_user(self, tg_id):
        async with self.pool.acquire() as connection:
            async with connection.transaction():
                balance = await connection.fetchrow("SELECT balance FROM users WHERE tg_id = $1", tg_id)
                tasks = await connection.fetchrow('SELECT COUNT(user_id) as count FROM completed_tasks WHERE user_id = (SELECT user_id FROM users WHERE tg_id = $1)', tg_id)
                accounts = await connection.fetchrow('SELECT COUNT(acc_name) as count FROM accounts WHERE user_id = (SELECT user_id FROM users WHERE tg_id = $1)', tg_id)
                list = [0, 0, 0]
                if balance is not None:
                    list[0] = balance['balance']
                if tasks is not None:
                    list[1] = tasks['count']
                if accounts is not None:
                    list[2] = accounts['count']
                return list

    # Проверка, есть ли пользователь в базе данных, если нет, то добавляем
    async def user_in_database(self, tg_id, username):
        async with self.pool.acquire() as connection:
            async with connection.transaction():
                result = await connection.fetchrow("SELECT tg_id FROM users WHERE tg_id = $1", tg_id)
                if result is not None:
                    return True
                await connection.execute("INSERT INTO users(tg_id, tg_name, balance) VALUES ($1, $2, 0)", tg_id, username)





























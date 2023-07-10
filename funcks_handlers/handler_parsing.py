import asyncio
import os
import pickle
import re

from config import load_config
from databases.database import Database
from funck_parsers.parsing_user import parsing_user
from funck_parsers.pasing_twit import parsing_tweet
from start_for_webdriver.webdriver import webdriver
from start_for_webdriver.login_in_twitter import login_in_twitter

config = load_config()

async def parser(task_id, user):
    db = Database()
    await db.connect()
    result = await db.viewing_task(task_id)
    await db.disconnect()
    actions = {'like': [], 'retweet': [], 'comment': []}
    # Собираем все необходимые действия
    for res in result:
        link = res['linker']
        if res['likeus']:
            # Сокращаем ссылку, убирая всё лишнее
            actions['like'].append(re.sub(r'(\d+)(.*)', r'\1', link))
        if res['retweetus']:
            actions['retweet'].append(re.sub(r'(\d+)(.*)', r'\1', link))
        if res['commentus']:
            actions['comment'].append(link)

    driver = await webdriver()
    # Открываем драйвер
    driver.get('https://twitter.com/')
    for cookie in pickle.load(open(f'./cookies/{config.twitter_login.tw_login}_cookies', 'rb')):
        driver.add_cookie(cookie)

    # Запускаем проверку
    for action in actions:
        act = actions[action]
        if action == 'comment':
            for a in act:
                if not await parsing_tweet(driver, a, user):
                    driver.quit()
                    return False
        # Если только 1 действие, то просматриваем твит
        elif len(act) == 1:
            if action == 'like':
                act[0] += '/likes'
            elif action == 'retweet':
                act[0] += '/retweets'
            if not await parsing_tweet(driver, *act, user):
                driver.quit()
                return False
        # Если 2 действия, то формируем нужный словарь и просматриваем пользователя
        elif len(act) > 1:
            user_link = 'https://twitter.com/' + user[1:]
            dict = {}
            # Составляем словарь
            for a in act:
                userus = '@' + re.search(r"https://twitter.com/([^/]+)", a).group(1)
                if userus not in dict:
                    dict[userus] = []
                dict[userus].append(a)
            # Определяем, куда этот словарь засунуть
            if action == 'like':
                if not await parsing_user(driver, user_link, links_likes=dict):
                    # Если не получилось, то продолжаем через просмотр твита
                    for dic in dict:
                        for d in dict[dic]:
                            if not await parsing_tweet(driver, d + '/likes', user):
                                driver.quit()
                                return False
            else:
                if not await parsing_user(driver, user_link, links_retweet=dict):
                    for dic in dict:
                        for d in dict[dic]:
                            if not await parsing_tweet(driver, d + '/retweets', user):
                                driver.quit()
                                return False




    driver.quit()
    return True

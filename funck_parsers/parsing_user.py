from asyncio import sleep

from msedge.selenium_tools import Edge
from selenium.common.exceptions import StaleElementReferenceException, NoSuchElementException, WebDriverException


# Эта функция уже может посмотреть сразу и лайки и ретвиты у пользователя на странице
# Сюда будет передаваться словарь, содержащий юзернейм пользователя (ключ), на которого нужно было сделать реакция
# И значения - ссылка на твит, если есть изображение, если его нет, то начальный текст. Если несколько ссылок от одного юзера, то они будут в списке
async def parsing_user(driver: Edge, user_link: str, links_retweet: dict[str, str]=None, links_likes: dict[str, str]=None):

    flag_retweet = False
    flag_likes = False


    if links_retweet:
        driver.get(user_link)
        await sleep(2)


        # while not flag_retweet:
        for i in range(3):
            # Определяем по маленькому списку, если вдруг будет что удалить
            keys_delete: str = None
            value_index_delete = []
            set_name = set()

            # Находим твит
            blocks = driver.find_elements_by_xpath('//article[@data-testid="tweet"]')
            for block in blocks:
                try:
                    # Провеяем, ретвит ли это или просто обычный пост
                    retweet_verif = (block.find_elements_by_xpath('.//div[@data-testid="socialContext"]') or block.find_element_by_xpath('.//span[@data-testid="socialContext"]'))
                    if retweet_verif:
                        # Находим имя пользователя
                        name = block.find_element_by_xpath('.//a[starts-with(@href, "/") and @tabindex="-1"]')
                        name = '@' + name.get_attribute("href")[20:]
                        set.add(name)

                        # Проверяем в цикле, тот ли это пользователь, которого нужно ретвитнуть
                        if name in links_retweet:
                            for key, value in links_retweet.items():
                                if key == name:
                                    # Смотрим, что нам нужно вообще найти, если это просто текст со ссылкой, то идём далее
                                    if isinstance(value, str):
                                        if value.startswith('https://twitter.com/'):
                                            # Проверяем, есть ли изображение в посте
                                            if block.find_element_by_xpath('.//div[@data-testid="tweetPhoto"]') and not block.find_elements_by_xpath('.//div[@data-testid="videoComponent"]'):
                                                # Если изображение, то находим ссылку
                                                element = block.find_element_by_xpath(f'.//a[contains(@href, "/{name[1:]}/status")]')
                                                link = element.get_attribute('href')
                                                # Если ссылка была найдена, то сравниваем, равна ли она значению
                                                if link.startswith(value):
                                                    # Если ссылка была найдена, то добавляем элемент к удалённым
                                                    keys_delete = key
                                                    break
                                            else:
                                                pass
                                        # Если же просто текст, идём здесь
                                        else:
                                            tweet_text = block.find_element_by_xpath('.//div[@data-testid="tweetText"]')
                                            tweet_text = tweet_text.find_element_by_xpath('.//span[normalize-space(text())]').text
                                            if tweet_text == value:
                                                keys_delete = key
                                                break


                                    # Если же это список, то идём по новой ветке
                                    elif isinstance(value, list) and len(value) > 0:
                                        for i in range(len(value)):
                                            # Если это ссылка
                                            if value[i].startswith('https://twitter.com/'):
                                                # Проверяем, есть ли изображение в посте
                                                if block.find_element_by_xpath('.//div[@data-testid="tweetPhoto"]') and not block.find_elements_by_xpath('.//div[@data-testid="videoComponent"]'):
                                                    # Если это изображение, то находим ссылку
                                                    element = block.find_element_by_xpath(f'.//a[contains(@href, "/{name[1:]}/status")]')
                                                    link = element.get_attribute('href')
                                                    # Если ссылка была найдена, то сравниваем, равна ли она значению
                                                    if link.startswith(value[i]):
                                                        # Если ссылка была найдена, то удаляем элемент
                                                        value_index_delete.append(key)
                                                        value_index_delete.append(i)
                                                        break
                                            # Если это не ссылка, а текст
                                            else:
                                                tweet_text = block.find_element_by_xpath('.//div[@data-testid="tweetText"]')
                                                tweet_text = tweet_text.find_element_by_xpath('.//span[normalize-space(text())]').text
                                                if tweet_text == value[i]:
                                                    value_index_delete.append(key)
                                                    value_index_delete.append(i)
                                                    break
                            # Проверка на то, что в итоге будем удалять
                            if len(value_index_delete) == 2:
                                links_retweet[value_index_delete[0]].pop(value_index_delete[1])
                                if not links_retweet[value_index_delete[0]]:
                                    links_retweet.pop(value_index_delete[0])
                            elif keys_delete:
                                links_retweet.pop(keys_delete)

                            if not links_retweet:
                                flag_retweet = True
                                break

                            keys_delete = None
                            value_index_delete.clear()

                except (StaleElementReferenceException, NoSuchElementException, WebDriverException) as e:
                    pass

            # Если юзеров никаких селениум не собрал, то, скорее всего, нет никаких ретвитов у пользователя
            if not set_name:
                 return False

            if flag_retweet and not links_likes:
                return True
            elif flag_retweet or not links_retweet:
                break
            else:
                driver.execute_script(f"window.scrollBy(0, 2000);")
                await sleep(1)

        # Если в итоге так ничего и не нашли, хотя было задано значение
        if not flag_retweet and links_retweet:
            return False




    # Если есть то, что нужно проверить на лайки
    if links_likes:
        driver.get(user_link + '/likes')
        await sleep(1.5)
        keys_delete: str = None
        value_index_delete = []
        all_set_likes = set()
        stoper = 0

        # while not flag_likes:
        for i in range(3):
            set_likes = set()
            # Находим твит
            blocks = driver.find_elements_by_xpath('//article[@data-testid="tweet"]')
            for block in blocks:
                try:
                    name = block.find_element_by_xpath('.//a[starts-with(@href, "/") and @tabindex="-1"]')
                    name = '@' + name.get_attribute("href")[20:]
                    set_likes.add(name)
                    # Проверяем в цикле, тот ли это пользователь, которого нужно лайкнуть
                    if name in links_likes:
                        for key, value in links_likes.items():
                            if key == name:
                                # Смотрим, что нам нужно вообще найти, если это просто текст со ссылкой, то идём далее
                                if isinstance(value, str):
                                    if value.startswith('https://twitter.com/'):
                                        # Проверяем, есть ли изображение в посте
                                        if block.find_element_by_xpath('.//div[@data-testid="tweetPhoto"]') and not block.find_elements_by_xpath('.//div[@data-testid="videoComponent"]'):
                                            # Если изображение, то находим ссылку
                                            element = block.find_element_by_xpath(f'.//a[contains(@href, "/{name[1:]}/status")]')
                                            link = element.get_attribute('href')
                                            # Если ссылка была найдена, то сравниваем, равна ли она значению
                                            if link.startswith(value):
                                                # Если ссылка была найдена, то добавляем ключ
                                                keys_delete = key
                                                break
                                    # Если же просто текст, идём здесь
                                    else:
                                        tweet_text = block.find_element_by_xpath('.//div[@data-testid="tweetText"]')
                                        tweet_text = tweet_text.find_element_by_xpath('.//span[normalize-space(text())]').text
                                        if tweet_text == value:
                                            keys_delete = key
                                            break

                                # Если же это список, то идём по новой ветке
                                elif isinstance(value, list) and len(value) > 0:
                                    for i in range(len(value)):
                                        # Если это ссылка
                                        if value[i].startswith('https://twitter.com/'):
                                            # Проверяем, есть ли изображение в посте
                                            if block.find_element_by_xpath('.//div[@data-testid="tweetPhoto"]') and not block.find_elements_by_xpath('.//div[@data-testid="videoComponent"]'):
                                                # Если это изображение, то находим ссылку
                                                element = block.find_element_by_xpath(f'.//a[contains(@href, "/{name[1:]}/status")]')
                                                link = element.get_attribute('href')
                                                # Если ссылка была найдена, то сравниваем, равна ли она значению
                                                if link.startswith(value[i]):
                                                    # Если ссылка была найдена, то удаляем элемент
                                                    value_index_delete.append(key)
                                                    value_index_delete.append(i)
                                                    break
                                            else:
                                                pass
                                        # Если это не ссылка, а текст
                                        else:
                                            tweet_text = block.find_element_by_xpath('.//div[@data-testid="tweetText"]')
                                            tweet_text = tweet_text.find_element_by_xpath('.//span[normalize-space(text())]').text
                                            if tweet_text == value[i]:
                                                value_index_delete.append(key)
                                                value_index_delete.append(i)
                                                break
                        # Проверка на то, что в итоге будем удалять
                        if len(value_index_delete) == 2:
                            links_likes[value_index_delete[0]].pop(value_index_delete[1])
                            if not links_likes[value_index_delete[0]]:
                                links_likes.pop(value_index_delete[0])
                        elif keys_delete:
                            links_likes.pop(keys_delete)

                        if not links_likes:
                            flag_likes = True
                            break

                        keys_delete = None
                        value_index_delete.clear()

                except (StaleElementReferenceException, NoSuchElementException, WebDriverException):
                    continue

            # Если юзеров никаких селениум не собрал, то, скорее всего, нет никаких лайков у пользователя
            if not set_likes:
                return False

            if flag_likes or not links_likes:
                return True
            elif flag_likes and links_retweet:
                return False
            else:
                driver.execute_script(f"window.scrollBy(0, 2000);")
                await sleep(1)

            check = set_likes.difference(all_set_likes)
            if len(check) == 0:
                stoper += 1
                if stoper == 2:
                    return False
            all_set_likes.update(set_likes)

    # Если в словарях ещё есть значения
    if links_retweet or links_likes:
        return False

from asyncio import sleep
from typing import Set, Union

from msedge.selenium_tools import Edge
from selenium.common.exceptions import StaleElementReferenceException, NoSuchElementException, WebDriverException
from selenium.webdriver.common.keys import Keys


async def parsing_tweet(driver: Edge, link: str, user: str = None) -> Union[Set[str], bool]:

    # Проверяем, что нужно проверять в функции, лайки или ретвиты
    search: str

    if link.endswith('likes'):
        search = 'Понравилось'
    elif link.endswith('retweets'):
        search = 'Ретвитнул(а)'
    elif link.endswith('with_comments'):
        search = None
    else:
        search = 'Показать больше ответов'

    # Проверка на собачку перед юзером
    if user and not user.startswith('@'):
        user = '@' + user

    # Доп текст, нужный мне
    dop_text = 'Показать дополнительные ответы, включая те, которые могут содержать материалы оскорбительного характера'

    # Открываем ссылку
    driver.get(link)
    await sleep(2)
    if search == 'Показать больше ответов':
        await sleep(1)

    # Расставляем нужные переменные перед циклом
    flag_for_while = True
    if user:
        flag_to_check = False
    else:
        flag_to_check = None
    set_all_users = set()

    rangus = 3
    if search == 'Показать больше ответов':
        rangus = 8
    # Делаем цикл
    for i in range(rangus):
    # while flag_for_while
        set_users = set()

        # Находим все блоки, содержащие информацию о пользователе
        user_blocks = driver.find_elements_by_xpath('//div[@data-testid="cellInnerDiv"]')
        # Проходимся по каждому
        for user_block in user_blocks:
            try:
                # Ищем нужную строчку в блоке
                element = user_block.find_element_by_xpath('.//a[starts-with(@href, "/")]')
                name = '@' + element.get_attribute("href")[20:]
                # Проверка юзера, если он был задан
                if user and user == name:
                    flag_to_check = True
                    return flag_to_check
                # Нажатие на кнопки для открытия всех комментов
                if search == 'Показать больше ответов':
                    try:
                        button = driver.find_element_by_xpath(f'.//span[contains(text(), "{search}")]')
                        button.click()
                        button = driver.find_element_by_xpath(f'.//span[contains(text(), "{dop_text}")]')
                        button.click()
                    except (StaleElementReferenceException, NoSuchElementException):
                        pass
                # Добавляем пользователя в множество
                set_users.add(name)
            # Обходим ошибки на то, если элементы повторяются
            except (StaleElementReferenceException, NoSuchElementException, WebDriverException):
                continue


        # Проверка на то, собрались ли новые юзеры
        check = set_users.difference(set_all_users)

        # Если пользователи не собрались, то крутим ещё раз вниз
        if len(check) == 0:
            for _ in range(3):
                # Жмякнуть на кнопочку, если смотрим ретвиты или лайки
                if search == 'Понравилось' or search == 'Ретвитнул(а)':
                    title = driver.find_element_by_xpath(f'.//span[contains(text(), "{search}")]')
                    title.click()
                # Опускаемся
                html = driver.find_element_by_tag_name('html')
                html.send_keys(Keys.END)

                # Повторная проверка всех элементов
                user_blocks = driver.find_elements_by_xpath('//div[@data-testid="cellInnerDiv"]')
                for user_block in user_blocks:
                    try:
                        element = user_block.find_element_by_xpath('.//a[starts-with(@href, "/")]')
                        name = '@' + element.get_attribute("href")[20:]
                        if user and user == name:
                            flag_to_check = True
                            return flag_to_check
                        if search == 'Показать больше ответов':
                            try:
                                button = driver.find_element_by_xpath(f'.//span[contains(text(), "{search}")]')
                                button.click()
                                button = driver.find_element_by_xpath(f'.//span[contains(text(), "{dop_text}")]')
                                button.click()
                            except (StaleElementReferenceException, NoSuchElementException):
                                pass
                        set_users.add(name)
                    except (StaleElementReferenceException, NoSuchElementException, WebDriverException):
                        continue
                # Проверка на то, изменилось ли что-то
                check = set_users.difference(set_all_users)
                if len(check) != 0:
                    break
                await sleep(1.5)
                # Доп. время на подгрузку страницы, если парсим комменты
                if search == 'Показать больше твитов':
                    await sleep(1)

            # Если цикл закончился, а ничего так и не прогрузилось, то цикл заканчивается
            else:
                flag_for_while = False


        # Если цикл работает, то сохраняем пользователей, а также крутим страницу вниз
        if flag_for_while:
            set_all_users.update(set_users)

            # Жмякнуть на кнопочку, если смотрим ретвиты или лайки
            if search == 'Понравилось' or search == 'Ретвитнул(а)':
                title = driver.find_element_by_xpath(f'.//span[contains(text(), "{search}")]')
                title.click()

            # Если мы смотрим цитаты, то опускаемся на чуть-чуть
            if not search or search == 'Показать больше ответов':
                driver.execute_script(f"window.scrollBy(0, 1800);")
                await sleep(1)
            # Если нет, то ныряем далее
            else:
                # Если отпарсили более 50 человек, то нафек это
                if len(set_all_users) >= 30:
                    return False
                # Опуститься чуть ниже
                html = driver.find_element_by_tag_name('html')
                html.send_keys(Keys.END)
                await sleep(0.7)

            # Доп. время на подгрузку страницы, если парсим комменты
            if search == 'Показать больше твитов':
                await sleep(1)

    # После цикла проверяем, если был задан юзер, то проверяем то, есть ли он, если не был, то показываем всё, что собрали
    if user:
        return flag_to_check
    return set_all_users

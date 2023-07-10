from selenium.webdriver import Chrome, ChromeOptions
from selenium.webdriver.common.proxy import Proxy, ProxyType



async def webdriver():
    # Установка прокси
    proxy = Proxy()
    proxy.proxyType = ProxyType.MANUAL
    proxy.http_proxy = '45.118.251.124' + ':' + str(8000)

    # Установка вебдрайвера и присоединение прокси
    options = ChromeOptions()
    options.add_argument('--proxy-server=http://{0}'.format(proxy.http_proxy))
    # Отключение информации о том, что это вебдрайвер
    options.add_argument('--disable-blink-features=AutomationControlled')
    # Включение фонового режима (чтобы вебдрайвер не открывался, это даёт прибавку к оперативке)
    options.headless = True

    # Установка вебдрайвера и присоединение прокси
    driver = Chrome(options=options,
                           executable_path='D:\\Development tools\\Driver_for_selenuim\\chromedriver.exe')
    return driver

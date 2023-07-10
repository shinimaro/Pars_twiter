from dataclasses import dataclass
from environs import Env


@dataclass
class TgBot:
    token: str
    support_name: str
    admins: list[str]
    superadmin: str

@dataclass
class DatabaseConfig:
    db_host: str
    db_user: str
    db_password: str
    db_name: str

@dataclass
class Proxy:
    proxy_host: str
    proxy_port: int

@dataclass
class TwitterLogin:
    tw_login: str
    tw_password: str

@dataclass
class Config:
    tg_bot: TgBot
    database: DatabaseConfig
    proxy: Proxy
    twitter_login: TwitterLogin

def load_config(path: str | None = None) -> Config:
    env = Env()
    env.read_env(path)
    return Config(tg_bot=(TgBot(token=env('BOT_TOKEN'),
                                support_name=env('SUPPORT_NAME'),
                                admins=list(map(int, env.list('ADMIN_IDS'))),
                                superadmin=env('SUPERADMIN_ID'))),
                  database=(DatabaseConfig(db_host=env('HOST'),
                                           db_user=env('USER'),
                                           db_password=env('PASSWORD'),
                                           db_name=env('DB_NAME'))),
                  proxy=(Proxy(proxy_host=env('PROXY_HOST'),
                               proxy_port=int(env('PROXY_PORT')))),
                  twitter_login=(TwitterLogin(tw_login=env('TWITTER_LOGIN'),
                                              tw_password=env('TWITTER_PASSWORD'))))





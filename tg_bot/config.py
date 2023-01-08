from dataclasses import dataclass
from environs import Env


@dataclass
class TgBot:
    token: str
    use_redis: bool


@dataclass
class Db:
    host: str
    password: str
    user: str
    database: str
    port: str

@dataclass
class Qiwi:
    token: str
    qiwi_pub_key: str
    qiwi_sec_key: str
    qiwi_phone: str

@dataclass
class Misc:
    channel_id: str
    min_payment_value: int
    ru_card: str
    ua_card: str
    phone: str
    other_params: str = None


@dataclass
class Config:
    bot: TgBot
    db: Db
    qiwi: Qiwi
    misc: Misc


def load_config(path: str = None):
    env = Env()
    env.read_env(path)

    return Config(
        bot=TgBot(
            token=env.str("BOT_TOKEN"),
            use_redis=env.bool("USE_REDIS"),
        ),
        db=Db(
            host=env.str("DATABASE_HOST"),
            password=env.str("DATABASE_PASSWORD"),
            user=env.str("DATABASE_USER"),
            database=env.str("DATABASE_NAME"),
            port=env.str("DATABASE_PORT"),
        ),
        qiwi=Qiwi(
            token=env.str("QIWI_TOKEN"),
            qiwi_pub_key=env.str("QIWI_PUB_KEY"),
            qiwi_sec_key=env.str("QIWI_SEC_KEY"),
            qiwi_phone=env.str("QIWI_WALLET"),
        ),
        misc=Misc(
            channel_id=env.str("CHANNEL_ID"),
            min_payment_value=env.int("MIN_PAYMENT_VALUE"),
            ua_card=env.str("UA_CARD"),
            ru_card=env.str("RUS_CARD"),
            phone=env.str("QIWI_WALLET"),
        )
    )

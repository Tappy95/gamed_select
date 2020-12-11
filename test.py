import random
import time

from datetime import datetime, timedelta
import pymysql
from sqlalchemy import create_engine, select, and_, update
from sqlalchemy.dialects.mysql import insert
import csv
from config import *
from models.bzly import GameList, GameRechange
from utils.util import serialize
import sys

sys.setrecursionlimit(1000000)

engine = create_engine(
    SQLALCHEMY_DATABASE_URI,
    pool_pre_ping=SQLALCHEMY_POOL_PRE_PING,
    echo=SQLALCHEMY_ECHO,
    pool_size=SQLALCHEMY_POOL_SIZE,
    max_overflow=SQLALCHEMY_POOL_MAX_OVERFLOW,
    pool_recycle=SQLALCHEMY_POOL_RECYCLE,
)


def read_csv_save_rechange():
    with open("./results/player_today.txt", "r") as reader:
        reader = reader.readlines()

        # 建立空字典
        results = []
        for item in reader:
            result = eval(item)
            result['games'] = str(result.pop('task'))
            result['id'] = result.pop('people_id')
            # result['update_time'] = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
            result['update_time'] = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
            results.append(result)

        with engine.connect() as conn:
            insert_stmt = insert(GameRechange)
            on_duplicate_key_stmt = insert_stmt.on_duplicate_key_update(
                id=insert_stmt.inserted.id,
                games=insert_stmt.inserted.games,
                update_time=insert_stmt.inserted.update_time
            )
            conn.execute(on_duplicate_key_stmt, results)
            # result = {
            #     "name": item[0],
            #     "game_id": "",
            #     "platform": item[4],
            #     "platform_id": item[5],
            #     "recharge10_rebate": float(item[1]),
            #     "recharge_point": int(item[2]),
            #     "loss": float(item[3]),
            #     "weight": 1,
            # }
    #         results.append(result)
    # with engine.connect() as conn:
    #     conn.execute(insert(GameList).values(results))


def test_time_filter():
    now = datetime.now()
    with engine.connect() as conn:
        select_before_games = conn.execute(select([GameRechange]).where(
            and_(
                GameRechange.update_time >= now - timedelta(days=7) - timedelta(hours=now.hour, minutes=now.minute,
                                                                                seconds=now.second,
                                                                                microseconds=now.microsecond),
                GameRechange.update_time != now - timedelta(hours=now.hour, minutes=now.minute, seconds=now.second,
                                                            microseconds=now.microsecond)
            )
        )).fetchall()
        print(select_before_games)


def read_day_csv():
    with open('./results/players_3.csv', 'r') as csv_obj:
        reader = csv.reader(csv_obj)
        results = []
        for idx, row in enumerate(reader):
            if not row[0]:
                break
            if idx >= 1:
                result = {}
                result['id'] = row.pop(0)
                the_list = [row[i:i + 2] for i in range(0, len(row), 2)]
                games = []
                for i in the_list:
                    if not i[0]:
                        break
                    games.append({"name": i[0], "platform": i[1]})
                result['games'] = str(games)
                # result['update_time'] = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
                result['update_time'] = datetime.now().strftime("%Y-%m-%d")
                results.append(result)
        print(results)
        with engine.connect() as conn:
            insert_stmt = insert(GameRechange)
            on_duplicate_key_stmt = insert_stmt.on_duplicate_key_update(
                id=insert_stmt.inserted.id,
                games=insert_stmt.inserted.games,
                update_time=insert_stmt.inserted.update_time
            )
            conn.execute(on_duplicate_key_stmt, results)


if __name__ == '__main__':
    # read_csv_save_rechange()
    # test_time_filter()
    read_day_csv()

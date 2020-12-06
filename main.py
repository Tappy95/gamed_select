import random
import time

from datetime import datetime, timedelta
import pymysql
from sqlalchemy import create_engine, select, and_, update
from sqlalchemy.dialects.mysql import insert
import csv
from config import *
from models.bzly import GameList
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


def read_csv():
    results = []

    with open("./游戏表.csv", "r") as reader:
        csv_reader = csv.reader(reader)

        # 建立空字典
        for item in csv_reader:
            result = {
                "name": item[0],
                "game_id": "",
                "platform": item[4],
                "platform_id": item[5],
                "recharge10_rebate": float(item[1]),
                "recharge_point": int(item[2]),
                "loss": float(item[3]),
                "weight": 1,
            }
            results.append(result)
    with engine.connect() as conn:
        conn.execute(insert(GameList).values(results))

    # print(result)


class Caculate_games:
    def __init__(self, worker, game_list, people_count=60, people_games=4, dy_p=25, ibx_p=25, jxw_p=25, xw_p=25):
        self.worker = worker
        self.people_count = people_count
        self.people_games = people_games
        self.dy_p = dy_p
        self.ibx_p = ibx_p
        self.jxw_p = jxw_p
        self.xw_p = xw_p
        self.dy_games = [game for game in game_list if game['platform_id'] == 11]
        self.ibx_games = [game for game in game_list if game['platform_id'] == 9]
        self.jxw_games = [game for game in game_list if game['platform_id'] == 10]
        self.xw_games = [game for game in game_list if game['platform_id'] == 6]
        self.platform_games = {
            "dy": self.dy_games,
            "ibx": self.ibx_games,
            "jxw": self.jxw_games,
            "xw": self.xw_games,
        }
        self.platform_games_count = {
            "多游": 0,
            "爱变现": 0,
            "聚享玩": 0,
            "享玩": 0,
        }
        self.total_game = self.people_count * self.people_games * self.worker
        for value in self.platform_games.values():
            add_list = []
            for game in value:
                if game['weight'] > 1:
                    for i in range(game['weight'] - 1):
                        add_list.append(game)
            value.extend(add_list)
            value = sorted(value, key=lambda k: k['name'],
                           reverse=False)
            value = sorted(value, key=lambda k: k['loss'],
                           reverse=False)

    def gen_platform_count(self):
        dy_count = int(self.total_game * (self.dy_p / 100))
        ibx_count = int(self.total_game * (self.ibx_p / 100))
        jxw_count = int(self.total_game * (self.jxw_p / 100))
        xw_count = int(self.total_game * (self.xw_p / 100))
        return {
            "dy": dy_count,
            "jxw": jxw_count,
            "ibx": ibx_count,
            "xw": xw_count,
        }

    def add_game_list_to_platform(self, results, platform_games, aim_count):
        if len(results) >= aim_count:
            return results[:aim_count]
        else:
            results.extend(platform_games)
            return self.add_game_list_to_platform(results, platform_games, aim_count)

    def gen_all_games(self):
        platform_game_detail = {}
        plat_game_count = self.gen_platform_count()
        for key, game_count in plat_game_count.items():
            platform_game_detail[key] = self.add_game_list_to_platform([], self.platform_games[key], game_count)
        self.platform_games_count = {
            "多游": len(platform_game_detail['dy']),
            "爱变现": len(platform_game_detail['ibx']),
            "聚享玩": len(platform_game_detail['jxw']),
            "享玩": len(platform_game_detail['xw']),
        }
        return platform_game_detail

    def add_task_to_people(self, people_tasks, all_games):
        all_games_count = {}
        is_deny = 1
        same_counts = 0
        last_counts = 0
        while all_games:
            if last_counts == len(all_games):
                same_counts += 1
            if same_counts >= 5 and is_deny:
                is_deny = 0
                print("----------打开平台限制")
            last_counts = len(all_games)
            if len(all_games) <= 2 and not is_deny:
                return people_tasks, all_games_count, self.platform_games_count
            print(len(all_games))
            random.shuffle(all_games)
            the_game = all_games.pop(0)
            is_add = 0
            for the_people in people_tasks:
                if len(the_people['task']) >= self.people_games:
                    continue
                for its_game in the_people['task']:
                    if its_game['platform_id'] == the_game['platform_id'] and is_deny:
                        break
                    if its_game['name'] == the_game['name']:
                        break
                else:
                    the_people['task'].append(the_game)
                    is_add = 1
                    break
            if is_add == 0:
                all_games.append(the_game)
            else:
                # print("加入成功")
                the_key = the_game['platform'] + '-' + the_game['name']
                if the_key in all_games_count:
                    all_games_count[the_key] += 1
                else:
                    all_games_count[the_key] = 1
        return people_tasks, all_games_count, self.platform_games_count

    def gen_people_tasks(self):
        people_task = []
        for i in range(self.people_count * self.worker):
            task = {
                "people_id": i + 1,
                "task": []
            }
            people_task.append(task)
        all_games = []
        for value in self.gen_all_games().values():
            all_games.extend(value)
        random.shuffle(all_games)
        return self.add_task_to_people(people_task, all_games)


def write_csv():
    with open('./results/player_today.txt', 'r') as file_obj:
        for row in file_obj.readlines():
            # print(row)
            the_json = eval(row)
            with open('./results/players/player_{}.csv'.format(the_json['people_id']), 'w') as write_obj:
                writer = csv.writer(write_obj)

                # 先写入columns_name
                writer.writerow(["游戏名", "游戏id", "平台", '平台Id', '充10返利', '起充点', '亏损'])
                # 写入多行用writerows
                results = [
                    [task['name'], task['game_id'], task['platform'], task['platform_id'], task['recharge10_rebate'],
                     task['recharge_point'], task['loss']] for task in the_json['task']]
                writer.writerows(results)


def run(worker=1, people_count=60, people_games=4, dy_p=25, ibx_p=25, jxw_p=25, xw_p=25):
    with engine.connect() as conn:
        select_game_list = select([GameList])
        cur = conn.execute(select_game_list)
        rec = cur.fetchall()
        game_list = serialize(cur, rec)
        c_game = Caculate_games(
            worker=worker,
            game_list=game_list,
            people_count=people_count,
            people_games=people_games,
            dy_p=dy_p,
            ibx_p=ibx_p,
            jxw_p=jxw_p,
            xw_p=xw_p
        )
        results, all_games_count, platform_games_count = c_game.gen_people_tasks()
        print(platform_games_count)
        with open('./results/games_count.csv', 'w') as count_obj:
            writer_count = csv.writer(count_obj)
            writer_count.writerow(["游戏", "平台", "总数"])
            # 写入多行用writerows
            csv_list = []
            for key, count in all_games_count.items():
                list1 = key.split('-')
                csv_list.append([list1[1], list1[0], count])
            csv_list = sorted(csv_list, key=lambda k: k[1],reverse=False)
            writer_count.writerows(csv_list)
        with open('./results/player_today.txt', 'w') as file_obj:
            for result in results:
                # result = str(result).replace('name', '游戏名').replace('platform','平台').replace('recharge10_rebate', '充10返现').replace('loss','亏损').replace('weight', '权重').replace('recharge_point', '起充点')
                result = str(result)
                file_obj.write(result + '\n')
            for i in range(worker):
                with open('./results/players_{}.csv'.format(i + 1), 'w') as write_obj:
                    writer = csv.writer(write_obj)
                    writer.writerow(
                        ["用户id", "游戏1", "平台1", "游戏2", "平台2", "游戏3", "平台3", "游戏4", "平台4", "游戏5", "平台5", "游戏6", "平台6",
                         "游戏7", "平台7", "游戏8", "平台8", ])
                    # 写入多行用writerows
                    csv_list = []
                    for p_info in results[i * people_count:(i + 1) * people_count]:
                        csv_item = [p_info['people_id']]
                        for task in p_info['task']:
                            csv_item.append(task['name'])
                            csv_item.append(task['platform'])
                        csv_list.append(csv_item)

                    writer.writerows(csv_list)

        # write_csv()


if __name__ == '__main__':
    print("---------请输入必要参数-------")
    worker = int(input("请输入分配人数:"))
    people_count = int(input("请输入player人数(每人分配账号数):"))
    game_count = int(input("请输入单个player游戏数目:"))
    jxw_p = int(input("请输入聚享玩占比(0-100):"))
    xw_p = int(input("请输入享玩占比(0-100):"))
    dy_p = int(input("请输入多游占比(0-100):"))
    ibx_p = int(input("请输入爱变现占比(0-100):"))
    print("-----------------------------")
    run(worker, people_count, game_count, dy_p, ibx_p, jxw_p, xw_p)
    print('导出文件目录为根目录下的results')
    input("输入任意键退出")
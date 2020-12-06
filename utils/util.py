
# 数据库序列化器
import decimal
from datetime import datetime


def serialize(cursor, records):
    row_info, list_info = {}, []
    for row in records:
        for key in cursor.keys():
            if isinstance(row[key], datetime):
                row_info[key] = row[key].strftime("%Y-%m-%d")
            elif isinstance(row[key], decimal.Decimal):
                row_info[key] = round(float(row[key]), 2)
            else:
                row_info[key] = row[key]
        list_info.append(row_info)
        row_info = {}
    return list_info
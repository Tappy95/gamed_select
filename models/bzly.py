# coding: utf-8
from sqlalchemy import Column, DECIMAL, Date, DateTime, Float, Index, String, Table, Text, text
from sqlalchemy.dialects.mysql import BIGINT, INTEGER, TINYINT, VARCHAR
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()
metadata = Base.metadata


class GameList(Base):
    __tablename__ = 'game_list'

    id = Column(INTEGER(11), primary_key=True)
    name = Column(String(18))
    game_id = Column(String(32))
    platform = Column(String(18))
    platform_id = Column(INTEGER(4))
    recharge10_rebate = Column(Float(10))
    loss = Column(Float(10))
    weight = Column(INTEGER(4))
    recharge_point = Column(INTEGER(5))


class GameRechange(Base):
    __tablename__ = 'game_rechange'

    id = Column(INTEGER(9), primary_key=True)
    update_time = Column(DateTime, primary_key=True)
    games = Column(Text)

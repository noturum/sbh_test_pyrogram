import os
from typing import Optional, List
from datetime import datetime
from enum import Enum
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import DeclarativeBase, mapped_column, Mapped


DB = os.getenv('DB')


class Status(Enum):
    ALIVE = 'alive'
    DEAD = 'dead'
    FINISHED = 'finished'


class BaseOrmModel(DeclarativeBase):
    ...


class Chats(BaseOrmModel):
    __tablename__ = 'chats'
    id_chat: Mapped[int] = mapped_column(primary_key=True, index=True)
    created_at: Mapped[datetime] = mapped_column()
    status_updated_at: Mapped[datetime] = mapped_column()
    triger: Mapped[bool] = mapped_column(default=False)
    last_message: Mapped[str] = mapped_column(nullable=True)
    _status: Mapped[Status] = mapped_column()

    @hybrid_property
    def status(self):
        return self._status

    @status.setter
    def status(self, val):
        self._status = val
        self.status_updated_at = datetime.now()


class DataBaseClient:

    def __init__(self):
        self.__engine = create_async_engine(DB)

    async def bootstrap(self):
        async with self.__engine.begin() as conn:
            await conn.run_sync(BaseOrmModel.metadata.create_all)

    async def exucute_stmt(self, stmt):
        async with AsyncSession(self.__engine, expire_on_commit=False) as session:
            res = await session.execute(stmt)
            await session.commit()
            await session.close()
            await self.__engine.dispose()
        return res

    async def save(self, obj: Chats):
        async with AsyncSession(self.__engine) as session:
            async with session.begin():
                session.add(obj)
            await session.commit()
            await session.close()
            await self.__engine.dispose()

    async def get_by_id(self, idchat: int) -> Optional[Chats]:
        stmt = select(Chats).where(Chats.id_chat == idchat)
        res = await self.exucute_stmt(stmt)
        return res.one_or_none()

    async def get_all(self) -> List[Chats]:
        stmt = select(Chats).where(Chats.status != Status.FINISHED)
        res = await self.exucute_stmt(stmt)
        return [task[0] for task in res.fetchall()]


if __name__ != "__main__":
    db_controller = DataBaseClient()

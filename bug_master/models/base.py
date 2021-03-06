import sqlite3
from typing import Union

from sqlalchemy.exc import PendingRollbackError

from ..consts import logger
from ..database import Base


class BaseModule(Base):
    __abstract__ = True

    @classmethod
    def create(cls, **kwargs) -> Union[Base, None]:
        """Create or get if already exist"""
        # session: Session = cls.get_session()
        with cls.get_session() as session:
            _id = kwargs.get("id", "")
            try:
                logger.debug(f"Querying {cls.__name__} with id {_id}")
                instance = session.query(cls).filter_by(id=_id).first()
            except PendingRollbackError:
                session.rollback()
                _id = kwargs.get("id", "")
                instance = session.query(cls).filter_by(id=_id).first()
            except sqlite3.OperationalError as e:
                logger.error(f"Database error, {e}")
                return None
            except Exception as e:
                logger.error(f"Database error, {e}")
                return None

            if not instance:
                instance = cls(**kwargs)
                session.add(instance)
                session.commit()
                logger.info(f"Added new entry to `{cls.__tablename__}` table, with id {instance.id}")
            else:
                logger.debug(f"Found {cls.__name__.lower()} instance - {instance}")

        return instance

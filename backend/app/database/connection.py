from psycopg.conninfo import make_conninfo
from psycopg_pool import AsyncConnectionPool

from app.config import settings


conninfo = make_conninfo(
    host=settings.db_host,
    port=settings.db_port,
    dbname=settings.db_name,
    user=settings.db_user,
    password=settings.db_password,
)


pool = AsyncConnectionPool(
    conninfo=conninfo,
    min_size=1,
    max_size=5,
    open=False,
)
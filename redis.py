import logging

from sanic import Sanic

from aioredis import create_redis_pool

logger = logging.getLogger(__name__)

redis = None


def register_redis(app: Sanic):
    logger.debug("Registering redis")
    config = get_redis_config(app.config)

    @app.listener("before_server_start")
    async def configure_redis(app, loop):
        logger.debug(f"Creating redis pool on address: {config['address']}")
        pool = await create_redis_pool(loop=loop, **config)

        app.redis = pool
        if not hasattr(app, "extensions"):
            app.extensions = {}
        app.extensions["redis"] = pool

    @app.listener("after_server_stop")
    async def close_redis_pool(app, loop):
        if not hasattr(app, "redis"):
            return

        pool = app.redis

        if pool is not None:
            logger.debug("Closing redis pool")
            waiter = pool.wait_closed()
            pool.close()
            await waiter


def get_redis_config(config):
    connection_uri = (
        getattr(config, "REDIS_HOST", "localhost"),
        getattr(config, "REDIS_PORT", 6379),
    )
    return {
        "address": connection_uri,
        "db": getattr(config, "REDIS_DATABASE", None),
        "password": getattr(config, "REDIS_PASSWORD", None),
        "ssl": getattr(config, "REDIS_SSL", None),
        "encoding": getattr(config, "REDIS_ENCODING", None),
        "minsize": getattr(config, "REDIS_MIN_SIZE_POOL", 1),
        "maxsize": getattr(config, "REDIS_MAX_SIZE_POOL", 10),
    }
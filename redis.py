import logging

from sanic import Sanic

import aioredis

logger = logging.getLogger(__name__)

redis = None


def register_redis(app: Sanic):
    logger.debug("Registering redis")
    config = get_redis_config(app.config)

    @app.listener("before_server_start")
    async def configure_redis(app, loop):
        logger.debug(f"Creating redis pool on address: {config['url']}")
        pool = await aioredis.from_url(**config)
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
            await pool.close()


def get_redis_config(config):
    protocol = "rediss://" if getattr(config, "REDIS_SSL", True) else "redis://"
    host = getattr(config, "REDIS_HOST", "localhost")
    port = str(getattr(config, "REDIS_PORT", 6379))
    print(protocol + host + ":" + port)
    return {
        "url": protocol + host + ":" + port,
        "db": getattr(config, "REDIS_DATABASE", None),
        "password": getattr(config, "REDIS_PASSWORD", None),
        "decode_responses": getattr(config, "REDIS_DECODE_RESPONSE", False),
    }
import os

from django.core.cache import cache


def set_quiz_result(quiz_id, user_id, instance_timestamp, data):
    timeout = int(os.environ.get("REDIS_TTL", 60 * 60 * 48))

    cache_key = f'results:{quiz_id}:{user_id}:{instance_timestamp}'
    cache.set(cache_key, data, timeout)

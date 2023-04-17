from contextlib import contextmanager

from django.db import DEFAULT_DB_ALIAS, connections


@contextmanager
def try_advisory_lock(lock_id: int):
    function_name = "pg_try_advisory_lock "
    release_function_name = "pg_advisory_unlock"
    base = "SELECT %s(%d)"
    params = (lock_id,)

    acquire_params = (function_name,) + params
    release_params = (release_function_name,) + params

    command = base % acquire_params
    cursor = connections[DEFAULT_DB_ALIAS].cursor()

    cursor.execute(command)

    acquired = cursor.fetchone()[0]

    try:
        yield acquired
    finally:
        if acquired:
            release_params = (release_function_name,) + params

            command = base % release_params
            cursor.execute(command)

        cursor.close()

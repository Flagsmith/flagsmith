from rest_framework.throttling import ScopedRateThrottle


class InfluxQueryThrottle(ScopedRateThrottle):
    scope = "influx_query"

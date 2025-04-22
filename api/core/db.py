from django.contrib.postgres.indexes import GinIndex


class UnrestrictedGinIndex(GinIndex):
    max_name_length = 63

import logging

from django.dispatch import Signal

logger = logging.getLogger(__name__)

feature_state_change_went_live = Signal()

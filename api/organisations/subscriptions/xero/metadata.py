from organisations.subscriptions.constants import XERO
from organisations.subscriptions.metadata import BaseSubscriptionMetadata


class XeroSubscriptionMetadata(BaseSubscriptionMetadata):
    payment_source = XERO

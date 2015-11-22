from .. import models


class CardProxy(models.Card):

    class Meta:
        proxy = True


class BitcoinRecieverProxy(models.BitcoinReceiver):

    class Meta:
        proxy = True

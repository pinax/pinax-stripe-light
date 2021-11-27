from django.dispatch import Signal


class WebhookRegistry:

    def __init__(self):
        self._registry = {}

    def register(self, webhook):
        self._registry[webhook.name] = {
            "webhook": webhook,
            "signal": Signal()
        }

    def unregister(self, name):
        del self._registry[name]

    def keys(self):
        return self._registry.keys()

    def get(self, name):
        return self[name]["webhook"]

    def get_signal(self, name, default=None):
        try:
            return self[name]["signal"]
        except KeyError:
            return default

    def signals(self):
        return {
            key: self.get_signal(key)
            for key in self.keys()
        }

    def __getitem__(self, name):
        return self._registry[name]


registry = WebhookRegistry()
del WebhookRegistry

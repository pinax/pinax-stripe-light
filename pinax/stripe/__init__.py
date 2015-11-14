import pkg_resources


default_app_config = "pinax.stripe.apps.AppConfig"
__version__ = pkg_resources.get_distribution("pinax-stripe").version

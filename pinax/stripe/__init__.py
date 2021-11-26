import django

import pkg_resources

if django.__version__ < "3.2":  # Deprecated in 4.1 but needed in 2.2 still
    default_app_config = "pinax.stripe.apps.AppConfig"

__version__ = pkg_resources.get_distribution("pinax-stripe").version

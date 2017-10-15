from django.conf.urls import url
from django.contrib import admin

from ..urls import urlpatterns


class FakeViewForUrl(object):
    def __call__(self):
        raise Exception("Should not get called.")


urlpatterns += [
    url(r"^admin/", admin.site.urls),
    url(r"^the/app/$", FakeViewForUrl, name="the_app"),
    url(r"^accounts/signup/$", FakeViewForUrl, name="signup"),
    url(r"^password/reset/confirm/(?P<token>.+)/$", FakeViewForUrl,
        name="password_reset"),
]

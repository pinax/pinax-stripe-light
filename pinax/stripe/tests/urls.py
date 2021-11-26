from django.contrib import admin
from django.urls import path

from ..urls import urlpatterns


class FakeViewForUrl:
    def __call__(self):
        raise Exception("Should not get called.")


urlpatterns += [
    path("admin/", admin.site.urls),
    path("the/app/", FakeViewForUrl, name="the_app"),
    path("accounts/signup/", FakeViewForUrl, name="signup"),
    path("password/reset/confirm/<str:token>/", FakeViewForUrl, name="password_reset"),
]

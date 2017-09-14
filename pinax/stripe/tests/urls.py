from django.contrib import admin
from django.conf.urls import url
from .mock_views import MockView
from ..urls import urlpatterns

urlpatterns += [

    url(r'^admin/', admin.site.urls),

    url(
        r'^the/app/$',
        MockView.as_view(),
        name='the_app'
    ),
    url(
        r'^accounts/signup/$',
        MockView.as_view(),
        name='signup'
    ),
    url(
        r'^password/reset/confirm/(?P<token>.+)/$',
        MockView.as_view(),
        name='password_reset'
    ),
]

from django.conf.urls import patterns, url
from .mock_views import MockView
from ..urls import urlpatterns

urlpatterns += patterns(
    '',
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
)

from django.http import HttpResponse
from django.views.generic import View


class MockView(View):

    def get(self, request, *args, **kwargs):
        return HttpResponse('Hello, World!')

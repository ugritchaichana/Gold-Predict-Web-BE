from django.shortcuts import render
from django.http import HttpResponse,JsonResponse

def index(request):
    return HttpResponse("Booth-Test")

def gold(request):
    data = {
        'key1': 'value1',
        'key2': 'value2',
        'key3': [1, 2, 3]
    }
    return JsonResponse(data)
"""
URL configuration for currency project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from apps.sync_prices import update_flow, load_json, CURRENT_JSON, PREVIOUS_JSON


def index(request):
    return render(request, "index.html")


def prices_api(request):
    current = load_json(CURRENT_JSON)
    previous = load_json(PREVIOUS_JSON)
    return JsonResponse({
        "current": current,
        "previous": previous,
        "current_last_modified": current.get("last_modified"),
        "previous_last_modified": previous.get("last_modified"),
    })


@csrf_exempt
def trigger_update(request):
    if request.method != "POST":
        return JsonResponse({"error": "POST required"}, status=405)
    ok = update_flow()
    return JsonResponse({"message": "update started" if ok else "update failed"}, status=200 if ok else 500)


urlpatterns = [
    path('', index),
    path('admin/', admin.site.urls),
    path('api/prices', prices_api),
    path('trigger-update', trigger_update),
]

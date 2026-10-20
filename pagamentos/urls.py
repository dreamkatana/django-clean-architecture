from django.urls import path

from .views import home_view, transferir_view

app_name = "pagamentos"

urlpatterns = [
    path("", home_view, name="home"),
    path("api/transferir/", transferir_view, name="transferir"),
]

from django.urls import path

from .views import transferir_view

app_name = "pagamentos"

urlpatterns = [
    path("api/transferir/", transferir_view, name="transferir"),
]

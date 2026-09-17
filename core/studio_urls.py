from django.urls import path

from . import studio_views as views

app_name = "studio"

urlpatterns = [
    path("", views.dashboard, name="home"),
    path("connexion/", views.login_view, name="login"),
    path("deconnexion/", views.logout_view, name="logout"),
    path("profil/", views.profile_view, name="profile"),
    path("messages/", views.message_list, name="messages"),
    path("messages/<int:pk>/", views.message_detail, name="message_detail"),
    path("securite/", views.lock_list, name="locks"),
    path("<slug:resource>/", views.resource_list, name="list"),
    path("<slug:resource>/nouveau/", views.resource_form, name="create"),
    path("<slug:resource>/<int:pk>/", views.resource_form, name="update"),
    path("<slug:resource>/<int:pk>/supprimer/", views.resource_delete, name="delete"),
]

from django.urls import path
from . import views

urlpatterns = [
    path("register", views.register_view, name="register"),
    path("login", views.login_view, name="login"),
    path("logout", views.logout_view, name="logout"),
    path("<user_id>", views.profile_view, name="profile"),
    path("<user_id>/edit", views.edit_profile_view, name="edit-profile"),
    path("<user_id>/edit/cropImage", views.crop_image, name="crop_image"),
    path("search/", views.search_result, name="search"),
]

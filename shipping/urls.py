"""URL patterns for the shipping app."""

from django.urls import path

from shipping import views

urlpatterns = [
    path("", views.index_view, name="index"),
    path("api/recommend/", views.recommend_box_view, name="recommend_box"),
]

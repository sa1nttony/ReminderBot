from django.urls import path
from . import api_views

urlpatterns = [
    path('tasks/', api_views.TaskList.as_view()),
    path('tasks/<int:pk>', api_views.TaskRetrieveUpdateDestroyView.as_view()),
    path('users/', api_views.UserList.as_view()),
    path('users/<int:pk>', api_views.UserRetrieveUpdateDestroyView.as_view())
]
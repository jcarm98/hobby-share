from django.urls import path, re_path, include
from . import views

urlpatterns = [
    path('check/login/', views.check_login, name='check_login'),
    path('check/username/', views.check_username, name='check_username'),
    path('check/email/', views.check_email, name='check_email'),
    path('sign-up/', views.sign_up, name='sign_up'),
    path('verify/user/', views.verify_user, name='verify_user'),
    path('log-in/', views.log_in, name='log_in'),
    path('log-out/', views.log_out, name='log_out'),
    path('email/', views.email, name='email'),
    path('forgot/username/', views.forgot_user, name='forgot_user'),
    path('forgot/password/', views.forgot_password, name='forgot_password'),
    path('reset/password/', views.reset_password, name='reset_password'),
    path('fetch/username/', views.fetch_username, name='fetch_username'),
    path('user/<str:username>/', views.get_user, name='get_user'),
    path('self/', views.get_self, name='get_self'),
    path('user/', views.user, name='user'),
    path('project/', views.make_project, name='make_project'),
    path('project/<int:id>/', views.project, name='project'),
    path('fetch/lastproject/', views.fetch_last_project, name='fetch_last_project'),
    path('request/', views.join_request, name='join_request'),
    path('invite/', views.invite, name='invite'),
    path('leave/', views.leave, name='leave'),
    path('fetch/projects/', views.fetch_projects, name='fetch_projects'),
    path('recent/', views.recent, name='recent'),
    path('remove/', views.remove, name='remove'),
    #path('all/', views.test_get_all, name='test_all'),
    #re_path(r'^post/?$', views.test_post, name='test_post')
]

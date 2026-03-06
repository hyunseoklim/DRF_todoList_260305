from django.urls import path
from .views import SignupAPIView, SessionLoginAPIView, SessionLogoutAPIView
from .views_page import LoginPageView, SignupPageView

urlpatterns = [
    # API
    path("api/signup/", SignupAPIView.as_view(), name="api-signup"),
    path("api/login/", SessionLoginAPIView.as_view(), name="api-login"),
    path("api/logout/", SessionLogoutAPIView.as_view(), name="api-logout"),
    # Pages
    path("signup-page/", SignupPageView.as_view(), name="page-signup"),
    path("login/", LoginPageView.as_view(), name="page-login"),
]

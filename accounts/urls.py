from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .views import SignupAPIView, SessionLogoutAPIView
from .views_page import LoginPageView, SignupPageView

urlpatterns = [
    # API
    path("api/signup/", SignupAPIView.as_view(), name="api-signup"),
    # JWT 로그인(토큰 발급): access + refresh 반환
    path("api/login/", TokenObtainPairView.as_view(), name="jwt-login"),
    # access 만료 시 refresh로 재발급
    path("api/token/refresh/", TokenRefreshView.as_view(), name="jwt-refresh"),
    # (임시 유지) 세션 로그아웃 API - JWT에서는 의미가 약함 (6단계에서 정리 권장)
    path("api/logout/", SessionLogoutAPIView.as_view(), name="api-logout"),
    # Pages
    path("signup-page/", SignupPageView.as_view(), name="page-signup"),
    path("login/", LoginPageView.as_view(), name="page-login"),
]

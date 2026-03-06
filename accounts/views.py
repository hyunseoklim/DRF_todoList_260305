from django.contrib.auth import logout  # 세션 로그인은 더 이상 필요 없음
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from .serializers import SignupSerializer


# 회원가입 API (JWT/세션과 무관하게 그대로 사용)
class SignupAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = SignupSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"detail": "회원가입 완료"}, status=status.HTTP_201_CREATED)


# 2단계부터는 SessionLoginAPIView가 필요 없음
# - /api/login/ 은 accounts/urls.py에서 TokenObtainPairView가 처리 (JWT 발급)
# - 따라서 authenticate/login 로직 제거


# ⚠️ 전환기 임시 로그아웃(세션 정리용)
# - JWT 환경에서 '로그아웃'은 보통 프론트에서 토큰 삭제로 처리합니다.
# - 그래도 혹시 남아있을 수 있는 세션을 logout(request)로 정리해줍니다.
class SessionLogoutAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        logout(request)
        return Response({"detail": "로그아웃(세션 정리)"}, status=status.HTTP_200_OK)

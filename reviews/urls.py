# ============================================================
# Django REST Framework Router 설정
# ============================================================

# DRF에서 ViewSet을 URL과 자동으로 연결해주는 Router 클래스 import
# → URL 패턴을 직접 작성하지 않아도 API 경로를 자동 생성해줌
from rest_framework.routers import DefaultRouter

# 현재 앱의 ViewSet import
# → CollectedReview 데이터를 조회하는 API ViewSet
from .views import CollectedReviewViewSet

from django.urls import path

from .views import reviews_page

# ============================================================
# Router 생성
# ============================================================

# DefaultRouter
# → DRF에서 가장 기본적으로 사용하는 Router
# → ViewSet을 등록하면 자동으로 REST API URL을 생성
router = DefaultRouter()


# ============================================================
# ViewSet 등록
# ============================================================

# router.register()
# → 특정 URL 경로에 ViewSet을 연결하는 함수
#
# r"collected-reviews"
# → API 기본 URL 경로
# → 예: /collected-reviews/
#
# CollectedReviewViewSet
# → 해당 URL에서 실행될 ViewSet 클래스
#
# basename
# → URL 이름을 만들 때 사용하는 기본 이름
router.register(
    r"collected-reviews", CollectedReviewViewSet, basename="collected-reviews"
)


# ============================================================
# Django URL 패턴 생성
# ============================================================

urlpatterns = [
    path("reviews/page/", reviews_page, name="reviews-page"),  # 추가
]

# router.urls
# → Router가 자동으로 생성한 URL 패턴 목록
#
# 이 값을 urlpatterns에 연결하면
# 아래 API가 자동으로 생성됩니다.
urlpatterns = router.urls

# Django 관리자 기능을 사용하기 위해 admin 모듈 import
from django.contrib import admin

# 현재 앱(models.py)에 정의된 CollectedReview 모델 import
from .models import CollectedReview


# ============================================================
# Django Admin에 CollectedReview 모델 등록
# ============================================================


# @admin.register()
# → 해당 모델을 Django 관리자 페이지에 등록하는 데코레이터
# → admin.site.register() 대신 간단히 사용 가능
@admin.register(CollectedReview)


# CollectedReview 모델의 관리자 페이지 설정 클래스
class CollectedReviewAdmin(admin.ModelAdmin):

    # ------------------------------------------------------------
    # 관리자 목록 화면에서 표시할 컬럼 설정
    # ------------------------------------------------------------
    # id           : 데이터 기본 키
    # title        : 리뷰 제목
    # doc_id       : 중복 방지용 문서 ID
    # collected_at : 데이터 수집 시각
    list_display = ("doc_id", "title", "collected_at")

    # ------------------------------------------------------------
    # 관리자 페이지 검색 기능 설정
    # ------------------------------------------------------------
    # title  : 제목 기준 검색
    # review : 본문 기준 검색
    # 관리자 검색창에서 키워드를 입력하면
    # 해당 필드를 기준으로 DB 검색 수행
    search_fields = ("title", "review")

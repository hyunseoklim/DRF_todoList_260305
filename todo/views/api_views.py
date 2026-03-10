from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from ..models import Todo  # 경로변경
from ..serializers import TodoSerializer  # 경로변경

# ViewSets 사용을 위한 DRF 모듈 import
from rest_framework import viewsets

# 인증된 사용자만 접근 가능하도록 하는 권한 클래스
from rest_framework.permissions import IsAuthenticated

from rest_framework.pagination import PageNumberPagination

# 기존 APIView 방식 대신 ViewSet을 사용하기 위해 TodoViewSet import
# from .views.api_views import TodoViewSet

from django.db.models import Q
from ..pagination import TodoListPagination


# Viewsets CRUD를 하나로 통일
class TodoViewSet(viewsets.ModelViewSet):
    serializer_class = TodoSerializer
    permission_classes = [IsAuthenticated]  # 로그인한 사용자만 접근 가능
    pagination_class = TodoListPagination  # 리스트 조회 시 페이지네이션 적용

    # ======================================================
    # 공개글 + 내 글 조회 로직
    # ======================================================
    def get_queryset(self):
        user = self.request.user  # 현재 로그인한 사용자

        return Todo.objects.filter(
            # Q 객체를 사용하여 OR 조건을 생성
            # ---------------------------------------------
            # Q(is_public=True)
            #   → 다른 사용자가 작성한 Todo라도
            #     "공개글(is_public=True)"이면 조회 가능
            #
            # Q(user=user)
            #   → 현재 로그인한 사용자가 작성한 Todo는
            #     공개 여부와 상관없이 모두 조회 가능
            #
            # 즉,
            # "공개글이거나 OR 내가 작성한 글" 을 조회
            Q(is_public=True)
            | Q(user=user)
        ).order_by(
            "-created_at"
        )  # 최신 글이 먼저 보이도록 정렬

    # ======================================================
    # Todo 생성 시 작성자 자동 설정
    # ======================================================
    def perform_create(self, serializer):
        # 프론트에서 user를 보내지 않아도
        # 현재 로그인한 사용자를 작성자로 자동 저장
        # 또한 기본적으로 글을 공개 상태(is_public=True)로 생성
        serializer.save(user=self.request.user, is_public=True)


class TodoListPagination(PageNumberPagination):

    page_size = 3
    # 한 페이지에 기본적으로 보여줄 데이터 개수

    page_size_query_param = "page_size"
    # URL 쿼리 파라미터로 페이지 크기 변경 가능
    # 예: /todo/viewsets/view/?page_size=5

    max_page_size = 50
    # 사용자가 설정할 수 있는 최대 페이지 크기 제한
    # 예: page_size=100 요청 시 최대 50까지만 허용


# 전체보기
class TodoListAPI(APIView):
    def get(self, request):
        # GET 요청이 들어오면 실행되는 함수

        todos = Todo.objects.all()
        # Todo 모델의 모든 데이터 조회 (QuerySet)

        serializer = TodoSerializer(todos, many=True)
        # 조회한 Todo 객체들을 Serializer로 JSON 변환 준비
        # many=True → 여러 개의 객체를 변환한다는 의미

        return Response(serializer.data)
        # serializer.data를 JSON 형태로 변환하여 API 응답으로 반환


# 생성하기
class TodoCreateAPI(APIView):

    def post(self, request):
        # POST 요청이 들어오면 실행되는 함수 (데이터 생성 요청)

        serializer = TodoSerializer(data=request.data)
        # 요청(request)으로 들어온 JSON 데이터를 Serializer에 전달

        serializer.is_valid(raise_exception=True)
        # 데이터 유효성 검사 수행
        # 잘못된 데이터가 있으면 자동으로 400 에러 발생

        todo = serializer.save()
        # 검증된 데이터를 Todo 모델에 저장 (DB에 새로운 데이터 생성)

        return Response(TodoSerializer(todo).data, status=status.HTTP_201_CREATED)
        # 생성된 Todo 객체를 다시 Serializer로 JSON 변환 후 응답
        # HTTP 상태코드 201 (생성 성공)


# 상세보기 API
class TodoRetrieveAPI(APIView):

    def get(self, request, pk):
        # GET 요청이 들어오면 실행되는 함수
        # pk는 URL에서 전달된 Todo의 기본키(id)

        try:
            todo = Todo.objects.get(pk=pk)
            # pk 값에 해당하는 Todo 데이터를 DB에서 조회

        except Todo.DoesNotExist:
            # 해당 pk의 Todo가 존재하지 않을 경우 실행

            return Response(
                {"error": "해당하는 todo가 없습니다."},
                # 에러 메시지를 JSON 형태로 반환
                status=status.HTTP_404_NOT_FOUND,
                # HTTP 상태코드 404 (데이터 없음)
            )

        serializer = TodoSerializer(todo)
        # 조회한 Todo 객체를 Serializer로 JSON 변환 준비

        return Response(serializer.data)
        # 변환된 데이터를 JSON 응답으로


# 수정하기 API
class TodoUpdateAPI(APIView):

    def put(self, request, pk):
        # PUT 요청 → 전체 수정 (모든 필드를 다시 보내야 함)

        try:
            todo = Todo.objects.get(pk=pk)
            # pk에 해당하는 Todo 데이터 조회

        except Todo.DoesNotExist:
            # 해당 Todo가 존재하지 않을 경우

            return Response(
                {"error": "해당하는 todo가 없습니다."},
                # 에러 메시지를 JSON 형태로 반환
                status=status.HTTP_404_NOT_FOUND,
                # HTTP 상태코드 404 반환
            )

        serializer = TodoSerializer(todo, data=request.data)
        # 기존 Todo 객체 + 요청 데이터(request.data)를 Serializer에 전달
        # 전체 데이터를 기준으로 수정

        serializer.is_valid(raise_exception=True)
        # 데이터 유효성 검사 (문제 있으면 400 에러 발생)

        todo = serializer.save()
        # 검증된 데이터로 Todo 객체 업데이트

        serializer = TodoSerializer(todo)
        # 수정된 Todo 객체를 다시 Serializer로 변환

        return Response(serializer.data)
        # 수정된 데이터를 JSON 형태로 응답

    def patch(self, request, pk):
        # PATCH 요청 → 부분 수정 (일부 필드만 수정 가능)

        try:
            todo = Todo.objects.get(pk=pk)
            # pk에 해당하는 Todo 데이터 조회

        except Todo.DoesNotExist:
            # 해당 Todo가 존재하지 않을 경우

            return Response(
                {"error": "해당하는 todo가 없습니다."},
                status=status.HTTP_404_NOT_FOUND,
                # HTTP 상태코드 404 반환
            )

        serializer = TodoSerializer(todo, data=request.data, partial=True)
        # partial=True → 일부 필드만 보내도 수정 가능

        serializer.is_valid(raise_exception=True)
        # 데이터 유효성 검사

        todo = serializer.save()
        # 수정된 데이터 DB 저장

        serializer = TodoSerializer(todo)
        # 수정된 객체를 JSON 변환

        return Response(serializer.data)
        # 수정된 데이터 응답


# 삭제하기 API
class TodoDeleteAPI(APIView):

    def delete(self, request, pk):
        # DELETE 요청이 들어오면 실행되는 함수
        # pk는 URL로 전달된 Todo의 기본키(id)

        try:
            todo = Todo.objects.get(pk=pk)
            # pk에 해당하는 Todo 데이터를 DB에서 조회

        except Todo.DoesNotExist:
            # 해당 Todo가 존재하지 않을 경우 실행

            return Response(
                {"error": "해당하는 todo가 없습니다."},
                # 에러 메시지를 JSON 형태로 반환
                status=status.HTTP_404_NOT_FOUND,
                # HTTP 상태코드 404 (데이터 없음)
            )

        todo.delete()
        # 조회한 Todo 데이터를 DB에서 삭제

        return Response(status=status.HTTP_204_NO_CONTENT)
        # 삭제 성공 시 응답 반환 (204 = 성공했지만 반환할 데이터 없음)

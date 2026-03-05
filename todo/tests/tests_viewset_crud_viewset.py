from django.test import TestCase
from rest_framework.test import APIClient

from ..models import Todo


# ---------------------------------------------------------
# ViewSet 기반 Todo CRUD API 테스트
# ---------------------------------------------------------
class TodoViewSetCRUDTests(TestCase):
    """
    ViewSet 라우팅 기반 API 테스트

    list:     GET    /todo/viewsets/view/
    create:   POST   /todo/viewsets/view/
    retrieve: GET    /todo/viewsets/view/<pk>/
    update:   PATCH  /todo/viewsets/view/<pk>/
    destroy:  DELETE /todo/viewsets/view/<pk>/
    """

    # ---------------------------------------------------------
    # 테스트 시작 전에 공통 데이터 준비
    # ---------------------------------------------------------
    def setUp(self):

        self.client = APIClient()
        # DRF API 테스트용 클라이언트
        # 실제 브라우저 대신 API 요청을 보내는 역할

        self.base_url = "/todo/viewsets/view/"
        # ViewSet API 기본 URL

        self.todo = Todo.objects.create(
            name="운동",
            description="스쿼트 50회",
            complete=False,
            exp=10,
        )
        # 테스트용 기본 Todo 데이터 생성

    # ---------------------------------------------------------
    # 목록 조회 테스트
    # ---------------------------------------------------------
    def test_list(self):

        res = self.client.get(self.base_url)
        # GET 요청으로 Todo 목록 조회

        self.assertEqual(res.status_code, 200)
        # 상태코드 200(성공)인지 확인

        data = res.json()
        # 응답 데이터를 JSON으로 변환

        self.assertIsInstance(data, list)
        # 응답이 리스트 형태인지 확인

        self.assertGreaterEqual(len(data), 1)
        # 최소 1개 이상의 데이터가 존재하는지 확인

    # ---------------------------------------------------------
    # 생성 테스트
    # ---------------------------------------------------------
    def test_create(self):

        payload = {
            "name": "공부",
            "description": "DRF",
            "complete": False,
            "exp": 5,
        }
        # 새로 생성할 Todo 데이터

        res = self.client.post(self.base_url, payload, format="json")
        # POST 요청으로 Todo 생성

        self.assertIn(res.status_code, (200, 201))
        # 상태코드 확인 (보통 201 Created)

        self.assertEqual(Todo.objects.count(), 2)
        # 기존 1개 + 새로 생성된 1개 = 총 2개인지 확인

    # ---------------------------------------------------------
    # 상세 조회 테스트
    # ---------------------------------------------------------
    def test_retrieve(self):

        res = self.client.get(f"{self.base_url}{self.todo.id}/")
        # 특정 Todo id로 조회

        self.assertEqual(res.status_code, 200)
        # 상태코드 200 확인

        self.assertEqual(res.json()["name"], "운동")
        # 반환된 데이터의 name 값 확인

    # ---------------------------------------------------------
    # 부분 수정 테스트 (PATCH)
    # ---------------------------------------------------------
    def test_partial_update_patch(self):

        payload = {"name": "운동(수정)"}
        # 수정할 데이터

        res = self.client.patch(
            f"{self.base_url}{self.todo.id}/", payload, format="json"
        )
        # PATCH 요청으로 Todo 일부 수정

        self.assertEqual(res.status_code, 200)
        # 수정 성공 확인

        self.todo.refresh_from_db()
        # DB에서 데이터를 다시 불러옴

        self.assertEqual(self.todo.name, "운동(수정)")
        # 실제 DB 값이 수정되었는지 확인

    # ---------------------------------------------------------
    # 삭제 테스트
    # ---------------------------------------------------------
    def test_destroy_delete(self):

        res = self.client.delete(f"{self.base_url}{self.todo.id}/")
        # DELETE 요청으로 Todo 삭제

        self.assertIn(res.status_code, (200, 204))
        # 삭제 성공 상태코드 확인 (보통 204)

        self.assertFalse(Todo.objects.filter(id=self.todo.id).exists())
        # DB에 해당 데이터가 존재하지 않는지 확인

    # ---------------------------------------------------------
    # 존재하지 않는 데이터 요청 테스트
    # ---------------------------------------------------------
    def test_not_found_returns_404(self):

        res = self.client.get(f"{self.base_url}999999/")
        # 존재하지 않는 id로 조회 요청

        self.assertEqual(res.status_code, 404)
        # 404 Not Found 반환 확인

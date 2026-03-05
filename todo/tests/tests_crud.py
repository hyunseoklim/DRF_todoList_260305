from django.test import TestCase
from rest_framework.test import APIClient

from ..models import Todo


# ---------------------------------------------------------
# ✅ Todo API CRUD 동작을 검증하는 테스트 클래스
# ---------------------------------------------------------
# TestCase를 상속받으면:
# - 테스트용 임시 DB가 생성됨
# - 각 테스트 함수 실행 전 DB가 초기화됨
# - 실제 DB에 영향을 주지 않음
class TodoAPITests(TestCase):

    # -----------------------------------------------------
    # 테스트 실행 전에 공통으로 준비되는 데이터
    # -----------------------------------------------------
    def setUp(self):
        # DRF 전용 테스트 클라이언트 생성
        # → 실제 브라우저 대신 API 요청을 보내는 역할
        self.client = APIClient()

        # 테스트용 기본 Todo 1개 생성
        # → retrieve / update / delete 테스트에서 사용
        self.todo = Todo.objects.create(
            name="운동",
            description="스쿼트 50회",
            complete=False,
            exp=10,
        )

    # -----------------------------------------------------
    # 1️⃣ 목록 조회 테스트 (GET /list/)
    # -----------------------------------------------------
    def test_list(self):
        # API 요청
        res = self.client.get("/todo/api/list/")

        # 상태코드가 200(성공)인지 확인
        self.assertEqual(res.status_code, 200)

        # 응답이 리스트 형태인지 확인
        self.assertIsInstance(res.json(), list)

    # -----------------------------------------------------
    # 2️⃣ 생성 테스트 (POST /create/)
    # -----------------------------------------------------
    def test_create(self):
        payload = {
            "name": "공부",
            "description": "DRF",
            "complete": False,
            "exp": 5,
        }

        # 새 Todo 생성 요청
        res = self.client.post("/todo/api/create/", payload, format="json")

        # 상태코드가 201(생성 성공)인지 확인
        self.assertEqual(res.status_code, 201)

        # 기존 1개 + 새로 생성 1개 = 총 2개인지 확인
        self.assertEqual(Todo.objects.count(), 2)

    # -----------------------------------------------------
    # 3️⃣ 상세 조회 테스트 (GET /retrieve/<pk>/)
    # -----------------------------------------------------
    def test_retrieve(self):
        # 생성된 Todo의 id로 조회
        res = self.client.get(f"/todo/api/retrieve/{self.todo.id}/")

        # 상태코드 200 확인
        self.assertEqual(res.status_code, 200)

        # 반환된 데이터의 name 값이 올바른지 확인
        self.assertEqual(res.json()["name"], "운동")

    # -----------------------------------------------------
    # 4️⃣ 수정 테스트 (PATCH /update/<pk>/)
    # -----------------------------------------------------
    def test_update_patch(self):
        payload = {"name": "운동(수정)"}

        # 해당 Todo의 name 수정 요청
        res = self.client.patch(
            f"/todo/api/update/{self.todo.id}/", payload, format="json"
        )

        # 상태코드 200 확인
        self.assertEqual(res.status_code, 200)

        # DB에서 다시 불러와서 실제 값이 변경되었는지 확인
        self.todo.refresh_from_db()
        self.assertEqual(self.todo.name, "운동(수정)")

    # -----------------------------------------------------
    # 5️⃣ 삭제 테스트 (DELETE /delete/<pk>/)
    # -----------------------------------------------------
    def test_delete(self):
        # 삭제 요청
        res = self.client.delete(f"/todo/api/delete/{self.todo.id}/")

        # 상태코드 204(삭제 성공) 확인
        self.assertEqual(res.status_code, 204)

        # 실제 DB에 해당 데이터가 존재하지 않는지 확인
        self.assertFalse(Todo.objects.filter(id=self.todo.id).exists())

    # -----------------------------------------------------
    # 6️⃣ 존재하지 않는 데이터 요청 시 404 테스트
    # -----------------------------------------------------
    def test_not_found_returns_404(self):
        # 존재하지 않는 id로 조회
        res = self.client.get("/todo/api/retrieve/999999/")

        # 404(Not Found) 반환 확인
        self.assertEqual(res.status_code, 404)

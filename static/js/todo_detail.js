// ======================================================
// Todo Detail 페이지 전용 JS
// - 수정 페이지 이동
// - 삭제
// - 홈으로 이동
// ======================================================

document.addEventListener("DOMContentLoaded", () => {

    // ======================================================
    // 0) 기본 설정
    // ======================================================
    const LOGIN_PAGE_URL = "/login/";
    const LIST_PAGE_URL = "/todo/list/";

    // HTML data 속성에서 todoId 가져오기
    // (Django 템플릿 변수를 JS로 넘기는 안전한 방법)
    const todoId = document.getElementById("todoMeta").dataset.todoId;

    // ======================================================
    // 0-1) window.api 존재 확인
    // ======================================================
    if (!window.api) {
        console.error("window.api가 없습니다. base.html에서 static/js/api.js 로드 확인");
        alert("설정 오류: api.js가 로드되지 않았습니다.");
        return;
    }

    // ======================================================
    // 0-2) access_token 확인
    // ======================================================
    const access = localStorage.getItem("access_token");
    if (!access) {
        console.log("access_token 없음 → 로그인 이동");
        window.location.href = LOGIN_PAGE_URL;
        return;
    }

    // ======================================================
    // 1) 공통 헬퍼
    // ======================================================
    function handleAuthError(err) {
        const status = err.response?.status;
        if (status === 401 || status === 403) {
            console.log("인증 실패(401/403) → 토큰 삭제 후 로그인 이동");
            localStorage.removeItem("access_token");
            localStorage.removeItem("refresh_token");
            window.location.href = LOGIN_PAGE_URL;
        }
        return Promise.reject(err);
    }

    // ======================================================
    // 2) 버튼 이벤트
    // ======================================================

    // 수정 버튼 → 수정 페이지 이동
    document.querySelector(".todoUpdate").addEventListener("click", () => {
        window.location.href = `/todo/update/${todoId}/`;
    });

    // 삭제 버튼 → 확인 후 삭제 API 호출
    document.querySelector(".todoDelete").addEventListener("click", async () => {
        const ok = confirm("정말 삭제하시겠습니까?");
        if (!ok) return;

        try {
            await window.api.delete(`/todo/viewsets/view/${todoId}/`);
            window.location.href = LIST_PAGE_URL;

        } catch (err) {
            handleAuthError(err).catch(() => { });
            console.error("삭제 실패:", err.response?.data || err.message);
            alert("삭제 중 오류가 발생했습니다.");
        }
    });

    // 홈으로 버튼 → 목록 페이지 이동
    document.querySelector(".todoHome").addEventListener("click", () => {
        window.location.href = LIST_PAGE_URL;
    });

});

// ======================================================
// Todo Update 페이지 전용 JS
// - Todo 수정 (이미지 포함 FormData + PATCH 방식)
// ======================================================

document.addEventListener("DOMContentLoaded", () => {

    // ======================================================
    // 0) 기본 설정
    // ======================================================
    const LOGIN_PAGE_URL = "/login/";

    // HTML data 속성에서 todoId 가져오기
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
    // 2) 저장 버튼 클릭 이벤트
    // ======================================================
    document.getElementById("todoUpdate").addEventListener("click", async () => {
        try {
            const formData = new FormData();
            formData.append("name", document.getElementById("name").value);
            formData.append("description", document.getElementById("description").value);
            formData.append("complete", document.getElementById("complete").checked ? "true" : "false");
            formData.append("exp", document.getElementById("exp").value || "0");

            const fileInput = document.getElementById("image");
            if (fileInput.files.length > 0) {
                formData.append("image", fileInput.files[0]);
            }

            const res = await window.api.patch(`/todo/viewsets/view/${todoId}/`, formData);

            console.log("수정 성공:", res.data);
            window.location.href = `/todo/detail/${todoId}/`;

        } catch (err) {
            handleAuthError(err).catch(() => { });
            console.error("수정 실패:", err.response?.data || err.message);
            alert("수정 실패: 콘솔/네트워크 확인");
        }
    });

});

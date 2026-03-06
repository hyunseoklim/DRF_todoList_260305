// static/js/api.js

const ACCESS_KEY = "access_token";
const REFRESH_KEY = "refresh_token";

// access 토큰 읽기
function getAccessToken() {
    return localStorage.getItem(ACCESS_KEY);
}

// refresh 토큰 읽기 (4~5단계에서 사용)
function getRefreshToken() {
    return localStorage.getItem(REFRESH_KEY);
}

// ✅ 전역 axios 인스턴스 생성
window.api = axios.create({
    baseURL: "/",   // same-origin
    timeout: 15000,
});

// ✅ 모든 요청에 Authorization 자동 부착
window.api.interceptors.request.use((config) => {
    const token = getAccessToken();

    if (token) {
        config.headers = config.headers || {};
        config.headers.Authorization = `Bearer ${token}`;
    }

    return config;
});

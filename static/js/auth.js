function getApiUrl() {
    const hostname = window.location.hostname;
    const port = window.location.port;

    if (hostname === 'localhost' || hostname === '127.0.0.1') {
        if (port === '8001') {
            return 'http://localhost:8001/api';
        } else if (port === '8000') {
            return 'http://localhost:8000/api';
        }
    } else if (hostname.includes('dev.')) {
        return 'https://dev-api.tuum.day/api';
    } else {
        // 프로덕션: 같은 도메인에서 API 서빙 (CORS 불필요)
        return '/api';
    }
}

const API_URL = getApiUrl();

// 토큰 관리를 위한 키 상수
const TOKEN_KEYS = {
    ACCESS_TOKEN: 'access_token',
    USER_ID: 'user_id',
};

// 토큰 저장
function saveTokens(accessToken, userId, rememberMe = false) {
    const storage = rememberMe ? localStorage : sessionStorage;
    // 다른 스토리지에 있는 토큰은 삭제하여 충돌을 방지합니다.
    const otherStorage = rememberMe ? sessionStorage : localStorage;
    otherStorage.removeItem(TOKEN_KEYS.ACCESS_TOKEN);
    otherStorage.removeItem(TOKEN_KEYS.USER_ID);

    storage.setItem(TOKEN_KEYS.ACCESS_TOKEN, accessToken);
    storage.setItem(TOKEN_KEYS.USER_ID, userId);
}

// 토큰 가져오기
function getTokens() {
    // localStorage에 토큰이 있으면 우선적으로 사용합니다.
    let accessToken = localStorage.getItem(TOKEN_KEYS.ACCESS_TOKEN);
    let userId = localStorage.getItem(TOKEN_KEYS.USER_ID);

    // localStorage에 토큰이 없으면 sessionStorage에서 찾습니다.
    if (!accessToken) {
        accessToken = sessionStorage.getItem(TOKEN_KEYS.ACCESS_TOKEN);
        userId = sessionStorage.getItem(TOKEN_KEYS.USER_ID);
    }

    return {
        accessToken: accessToken,
        userId: userId,
    };
}

// 토큰 삭제 (로그아웃 시 사용)
function clearTokens() {
    // 두 스토리지 모두에서 토큰을 삭제합니다.
    localStorage.removeItem(TOKEN_KEYS.ACCESS_TOKEN);
    localStorage.removeItem(TOKEN_KEYS.USER_ID);
    sessionStorage.removeItem(TOKEN_KEYS.ACCESS_TOKEN);
    sessionStorage.removeItem(TOKEN_KEYS.USER_ID);
}

// 토큰 존재 여부 확인
function hasValidTokens() {
    return !!(localStorage.getItem(TOKEN_KEYS.ACCESS_TOKEN) || sessionStorage.getItem(TOKEN_KEYS.ACCESS_TOKEN));
}

// API 요청 시 사용할 인증 헤더 생성
function getAuthHeaders() {
    const { accessToken } = getTokens();
    return accessToken
        ? {
              Authorization: `Bearer ${accessToken}`,
          }
        : {};
}

/**
 * 강제 로그아웃 및 로그인 페이지 리다이렉트 처리
 */
function forceLogout() {
    clearTokens();
    alert('세션이 만료되었거나 유효하지 않습니다. 다시 로그인해주세요.');
    window.location.href = '/login';
}

// 토큰 갱신 중복 실행을 방지하기 위한 변수
let isRefreshing = false;
let refreshSubscribers = [];
/**
 * 토큰을 갱신하고 원래 요청을 재시도하는 함수
 * @param {string} originalUrl 재시도할 원래 URL
 * @param {RequestInit} originalOptions 재시도할 원래 fetch 옵션
 * @returns {Promise<Response|null>} 재시도 성공 시 Response, 실패 시 null
 */
async function refreshTokenAndRetry(originalUrl, originalOptions) {
    // 이미 다른 요청에 의해 토큰 갱신이 진행 중인 경우
    if (isRefreshing) {
        // 갱신이 완료될 때까지 기다렸다가 원래 요청을 재시도하는 Promise를 반환
        return new Promise((resolve) => {
            // 갱신 후 실행할 콜백을 배열에 추가
            refreshSubscribers.push(() => {
                console.log('대기 후 원래 요청 재시도:', originalUrl);
                resolve(fetchWithAuth(originalUrl, originalOptions));
            });
        });
    }

    isRefreshing = true;
    console.log('액세스 토큰 갱신 시도...');

    try {
        // 중요: 토큰 갱신 요청은 fetchWithAuth를 사용하지 않음 (무한 루프 방지)
        const refreshResponse = await fetch(`${API_URL}/user/v1/token/refresh`, {
            method: 'POST',
            credentials: 'include',
        });

        if (!refreshResponse.ok) {
            console.error('토큰 갱신 실패:', refreshResponse.status, await refreshResponse.text());
            forceLogout();
            return null;
        }

        const data = await refreshResponse.json();
        // '로그인 상태 유지' 여부를 알 수 없으므로, localStorage에 토큰이 있었다면 true로 간주
        const rememberMe = !!localStorage.getItem(TOKEN_KEYS.ACCESS_TOKEN);
        saveTokens(data.access_token, data.user_id, rememberMe);
        console.log('토큰 갱신 성공. 대기 중인 요청 처리...');

        // 대기 중이던 모든 요청들을 실행
        refreshSubscribers.forEach((callback) => callback());
        refreshSubscribers = []; // 배열 비우기

        console.log('첫 요청 재시도:', originalUrl);
        return fetchWithAuth(originalUrl, originalOptions); // 원래의 첫 요청 재시도
    } catch (error) {
        console.error('토큰 갱신 중 네트워크 오류 또는 기타 문제 발생:', error);
        forceLogout();
        return null;
    } finally {
        isRefreshing = false;
    }
}

/**
 * 인증 헤더와 함께 fetch 요청을 보내는 공용 함수 (401 시 토큰 갱신 및 재시도)
 * @param {string} url 요청할 URL
 * @param {RequestInit} options fetch 옵션 객체
 * @returns {Promise<Response>} fetch Promise
 */
async function fetchWithAuth(url, options = {}) {
    const headers = getAuthHeaders();

    // 기존 옵션의 헤더와 병합
    const mergedHeaders = {
        ...(options.headers || {}),
        ...headers,
    };
    // Content-Type은 body가 있을 때만 추가하는 것이 더 안전할 수 있음
    if (options.body && !(options.body instanceof FormData)) {
        mergedHeaders['Content-Type'] = 'application/json';
    }

    // options.body가 객체면 JSON 문자열로 변환 (FormData 제외)
    let body = options.body;
    if (typeof body === 'object' && body !== null && !(body instanceof FormData)) {
        body = JSON.stringify(body);
    }

    const mergedOptions = {
        ...options,
        headers: mergedHeaders,
        body: body,
        credentials: 'include',
    };

    try {
        const full_url = API_URL + url;
        const response = await fetch(full_url, mergedOptions);

        // 401 Unauthorized 에러 발생 시 토큰 갱신 및 재시도 로직
        if (response.status === 401) {
            console.warn('[fetchWithAuth] 401 Unauthorized 감지. 토큰 갱신 및 재시도 시작... :' + full_url);
            // 재시도 함수의 결과를 반환 (성공 시 Response, 실패 시 null)
            const retryResponse = await refreshTokenAndRetry(url, mergedOptions);
            // 재시도 실패(null) 시 에러처럼 처리하거나, 호출 측에서 null을 처리하도록 함
            if (retryResponse === null) {
                // 이미 forceLogout이 호출되었으므로 여기서는 에러만 던져서 흐름 중단
                throw new Error('Token refresh failed and user was logged out.');
            }
            return retryResponse;
        } else {
            // 401이 아니면 정상 응답 반환
            return response;
        }
    } catch (error) {
        // 네트워크 에러 또는 재시도 실패 에러 처리
        console.error(`fetchWithAuth 실패 [${options.method || 'GET'} ${url}]:`, error);
        // 여기서 에러를 다시 던져서, 호출한 곳에서 처리하도록 함
        throw error;
    }
}

/**
 * 로그인 상태를 확인하는 함수
 * @returns {Promise<boolean>} 로그인되어 있지 않으면 false, 로그인되어 있으면 true를 반환
 */
async function checkLoginStatus() {
    try {
        const response = await fetchWithAuth('/user/v1/me');
        return response.ok;
    } catch (error) {
        console.error('인증 확인 실패:', error);
        return false;
    }
}

/**
 * 사용자 정보를 가져오는 함수
 * @returns {Promise<Object>} 사용자 정보 객체 또는 null
 */
async function getUserInfo() {
    try {
        const response = await fetchWithAuth('/user/v1/me');
        if (!response.ok) {
            return null;
        }
        return await response.json();
    } catch (error) {
        console.error('사용자 정보 조회 실패:', error);
        return null;
    }
}

/**
 * 로그아웃 처리 함수
 * @returns {Promise<boolean>} 로그아웃 성공 여부
 */
async function logout() {
    try {
        const response = await fetchWithAuth('/user/v1/logout', {
            method: 'POST',
        });
        if (response.ok) {
            clearTokens();
            window.location.href = '/login';
            return true;
        }
        return false;
    } catch (error) {
        console.error('로그아웃 실패:', error);
        return false;
    }
}

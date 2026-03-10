const LOGIN_ERROR_MESSAGE_BY_DETAIL = Object.freeze({
    'User account is not active':
        '가입 승인 대기 중입니다. 승인 완료 메일을 확인한 뒤 다시 로그인해 주세요.',
    'Invalid password': '비밀번호가 올바르지 않습니다. 다시 확인해 주세요.',
    'User not found': '등록된 계정을 찾을 수 없습니다. 회원가입 후 이용해 주세요.',
});

const DEFAULT_LOGIN_ERROR_MESSAGE =
    '로그인에 실패했습니다. 입력 정보를 확인한 뒤 다시 시도해 주세요.';
const NETWORK_ERROR_MESSAGE =
    '네트워크 오류로 로그인에 실패했습니다. 잠시 후 다시 시도해 주세요.';

function clearLoginFeedback() {
    const feedbackElement = document.getElementById('login-feedback');
    if (!feedbackElement) {
        return;
    }

    feedbackElement.hidden = true;
    feedbackElement.textContent = '';
}

function showLoginFeedback(message) {
    const feedbackElement = document.getElementById('login-feedback');
    if (!feedbackElement) {
        alert(message);
        return;
    }

    feedbackElement.textContent = message;
    feedbackElement.hidden = false;
}

async function parseLoginErrorMessage(response) {
    let detail = '';

    try {
        const errorData = await response.json();
        if (typeof errorData?.detail === 'string') {
            detail = errorData.detail;
        }
    } catch (_error) {
        // 응답 본문이 비어있거나 JSON 파싱이 불가한 경우 기본 메시지로 처리합니다.
    }

    return LOGIN_ERROR_MESSAGE_BY_DETAIL[detail] || DEFAULT_LOGIN_ERROR_MESSAGE;
}

async function handleLogin(event) {
    event.preventDefault();
    clearLoginFeedback();

    const email = document.getElementById('email').value;
    const password = document.getElementById('password').value;
    const rememberMe = document.getElementById('remember-me')?.checked || false;

    try {
        const response = await fetch(`${API_URL}/user/v1/login`, {
            method: 'POST',
            credentials: 'include',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                email,
                password,
            }),
        });

        if (!response.ok) {
            throw new Error(await parseLoginErrorMessage(response));
        }

        const data = await response.json();

        saveTokens(data.access_token, data.user_id, rememberMe);
        window.location.href = '/hotdeal';
    } catch (error) {
        const message = error instanceof Error ? error.message : NETWORK_ERROR_MESSAGE;
        showLoginFeedback(message || NETWORK_ERROR_MESSAGE);
        console.error('로그인 에러:', error);
    }
}

document.addEventListener('DOMContentLoaded', () => {
    const loginForm = document.getElementById('login-form');
    loginForm.addEventListener('submit', handleLogin);
});

const SIGNUP_ERROR_MESSAGE_BY_DETAIL = Object.freeze({
    'Email already registered':
        '이미 가입된 이메일입니다. 로그인하거나 다른 이메일로 다시 시도해 주세요.',
});

const DEFAULT_SIGNUP_ERROR_MESSAGE = '회원가입에 실패했습니다. 잠시 후 다시 시도해 주세요.';

function clearSignupFeedback() {
    const feedbackElement = document.getElementById('signup-feedback');
    if (!feedbackElement) {
        return;
    }

    feedbackElement.hidden = true;
    feedbackElement.textContent = '';
}

function showSignupFeedback(message) {
    const feedbackElement = document.getElementById('signup-feedback');
    if (!feedbackElement) {
        alert(message);
        return;
    }

    feedbackElement.textContent = message;
    feedbackElement.hidden = false;
}

function showPendingApprovalState({ email, nickname }) {
    const signupForm = document.getElementById('signup-form');
    const pendingContainer = document.getElementById('signup-pending');
    const pendingEmail = document.getElementById('pending-email');
    const pendingNickname = document.getElementById('pending-nickname');

    if (signupForm) {
        signupForm.classList.add('is-hidden');
    }
    if (pendingEmail) {
        pendingEmail.textContent = email;
    }
    if (pendingNickname) {
        pendingNickname.textContent = nickname;
    }
    if (pendingContainer) {
        pendingContainer.hidden = false;
    }
}

async function parseSignupErrorMessage(response) {
    try {
        const errorData = await response.json();
        const detail = typeof errorData?.detail === 'string' ? errorData.detail : '';
        return SIGNUP_ERROR_MESSAGE_BY_DETAIL[detail] || DEFAULT_SIGNUP_ERROR_MESSAGE;
    } catch (_error) {
        return DEFAULT_SIGNUP_ERROR_MESSAGE;
    }
}

async function handleSignup(event) {
    event.preventDefault();
    clearSignupFeedback();

    const email = document.getElementById('email').value;
    const password = document.getElementById('password').value;
    const passwordConfirm = document.getElementById('password-confirm').value;
    const nickname = document.getElementById('nickname').value;

    if (password !== passwordConfirm) {
        showSignupFeedback('비밀번호가 일치하지 않습니다.');
        return;
    }

    try {
        const response = await fetch(`${API_URL}/user/v1/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                email,
                password,
                nickname,
            }),
        });

        if (!response.ok) {
            throw new Error(await parseSignupErrorMessage(response));
        }

        await response.json();
        showPendingApprovalState({ email, nickname });
    } catch (error) {
        const message =
            error instanceof Error && error.message
                ? error.message
                : DEFAULT_SIGNUP_ERROR_MESSAGE;
        showSignupFeedback(message);
        console.error('회원가입 에러:', error);
    }
}

document.addEventListener('DOMContentLoaded', () => {
    const signupForm = document.getElementById('signup-form');
    signupForm.addEventListener('submit', handleSignup);
});

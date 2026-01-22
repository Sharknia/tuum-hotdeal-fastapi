async function handleLogin(event) {
    event.preventDefault();

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
            throw new Error('로그인에 실패했습니다.');
        }

        const data = await response.json();

        // 토큰 저장
        saveTokens(data.access_token, data.user_id, rememberMe);
        // 홈 페이지로 이동
        window.location.href = '/home';
    } catch (error) {
        alert(error.message);
        console.error('로그인 에러:', error);
    }
}

// 폼 제출 이벤트 리스너 등록
document.addEventListener('DOMContentLoaded', () => {
    const loginForm = document.getElementById('login-form');
    loginForm.addEventListener('submit', handleLogin);
});

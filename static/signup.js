async function handleSignup(event) {
    event.preventDefault();

    const email = document.getElementById('email').value;
    const password = document.getElementById('password').value;
    const passwordConfirm = document.getElementById('password-confirm').value;
    const nickname = document.getElementById('nickname').value;

    // 비밀번호 확인
    if (password !== passwordConfirm) {
        alert('비밀번호가 일치하지 않습니다.');
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
            const errorData = await response.json();
            throw new Error(errorData.detail || '회원가입에 실패했습니다.');
        }

        const data = await response.json();
        alert('회원가입이 완료되었습니다. 로그인 페이지로 이동합니다.');
        window.location.href = '/login';
    } catch (error) {
        alert(error.message);
        console.error('회원가입 에러:', error);
    }
}

// 폼 제출 이벤트 리스너 등록
document.addEventListener('DOMContentLoaded', () => {
    const signupForm = document.getElementById('signup-form');
    signupForm.addEventListener('submit', handleSignup);
});

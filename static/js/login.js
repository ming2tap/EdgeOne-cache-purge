document.getElementById('loginForm').addEventListener('submit', async function(e) {
    e.preventDefault();
    
    const formData = new FormData(this);
    const errorDiv = document.getElementById('errorMessage');
    errorDiv.textContent = '';
    
    try {
        const response = await fetch('/login', {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        if (data.success) {
            window.location.href = data.redirect;
        } else {
            errorDiv.textContent = data.message || '登录失败，请重试';
        }
    } catch (error) {
        errorDiv.textContent = '网络错误，请重试';
        console.error('Login error:', error);
    }
});

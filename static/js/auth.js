document.addEventListener('DOMContentLoaded', (event) => {
  const loginForm = document.querySelector('#login-form');
  if (loginForm) {
    loginForm.addEventListener('submit', handleLogin);
  }
});

async function handleLogin(e) {
  e.preventDefault();
  const response = await fetch('/login', {
    method: 'POST',
    body: new FormData(e.target),
    credentials: 'include'
  });
  if (response.ok) {
    window.location.href = '/dashboard';
  } else {
    const errorData = await response.json();
    alert(`Login failed: ${errorData.detail}`);
  }
}

function authenticatedFetch(url, options = {}) {
  return fetch(url, {
    ...options,
    credentials: 'include'
  });
}
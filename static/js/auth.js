// Event listener for when the DOM content is fully loaded
document.addEventListener('DOMContentLoaded', (event) => {
// Runs when the DOM is fully loaded
// Finds the login form and attaches the handleLogin function to its submit event
  const loginForm = document.querySelector('#login-form');
  if (loginForm) {
    loginForm.addEventListener('submit', handleLogin);
  }
});

// Handles the login form submission
/* This function:
  1. Prevents the default form submission
  2. Sends a POST request to the / login endpoint with form data
  3. Redirects to the dashboard on successful login
  4. Displays an alert with the error message on login failure 
*/
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

/*
  Wrapper function for fetch that includes credentials in the request
  Ensures that all requests made through it include credentials,
  which is necessary for sending the auth token with each request
*/
function authenticatedFetch(url, options = {}) {
  return fetch(url, {
    ...options,
    credentials: 'include'
  });
}
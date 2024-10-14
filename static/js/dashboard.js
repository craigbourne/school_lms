// Asynchronously loads the dashboard content
async function loadDashboard() {
  /* 
  Makes an authenticated request to / dashboard endpoint.
  If successful, replaces body content with the dashboard HTML.
  If unsuccessful (for example, user not authenticated), redirects to login page
  */

  const response = await authenticatedFetch('/dashboard');
  if (response.ok) {
    const dashboardHtml = await response.text();
    document.body.innerHTML = dashboardHtml;
  } else {
    window.location.href = '/login';
  }
}

// Immediately invoke the loadDashboard function when the script is loaded
loadDashboard();
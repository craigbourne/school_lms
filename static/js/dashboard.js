async function loadDashboard() {
  const response = await authenticatedFetch('/dashboard');
  if (response.ok) {
    const dashboardHtml = await response.text();
    document.body.innerHTML = dashboardHtml;
  } else {
    window.location.href = '/login';
  }
}

loadDashboard();
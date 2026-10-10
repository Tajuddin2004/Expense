/**
 * API Service for Communicating with Django REST Framework Backend
 */

const isLocalDevFrontOnly = window.location.origin.includes(':5500') || 
                            window.location.origin.includes(':3000') || 
                            window.location.protocol === 'file:';

const API_BASE = isLocalDevFrontOnly 
  ? 'http://127.0.0.1:8000/api'
  : `${window.location.origin}/api`;

let currentCsrfToken = null;

function getCookie(name) {
  let cookieValue = null;
  if (document.cookie && document.cookie !== '') {
    const cookies = document.cookie.split(';');
    for (let i = 0; i < cookies.length; i++) {
      const cookie = cookies[i].trim();
      if (cookie.substring(0, name.length + 1) === (name + '=')) {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
        break;
      }
    }
  }
  return cookieValue;
}

// Fetch CSRF token on startup
async function initCsrf() {
  try {
    const res = await fetch(`${API_BASE}/auth/csrf/`, { credentials: 'include' });
    const data = await res.json();
    if (data && data.csrfToken) {
      currentCsrfToken = data.csrfToken;
    }
  } catch (err) {
    // Backend may still be loading
  }
}
initCsrf();

async function apiRequest(endpoint, method = 'GET', body = null) {
  // If we don't have a CSRF token yet and it's a mutating request, try to fetch it
  if (!currentCsrfToken && method !== 'GET') {
    await initCsrf();
  }

  const headers = {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
  };

  const csrftoken = currentCsrfToken || getCookie('csrftoken');
  if (csrftoken) {
    headers['X-CSRFToken'] = csrftoken;
  }

  const options = {
    method,
    headers,
    credentials: 'include', // Includes Django session cookies
  };

  if (body) {
    options.body = JSON.stringify(body);
  }

  try {
    const response = await fetch(`${API_BASE}${endpoint}`, options);
    const data = await response.json().catch(() => ({}));
    
    if (!response.ok) {
      let errorMessage = 'An error occurred';
      if (data.error) errorMessage = data.error;
      else if (data.message) errorMessage = data.message;
      else if (typeof data === 'object') {
        const firstKey = Object.keys(data)[0];
        if (firstKey) {
          const val = data[firstKey];
          errorMessage = Array.isArray(val) ? `${firstKey}: ${val[0]}` : `${firstKey}: ${val}`;
        }
      }
      return { success: false, status: response.status, error: errorMessage, data };
    }
    return { success: true, status: response.status, data };
  } catch (err) {
    return { success: false, status: 0, error: 'Could not connect to backend server. Make sure Django is running.' };
  }
}

const API = {
  // Auth
  getCurrentUser: () => apiRequest('/auth/user/'),
  signup: (username, email, password, confirm_password, name = '') => 
    apiRequest('/auth/signup/', 'POST', { username, email, password, confirm_password, name }),
  verifyOtp: (email, otp_code) => 
    apiRequest('/auth/verify-otp/', 'POST', { email, otp_code }),
  resendOtp: (email) => 
    apiRequest('/auth/resend-otp/', 'POST', { email }),
  signin: (username_or_email, password) => 
    apiRequest('/auth/signin/', 'POST', { username_or_email, password }),
  signout: () => 
    apiRequest('/auth/signout/', 'POST'),
  forgotPassword: (email) => 
    apiRequest('/auth/forgot-password/', 'POST', { email }),
  resetPassword: (email, otp_code, new_password, confirm_password) => 
    apiRequest('/auth/reset-password/', 'POST', { email, otp_code, new_password, confirm_password }),

  // Expenses & Dashboard
  getDashboard: () => apiRequest('/expenses/dashboard/'),
  getExpenses: () => apiRequest('/expenses/'),
  createExpense: (expenseData) => apiRequest('/expenses/', 'POST', expenseData),
  updateExpense: (id, expenseData) => apiRequest(`/expenses/${id}/`, 'PUT', expenseData),
  deleteExpense: (id) => apiRequest(`/expenses/${id}/`, 'DELETE'),
};

window.API = API;

/**
 * Client Application - Dynamic State, Modals & View Management
 */

// Global State
const State = {
  user: null,
  currentView: 'landing',
  expenses: [],
  dashboardData: null,
  pendingEmail: '',
  editingExpenseId: null,
  deletingExpenseId: null,
};

// Toast Notifications
function showToast(message, type = 'success') {
  const container = document.getElementById('toast-container');
  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;
  toast.innerHTML = `<span>${message}</span>`;
  container.appendChild(toast);
  setTimeout(() => {
    toast.style.opacity = '0';
    setTimeout(() => toast.remove(), 300);
  }, 4000);
}

// Router & View Management
function navigateTo(viewName) {
  // If requesting dashboard or expenses while not logged in, show signin
  if ((viewName === 'dashboard' || viewName === 'expenses') && !State.user) {
    showAuthModal('signin');
    return;
  }

  // Update views
  document.querySelectorAll('.view').forEach(v => v.classList.remove('active'));
  const targetView = document.getElementById(`view-${viewName}`);
  
  if (targetView) {
    targetView.classList.add('active');
    State.currentView = viewName;
  } else {
    // 404 View
    document.getElementById('view-404').classList.add('active');
    State.currentView = '404';
  }

  // Notify canvas animations of view change
  document.dispatchEvent(new CustomEvent('viewChanged', { detail: State.currentView }));

  // Update navigation link highlights
  document.querySelectorAll('.nav-link').forEach(link => {
    link.classList.toggle('active', link.dataset.view === viewName);
  });

  // Load view-specific data
  if (viewName === 'dashboard') loadDashboard();
  if (viewName === 'expenses') loadExpenses();
  window.scrollTo({ top: 0, behavior: 'smooth' });
}

// Modals
function openModal(modalId) {
  document.getElementById(modalId).classList.add('active');
}

function closeModal(modalId) {
  document.getElementById(modalId).classList.remove('active');
}

function showAuthModal(type) {
  closeModal('modal-signup');
  closeModal('modal-otp');
  closeModal('modal-signin');
  closeModal('modal-forgot');
  closeModal('modal-reset');
  openModal(`modal-${type}`);
}

// Render Navbar based on Auth State
function updateNavbar() {
  const navLinks = document.getElementById('nav-links');
  if (State.user) {
    navLinks.innerHTML = `
      <li><a class="nav-link ${State.currentView === 'dashboard' ? 'active' : ''}" onclick="navigateTo('dashboard')">Dashboard</a></li>
      <li><a class="nav-link ${State.currentView === 'expenses' ? 'active' : ''}" onclick="navigateTo('expenses')">All Expenses</a></li>
      <li><button class="btn btn-primary btn-sm" onclick="openExpenseModal()">+ Add Expense</button></li>
      <li style="margin-left: 0.5rem; display: flex; align-items: center; gap: 0.6rem;">
        <span style="font-size: 0.85rem; font-weight: 600; color: var(--slate-600);">👤 ${State.user.username}</span>
        <button class="btn btn-secondary btn-sm" onclick="handleSignout()">Sign Out</button>
      </li>
    `;
  } else {
    navLinks.innerHTML = `
      <li><a class="nav-link" onclick="navigateTo('landing')">Home</a></li>
      <li><a class="nav-link" onclick="showAuthModal('signin')">Sign In</a></li>
      <li><button class="btn btn-primary btn-sm" onclick="showAuthModal('signup')">Sign Up</button></li>
    `;
  }
}

// Check initial auth state
async function checkAuth() {
  const res = await API.getCurrentUser();
  if (res.success && res.data.authenticated) {
    State.user = res.data.user;
    updateNavbar();
    if (State.currentView === 'landing') {
      navigateTo('dashboard');
    }
  } else {
    State.user = null;
    updateNavbar();
    navigateTo('landing');
  }
}

// Auth Handlers
async function handleSignup(e) {
  e.preventDefault();
  const nameInput = document.getElementById('signup-name');
  const name = nameInput ? nameInput.value.trim() : '';
  const username = document.getElementById('signup-username').value.trim();
  const email = document.getElementById('signup-email').value.trim();
  const password = document.getElementById('signup-password').value;
  const confirm = document.getElementById('signup-confirm').value;

  const res = await API.signup(username, email, password, confirm, name);
  if (res.success) {
    State.pendingEmail = email;
    document.getElementById('otp-target-email').textContent = email;
    closeModal('modal-signup');
    showAuthModal('otp');
    showToast(res.data.message || 'OTP sent! Please check your email.', 'success');
  } else {
    showToast(res.error, 'error');
  }
}

async function handleVerifyOtp(e) {
  e.preventDefault();
  const otpCode = document.getElementById('otp-code').value.trim();
  const res = await API.verifyOtp(State.pendingEmail, otpCode);
  if (res.success) {
    State.user = res.data.user;
    closeModal('modal-otp');
    updateNavbar();
    showToast(res.data.message, 'success');
    navigateTo('dashboard');
  } else {
    showToast(res.error, 'error');
  }
}

async function handleResendOtp() {
  if (!State.pendingEmail) return;
  const res = await API.resendOtp(State.pendingEmail);
  if (res.success) {
    showToast('A fresh OTP has been sent to your email!', 'info');
  } else {
    showToast(res.error, 'error');
  }
}

async function handleSignin(e) {
  e.preventDefault();
  const username_or_email = document.getElementById('signin-identity').value.trim();
  const password = document.getElementById('signin-password').value;

  const res = await API.signin(username_or_email, password);
  if (res.success) {
    State.user = res.data.user;
    closeModal('modal-signin');
    updateNavbar();
    showToast(`Welcome back, ${State.user.username}!`, 'success');
    navigateTo('dashboard');
  } else if (res.data && res.data.unverified) {
    State.pendingEmail = res.data.email;
    document.getElementById('otp-target-email').textContent = State.pendingEmail;
    closeModal('modal-signin');
    showAuthModal('otp');
    showToast(res.error, 'info');
  } else {
    showToast(res.error, 'error');
  }
}

async function handleSignout() {
  await API.signout();
  State.user = null;
  updateNavbar();
  showToast('You have been signed out.', 'info');
  navigateTo('landing');
}

async function handleForgotPassword(e) {
  e.preventDefault();
  const email = document.getElementById('forgot-email').value.trim();
  const res = await API.forgotPassword(email);
  if (res.success) {
    State.pendingEmail = email;
    document.getElementById('reset-target-email').textContent = email;
    closeModal('modal-forgot');
    showAuthModal('reset');
    showToast(res.data.message, 'success');
  } else {
    showToast(res.error, 'error');
  }
}

async function handleResetPassword(e) {
  e.preventDefault();
  const otpCode = document.getElementById('reset-otp').value.trim();
  const newPassword = document.getElementById('reset-password').value;
  const confirmPassword = document.getElementById('reset-confirm').value;

  const res = await API.resetPassword(State.pendingEmail, otpCode, newPassword, confirmPassword);
  if (res.success) {
    closeModal('modal-reset');
    showToast(res.data.message, 'success');
    showAuthModal('signin');
  } else {
    showToast(res.error, 'error');
  }
}

// Dashboard View
async function loadDashboard() {
  const res = await API.getDashboard();
  if (!res.success) {
    showToast(res.error, 'error');
    return;
  }
  const d = res.data;
  State.dashboardData = d;

  document.getElementById('dash-total').textContent = `₹${d.total_spending.toFixed(2)}`;
  document.getElementById('dash-month').textContent = `₹${d.current_month_spending.toFixed(2)}`;
  document.getElementById('dash-month-name').textContent = d.current_month_name;
  document.getElementById('dash-count').textContent = d.expense_count;

  // Categories
  const catContainer = document.getElementById('dash-categories');
  if (d.category_summary && d.category_summary.length > 0) {
    catContainer.innerHTML = d.category_summary.map(cat => {
      const pct = d.total_spending > 0 ? (cat.total / d.total_spending) * 100 : 0;
      return `
        <div class="category-item">
          <div class="category-row-header">
            <div>
              <span class="badge badge-${cat.category}">${cat.category}</span>
              <span style="font-size: 0.8rem; color: var(--slate-500); margin-left: 0.4rem;">(${cat.count} items)</span>
            </div>
            <span style="font-weight: 700; color: var(--slate-900);">₹${cat.total.toFixed(2)}</span>
          </div>
          <div class="category-bar-bg">
            <div class="category-bar-fill" style="width: ${pct.toFixed(1)}%;"></div>
          </div>
        </div>
      `;
    }).join('');
  } else {
    catContainer.innerHTML = `<div class="empty-state" style="padding: 2rem 1rem;"><p class="empty-state-title" style="font-size: 1rem;">No spending recorded yet</p></div>`;
  }

  // Recent Expenses
  const recentTable = document.getElementById('dash-recent');
  if (d.recent_expenses && d.recent_expenses.length > 0) {
    recentTable.innerHTML = `
      <table class="data-table">
        <tbody>
          ${d.recent_expenses.map(e => `
            <tr>
              <td>
                <div style="font-weight: 600; color: var(--slate-900);">${e.title}</div>
                <div style="font-size: 0.775rem; color: var(--slate-400);">
                  ${e.date} &bull; <span class="badge badge-${e.category}" style="padding: 0.1rem 0.4rem; font-size: 0.7rem;">${e.category}</span>
                </div>
              </td>
              <td style="text-align: right; font-weight: 700; color: var(--slate-900);">₹${parseFloat(e.amount).toFixed(2)}</td>
            </tr>
          `).join('')}
        </tbody>
      </table>
    `;
  } else {
    recentTable.innerHTML = `<div class="empty-state" style="padding: 2rem 1rem;"><div class="empty-state-icon">💸</div><p class="empty-state-title">No expenses yet</p><button class="btn btn-primary btn-sm" onclick="openExpenseModal()">+ Add Expense</button></div>`;
  }
}

// Expenses CRUD View
async function loadExpenses() {
  const res = await API.getExpenses();
  if (!res.success) {
    showToast(res.error, 'error');
    return;
  }
  State.expenses = res.data;
  renderExpensesList();
}

function renderExpensesList() {
  const container = document.getElementById('expenses-table-container');
  const countEl = document.getElementById('expenses-count-total');
  
  const total = State.expenses.reduce((sum, e) => sum + parseFloat(e.amount), 0);
  countEl.textContent = `${State.expenses.length} transaction(s) • Total: ₹${total.toFixed(2)}`;

  if (State.expenses.length === 0) {
    container.innerHTML = `
      <div class="empty-state">
        <div class="empty-state-icon">📋</div>
        <h2 class="empty-state-title">No expenses recorded</h2>
        <p class="empty-state-text">Track your spending by adding your first expense.</p>
        <button class="btn btn-primary" onclick="openExpenseModal()">+ Add New Expense</button>
      </div>
    `;
    return;
  }

  container.innerHTML = `
    <div class="table-responsive">
      <table class="data-table">
        <thead>
          <tr>
            <th>Date</th>
            <th>Title &amp; Notes</th>
            <th>Category</th>
            <th style="text-align: right;">Amount</th>
            <th style="text-align: right;">Actions</th>
          </tr>
        </thead>
        <tbody>
          ${State.expenses.map(e => `
            <tr>
              <td style="white-space: nowrap; font-weight: 500; color: var(--slate-600);">${e.date}</td>
              <td>
                <div style="font-weight: 600; color: var(--slate-900);">${e.title}</div>
                ${e.description ? `<div style="font-size: 0.8rem; color: var(--slate-500); margin-top: 0.2rem;">${e.description}</div>` : ''}
              </td>
              <td><span class="badge badge-${e.category}">${e.category}</span></td>
              <td style="text-align: right; font-weight: 700; color: var(--slate-900);">₹${parseFloat(e.amount).toFixed(2)}</td>
              <td>
                <div style="display: flex; gap: 0.4rem; justify-content: flex-end;">
                  <button class="btn btn-secondary btn-sm" onclick="editExpense(${e.id})">Edit</button>
                  <button class="btn btn-danger btn-sm" onclick="confirmDeleteExpense(${e.id}, '${e.title}', ${e.amount})">Delete</button>
                </div>
              </td>
            </tr>
          `).join('')}
        </tbody>
      </table>
    </div>
  `;
}

// Expense Add/Edit Modal
function openExpenseModal(expense = null) {
  const titleEl = document.getElementById('modal-expense-title-text');
  const submitBtn = document.getElementById('expense-submit-btn');
  
  if (expense) {
    State.editingExpenseId = expense.id;
    titleEl.textContent = `Edit Expense: ${expense.title}`;
    submitBtn.textContent = 'Save Changes';
    document.getElementById('exp-title').value = expense.title;
    document.getElementById('exp-amount').value = expense.amount;
    document.getElementById('exp-category').value = expense.category;
    document.getElementById('exp-date').value = expense.date;
    document.getElementById('exp-description').value = expense.description || '';
  } else {
    State.editingExpenseId = null;
    titleEl.textContent = 'Add New Expense';
    submitBtn.textContent = 'Add Expense';
    document.getElementById('exp-title').value = '';
    document.getElementById('exp-amount').value = '';
    document.getElementById('exp-category').value = 'Food';
    document.getElementById('exp-date').value = new Date().toISOString().split('T')[0];
    document.getElementById('exp-description').value = '';
  }
  openModal('modal-expense');
}

function editExpense(id) {
  const expense = State.expenses.find(e => e.id === id);
  if (expense) openExpenseModal(expense);
}

async function handleSaveExpense(e) {
  e.preventDefault();
  const data = {
    title: document.getElementById('exp-title').value.trim(),
    amount: document.getElementById('exp-amount').value,
    category: document.getElementById('exp-category').value,
    date: document.getElementById('exp-date').value,
    description: document.getElementById('exp-description').value.trim(),
  };

  let res;
  if (State.editingExpenseId) {
    res = await API.updateExpense(State.editingExpenseId, data);
  } else {
    res = await API.createExpense(data);
  }

  if (res.success) {
    closeModal('modal-expense');
    showToast(State.editingExpenseId ? 'Expense updated successfully!' : 'Expense added successfully!', 'success');
    if (State.currentView === 'expenses') loadExpenses();
    if (State.currentView === 'dashboard') loadDashboard();
  } else {
    showToast(res.error, 'error');
  }
}

// Delete Confirmation Modal
function confirmDeleteExpense(id, title, amount) {
  State.deletingExpenseId = id;
  document.getElementById('del-title').textContent = title;
  document.getElementById('del-amount').textContent = `₹${parseFloat(amount).toFixed(2)}`;
  openModal('modal-delete');
}

async function handleConfirmDelete() {
  if (!State.deletingExpenseId) return;
  const res = await API.deleteExpense(State.deletingExpenseId);
  closeModal('modal-delete');
  if (res.success) {
    showToast(res.data.message || 'Expense deleted.', 'success');
    if (State.currentView === 'expenses') loadExpenses();
    if (State.currentView === 'dashboard') loadDashboard();
  } else {
    showToast(res.error, 'error');
  }
}

// Initialization on DOM load
document.addEventListener('DOMContentLoaded', () => {
  checkAuth();
});

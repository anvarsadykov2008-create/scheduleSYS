/**
 * Main Application Logic
 */
const ui = {
  currentPageId: 'page-public',
  toastQueue: [],
  isToastActive: false,

  init() {
    this.setupNavigation();
    
    // Initial page parsing based on URL hash or path
    // For simplicity in this demo, defaulting to public schedule
    this.navigate('page-public');

    // Initialize subsystems
    Auth.init();
    Schedule.init();
  },

  navigate(pageId) {
    // Hide all pages
    document.querySelectorAll('.page').forEach(p => p.hidden = true);
    
    // Show target page
    const target = document.getElementById(pageId);
    if (target) {
      target.hidden = false;
      this.currentPageId = pageId;
      
      // Update body class for specific layouts if needed
      if (pageId === 'page-auth' || pageId.includes('login')) {
         document.body.style.overflow = 'hidden';
      } else {
         document.body.style.overflow = '';
      }
    }
  },

  setupNavigation() {
    // Setup generic navigation intercept
    document.addEventListener('click', (e) => {
      const a = e.target.closest('a');
      if (a && a.getAttribute('href')?.startsWith('/')) {
        e.preventDefault();
        const href = a.getAttribute('href');
        
        if (href === '/' || href === '/index.html') {
          this.navigate('page-public');
        } else if (href === '/login.html') {
          this.navigate('page-login');
        } else if (href === '/dashboard.html') {
          if (Auth.user) this.navigate('page-dashboard');
          else this.navigate('page-login');
        }
      }
    });

    // Sidebar toggle (Mobile)
    const toggleBtn = document.getElementById('sidebar-toggle');
    const closeBtn = document.getElementById('sidebar-close');
    const sidebar = document.getElementById('sidebar');

    toggleBtn?.addEventListener('click', () => {
      sidebar?.classList.add('open');
    });

    closeBtn?.addEventListener('click', () => {
      sidebar?.classList.remove('open');
    });
    
    // Auto-close sidebar on mobile nav click
    document.querySelectorAll('.sidebar-link').forEach(link => {
       link.addEventListener('click', () => {
           if(window.innerWidth < 1024) {
               sidebar?.classList.remove('open');
           }
       });
    });
  },

  updateUserInterface(user) {
    const navUserArea = document.getElementById('nav-user-area');
    const dbSections = {
      admin: document.getElementById('nav-admin-section'),
      student: document.getElementById('nav-student-section'),
      teacher: document.getElementById('nav-teacher-section')
    };

    if (user) {
      // Top navbar
      if (navUserArea) {
        navUserArea.innerHTML = `
          <div style="display:flex; align-items:center; gap:var(--space-3)">
            <span style="font-size:var(--text-sm); color:var(--color-text-muted)">${user.full_name}</span>
            <a href="/dashboard.html" class="btn btn-primary btn-sm">
              Панель управления
            </a>
          </div>
        `;
      }

      // Sidebar content
      const avatarBtn = document.getElementById('sidebar-avatar');
      const userName = document.getElementById('sidebar-username');
      const userRole = document.getElementById('sidebar-role');

      if (avatarBtn) avatarBtn.textContent = user.full_name.charAt(0).toUpperCase();
      if (userName) userName.textContent = user.full_name;
      if (userRole) userRole.textContent = user.role;

      // Hide all nav sections
      Object.values(dbSections).forEach(el => el && (el.hidden = true));

      // Show specific nav section based on role
      if (user.role === 'студент' && dbSections.student) {
         dbSections.student.hidden = false;
      } else if (user.role === 'преподаватель' && dbSections.teacher) {
         dbSections.teacher.hidden = false;
      } else if (['администратор', 'учебная_часть', 'диспетчер'].includes(user.role) && dbSections.admin) {
         dbSections.admin.hidden = false;
      }

    } else {
      // Reset to public view
      if (navUserArea) {
        navUserArea.innerHTML = `
          <a href="/login.html" class="btn btn-ghost btn-sm" onclick="ui.navigate('page-login'); return false;">Войти</a>
        `;
      }
    }
  },

  setLoading(buttonElement, isLoading) {
    if (!buttonElement) return;
    const text = buttonElement.querySelector('.btn-text');
    const spinner = buttonElement.querySelector('.btn-spinner');
    
    if (isLoading) {
      buttonElement.disabled = true;
      if (text) text.hidden = true;
      if (spinner) spinner.hidden = false;
    } else {
      buttonElement.disabled = false;
      if (text) text.hidden = false;
      if (spinner) spinner.hidden = true;
    }
  },

  showToast(message, type = 'info') {
    this.toastQueue.push({ message, type });
    this.processToasts();
  },

  processToasts() {
    if (this.isToastActive || this.toastQueue.length === 0) return;

    this.isToastActive = true;
    const toastData = this.toastQueue.shift();
    const container = document.getElementById('toast-container');
    
    if (!container) return;

    const toast = document.createElement('div');
    toast.className = `toast toast-${toastData.type}`;
    
    // Icon based on type
    let icon = '';
    if (toastData.type === 'success') {
      icon = '<svg width="20" height="20" fill="var(--color-success)" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"/></svg>';
    } else if (toastData.type === 'error') {
      icon = '<svg width="20" height="20" fill="var(--color-danger)" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clip-rule="evenodd"/></svg>';
    } else {
      icon = '<svg width="20" height="20" fill="var(--color-primary)" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clip-rule="evenodd"/></svg>';
    }

    toast.innerHTML = `
      ${icon}
      <div style="flex:1; font-size:var(--text-sm)">${toastData.message}</div>
    `;

    container.appendChild(toast);

    setTimeout(() => {
      toast.classList.add('toast-closing');
      toast.addEventListener('animationend', () => {
        toast.remove();
        this.isToastActive = false;
        this.processToasts();
      });
    }, 4000); // 4 sec display time
  }
};

// Global helper for Auth page (called by HTML onclick)
window.switchTab = function(tabName) {
  document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
  document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
  
  document.getElementById(`tab-${tabName}`).classList.add('active');
  const panel = document.getElementById(`panel-${tabName}`);
  panel.classList.add('active');
  panel.hidden = false;
  
  if (tabName === 'login') {
    document.getElementById('panel-register').hidden = true;
  } else {
    document.getElementById('panel-login').hidden = true;
  }
};

window.togglePassword = function(inputId, btn) {
  const input = document.getElementById(inputId);
  if (input.type === 'password') {
    input.type = 'text';
    btn.innerHTML = '<svg class="eye-icon" viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M3.707 2.293a1 1 0 00-1.414 1.414l14 14a1 1 0 001.414-1.414l-1.473-1.473A10.014 10.014 0 0019.542 10C18.268 5.943 14.478 3 10 3a9.958 9.958 0 00-4.512 1.074l-1.78-1.781zm4.261 4.26l1.514 1.515a2.003 2.003 0 012.45 2.45l1.514 1.514a4 4 0 00-5.478-5.478z" clip-rule="evenodd"/><path d="M12.454 16.697L9.75 13.992a4 4 0 01-3.742-3.741L2.335 6.578A9.98 9.98 0 00.458 10c1.274 4.057 5.065 7 9.542 7 .847 0 1.669-.105 2.454-.303z"/></svg>';
  } else {
    input.type = 'password';
    btn.innerHTML = '<svg class="eye-icon" viewBox="0 0 20 20" fill="currentColor"><path d="M10 3C5 3 1.73 7.11 1 10c.73 2.89 4 7 9 7s8.27-4.11 9-7c-.73-2.89-4-7-9-7zm0 12a5 5 0 110-10 5 5 0 010 10zm0-2a3 3 0 100-6 3 3 0 000 6z"/></svg>';
  }
};

// Bootstrap application once DOM is fully loaded
document.addEventListener('DOMContentLoaded', () => {
   ui.init();
});

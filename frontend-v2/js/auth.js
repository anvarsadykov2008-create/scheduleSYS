/**
 * Auth controller
 */
const Auth = {
  user: null,

  async init() {
    this.checkAuth();
    this.setupListeners();
    await this.loadInitialData();
  },

  setupListeners() {
    document.getElementById('form-login')?.addEventListener('submit', (e) => this.handleLogin(e));
    document.getElementById('form-register')?.addEventListener('submit', (e) => this.handleRegister(e));
    document.getElementById('btn-logout')?.addEventListener('click', () => this.logout());
    
    // React to 401s from API
    window.addEventListener('auth:unauthorized', () => {
      ui.showToast('Сессия истекла. Пожалуйста, войдите снова.', 'error');
      this.logout();
    });
  },

  async loadInitialData() {
    try {
      // Load groups for registration dropdown
      const regGroupSelect = document.getElementById('reg-group');
      if (regGroupSelect) {
        const groups = await window.api.getGroups();
        regGroupSelect.innerHTML = '<option value="">Не выбрано (для преподавателей)</option>';
        groups.forEach(g => {
          regGroupSelect.innerHTML += `<option value="${g.id}">${g.name}</option>`;
        });
      }
    } catch (e) {
      console.error("Failed to load generic data for auth", e);
    }
  },

  async checkAuth() {
    const token = localStorage.getItem('access_token');
    
    if (token) {
      try {
        this.user = await window.api.getMe();
        ui.updateUserInterface(this.user);
        
        // If we're on login page, redirect to dashboard
        if (ui.currentPageId === 'page-login') {
          ui.navigate('page-dashboard');
        }
      } catch (e) {
        console.error("Token invalid or expired");
        this.logout();
      }
    } else {
      ui.updateUserInterface(null);
    }
  },

  async handleLogin(e) {
    e.preventDefault();
    const btn = document.getElementById('btn-login');
    const iinInput = document.getElementById('login-iin');
    const passInput = document.getElementById('login-password');
    const errorBox = document.getElementById('login-error');
    const iinError = document.getElementById('login-iin-error');
    
    // Basic validation
    let isValid = true;
    iinError.textContent = '';
    
    if (iinInput.value.trim().length !== 12 || !/^\d+$/.test(iinInput.value.trim())) {
      iinError.textContent = 'ИИН должен состоять из 12 цифр';
      isValid = false;
    }
    
    if (!isValid) return;

    ui.setLoading(btn, true);
    errorBox.hidden = true;

    try {
      const response = await window.api.login(iinInput.value.trim(), passInput.value);
      localStorage.setItem('access_token', response.access_token);
      ui.showToast('Вы успешно вошли в систему', 'success');
      await this.checkAuth();
    } catch (error) {
      errorBox.textContent = error.message;
      errorBox.hidden = false;
    } finally {
      ui.setLoading(btn, false);
    }
  },

  async handleRegister(e) {
    e.preventDefault();
    const btn = document.getElementById('btn-register');
    const iinInput = document.getElementById('reg-iin');
    const nameInput = document.getElementById('reg-name');
    const roleSelect = document.getElementById('reg-role');
    const groupSelect = document.getElementById('reg-group');
    
    const errorBox = document.getElementById('reg-error');
    const successBox = document.getElementById('reg-success');
    
    ui.setLoading(btn, true);
    errorBox.hidden = true;
    successBox.hidden = true;

    const payload = {
      iin: iinInput.value.trim(),
      full_name: nameInput.value.trim(),
      role: roleSelect.value,
      group_id: groupSelect.value ? parseInt(groupSelect.value) : null
    };

    try {
      const response = await window.api.register(payload);
      
      // Auto-set the password to the one returned
      document.getElementById('login-iin').value = payload.iin;
      document.getElementById('login-password').value = response.password;
      
      successBox.textContent = `Успешно! ${response.message}. Войдите в систему.`;
      successBox.hidden = false;
      
      // Switch back to login tab after 3 seconds
      setTimeout(() => {
        switchTab('login');
        // Actually login
        document.getElementById('btn-login').click();
      }, 3000);
      
    } catch (error) {
      errorBox.textContent = error.message;
      errorBox.hidden = false;
    } finally {
      ui.setLoading(btn, false);
    }
  },

  logout() {
    localStorage.removeItem('access_token');
    this.user = null;
    ui.updateUserInterface(null);
    ui.navigate('page-public');
    ui.showToast('Вы вышли из системы');
  }
};

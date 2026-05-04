const API_CONFIG = {
  BASE_URL: 'http://localhost:8000/api', // Adjust if deployed
};

class ApiService {
  /**
   * Universal fetch wrapper
   */
  async request(endpoint, options = {}) {
    const url = `${API_CONFIG.BASE_URL}${endpoint}`;
    
    // Setup headers
    const headers = new Headers(options.headers || {});
    if (!headers.has('Content-Type') && !(options.body instanceof FormData)) {
      headers.set('Content-Type', 'application/json');
    }
    
    // Add Auth token if available
    const token = localStorage.getItem('access_token');
    if (token) {
      headers.set('Authorization', `Bearer ${token}`);
    }
    
    try {
      const response = await fetch(url, {
        ...options,
        headers
      });
      
      const isJson = response.headers.get('content-type')?.includes('application/json');
      const data = isJson ? await response.json() : await response.text();
      
      if (!response.ok) {
        // Handle 401 Unauthorized globally
        if (response.status === 401) {
          localStorage.removeItem('access_token');
          window.dispatchEvent(new Event('auth:unauthorized'));
        }
        
        throw new Error(data.detail || data.message || `API Error: ${response.status}`);
      }
      
      return data;
      
    } catch (error) {
      console.error(`[API Error] ${endpoint}:`, error);
      throw error;
    }
  }

  // Auth
  async login(username, password) {
    const params = new URLSearchParams();
    params.append('username', username);
    params.append('password', password);
    
    return this.request('/auth/token', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded'
      },
      body: params
    });
  }

  async register(data) {
    return this.request('/auth/register', {
      method: 'POST',
      body: JSON.stringify(data)
    });
  }

  async getMe() {
    return this.request('/auth/users/me');
  }

  // Data fetching
  async getGroups() {
    return this.request('/groups');
  }

  async getPublicVersions(semesterId = null) {
    const query = semesterId ? `?semester_id=${semesterId}` : '';
    return this.request(`/schedule/public/versions${query}`);
  }

  async getScheduleEntries(versionId, groupId = null, teacherId = null) {
    const params = new URLSearchParams();
    if (groupId) params.append('group_id', groupId);
    if (teacherId) params.append('teacher_id', teacherId);
    
    // Using detailed entries for public view
    return this.request(`/schedule/versions/${versionId}/entries/detailed?${params.toString()}`);
  }
}

window.api = new ApiService();

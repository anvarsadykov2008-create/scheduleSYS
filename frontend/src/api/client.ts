const getApiUrl = (): string => {
    if (import.meta.env.VITE_API_URL) {
        return import.meta.env.VITE_API_URL;
    }
    // Везде используем относительный путь /api. 
    // В dev он проксируется через Vite (vite.config.ts), 
    // в prod обслуживается сервером (FastAPI или Nginx).
    return "/api";
};

export const API_URL = getApiUrl();

const authHeaders = (): Record<string, string> => {
    const token = localStorage.getItem('token');
    return token ? { 'Authorization': `Bearer ${token}` } : {};
};

async function throwApiError(response: Response): Promise<never> {
    let detail: string;
    try {
        const body = await response.json();
        detail = body?.detail
            ? (Array.isArray(body.detail)
                ? body.detail.map((e: { msg?: string }) => e.msg || JSON.stringify(e)).join('; ')
                : String(body.detail))
            : response.statusText;
    } catch {
        detail = response.statusText;
    }
    throw new Error(detail);
}

export const apiClient = {
    get: async <T>(endpoint: string): Promise<T> => {
        const response = await fetch(`${API_URL}${endpoint}`, {
            headers: { ...authHeaders() },
        });
        if (!response.ok) await throwApiError(response);
        return response.json();
    },

    post: async <T>(endpoint: string, data: unknown): Promise<T> => {
        const response = await fetch(`${API_URL}${endpoint}`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                ...authHeaders(),
            },
            body: JSON.stringify(data),
        });
        if (!response.ok) await throwApiError(response);
        return response.json();
    },

    put: async <T>(endpoint: string, data: unknown): Promise<T> => {
        const response = await fetch(`${API_URL}${endpoint}`, {
            method: "PUT",
            headers: {
                "Content-Type": "application/json",
                ...authHeaders(),
            },
            body: JSON.stringify(data),
        });
        if (!response.ok) await throwApiError(response);
        return response.json();
    },

    delete: async (endpoint: string): Promise<void> => {
        const response = await fetch(`${API_URL}${endpoint}`, {
            method: "DELETE",
            headers: { ...authHeaders() },
        });
        if (!response.ok) await throwApiError(response);
    },

    // Загрузка двоичного файла (например, .xlsx)
    fetchBlob: async (endpoint: string): Promise<Blob> => {
        const response = await fetch(`${API_URL}${endpoint}`, {
            headers: { ...authHeaders() },
        });
        if (!response.ok) {
            throw new Error(`API Error: ${response.statusText}`);
        }
        return response.blob();
    },

    postFile: async <T>(endpoint: string, file: File): Promise<T> => {
        const formData = new FormData();
        formData.append("file", file);
        const response = await fetch(`${API_URL}${endpoint}`, {
            method: "POST",
            headers: {
                ...authHeaders(),
            },
            body: formData,
        });
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.detail || `API Error: ${response.statusText}`);
        }
        return response.json();
    },
};

import axios from 'axios';

const API_URL = 'http://localhost:8000/api';

// Create axios instance with default config
const api = axios.create({
    baseURL: API_URL,
    headers: {
        'Content-Type': 'application/json',
    },
});

// Add token to requests if it exists
api.interceptors.request.use(
    (config) => {
        const token = localStorage.getItem('access_token');
        if (token) {
            config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
    },
    (error) => {
        return Promise.reject(error);
    }
);

// Profile API functions
export const getProfile = async () => {
    try {
        const response = await api.get('/profile/me/');
        return response.data;
    } catch (error) {
        throw new Error(error.response?.data?.message || 'Failed to fetch profile');
    }
};

export const updateProfile = async (profileData) => {
    try {
        const response = await api.patch('/profile/me/', profileData);
        return response.data;
    } catch (error) {
        throw new Error(error.response?.data?.message || 'Failed to update profile');
    }
};

export const updateTheme = async (theme) => {
    try {
        const response = await api.post('/profile/update-theme/', { theme });
        return response.data;
    } catch (error) {
        throw new Error(error.response?.data?.message || 'Failed to update theme');
    }
};

export const updateNotifications = async (preferences) => {
    try {
        const response = await api.post('/profile/update-notifications/', { preferences });
        return response.data;
    } catch (error) {
        throw new Error(error.response?.data?.message || 'Failed to update notifications');
    }
};

export const uploadAvatar = async (file) => {
    try {
        const formData = new FormData();
        formData.append('avatar', file);

        const response = await api.post('/profile/upload-avatar/', formData, {
            headers: {
                'Content-Type': 'multipart/form-data',
            },
        });
        return response.data;
    } catch (error) {
        throw new Error(error.response?.data?.message || 'Failed to upload avatar');
    }
};

export const removeAvatar = async () => {
    try {
        const response = await api.delete('/profile/remove-avatar/');
        return response.data;
    } catch (error) {
        throw new Error(error.response?.data?.message || 'Failed to remove avatar');
    }
};

export const getProfileStats = async () => {
    try {
        const response = await api.get('/profile/stats/');
        return response.data;
    } catch (error) {
        throw new Error(error.response?.data?.message || 'Failed to fetch profile stats');
    }
};

// Task API functions
export const deleteTask = async (taskId) => {
    try {
        const response = await api.delete(`/tasks/${taskId}/`);
        return response.data;
    } catch (error) {
        throw new Error(error.response?.data?.message || 'Failed to delete task');
    }
};

// Task management functions
export const markTaskCompleted = async (taskId) => {
    try {
        const response = await api.post(`/tasks/${taskId}/mark_completed/`);
        return response.data;
    } catch (error) {
        throw new Error(error.response?.data?.message || 'Failed to mark task as completed');
    }
};

export const getTasksByCategory = async () => {
    try {
        const response = await api.get('/tasks/by_category/');
        return response.data;
    } catch (error) {
        throw new Error(error.response?.data?.message || 'Failed to fetch tasks by category');
    }
};

export const getUpcomingTasks = async (days = 7) => {
    try {
        const response = await api.get(`/tasks/upcoming/?days=${days}`);
        return response.data;
    } catch (error) {
        throw new Error(error.response?.data?.message || 'Failed to fetch upcoming tasks');
    }
};

// Authentication functions
export const login = async (email, password) => {
    try {
        const response = await api.post('/users/login/', { email, password });
        const { access, refresh, user } = response.data;
        
        // Store tokens
        localStorage.setItem('access_token', access);
        localStorage.setItem('refresh_token', refresh);
        
        return user;
    } catch (error) {
        throw new Error(error.response?.data?.message || 'Login failed');
    }
};

export const register = async (userData) => {
    try {
        const response = await api.post('/users/register/', userData);
        const { access, refresh, user } = response.data;
        
        // Store tokens
        localStorage.setItem('access_token', access);
        localStorage.setItem('refresh_token', refresh);
        
        return user;
    } catch (error) {
        throw new Error(error.response?.data?.message || 'Registration failed');
    }
};

export const logout = () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
};

export const refreshToken = async () => {
    try {
        const refresh = localStorage.getItem('refresh_token');
        if (!refresh) throw new Error('No refresh token available');

        const response = await api.post('/users/token-refresh/', {
            refresh,
        });
        
        const { access } = response.data;
        localStorage.setItem('access_token', access);
        
        return access;
    } catch (error) {
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        throw new Error('Session expired. Please login again.');
    }
};

// Error handling interceptor
api.interceptors.response.use(
    (response) => response,
    async (error) => {
        const originalRequest = error.config;

        // If error is 401 and we haven't tried to refresh the token yet
        if (error.response?.status === 401 && !originalRequest._retry) {
            originalRequest._retry = true;

            try {
                await refreshToken();
                // Retry the original request with new token
                return api(originalRequest);
            } catch (refreshError) {
                // If refresh token fails, logout user
                logout();
                throw refreshError;
            }
        }

        return Promise.reject(error);
    }
); 
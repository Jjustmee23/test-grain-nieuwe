import axios from 'axios';

// API Configuration
export const API_BASE_URL = process.env.REACT_APP_API_URL || '/api';
export const WS_URL = process.env.REACT_APP_WS_URL || 'ws://localhost:5000';

// Create axios instance with base configuration
export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true,
});

// Connection status monitoring
let isBackendConnected = true;

export const getConnectionStatus = () => isBackendConnected;

// Request interceptor to add auth token
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('accessToken');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor for error handling
apiClient.interceptors.response.use(
  (response) => {
    // Backend is responding, mark as connected
    isBackendConnected = true;
    return response;
  },
  async (error) => {
    const originalRequest = error.config;

    // Check if it's a network error
    if (!error.response) {
      isBackendConnected = false;
      console.error('Backend connection failed:', error.message);
      return Promise.reject(new Error('Backend server is unavailable. Please try again later.'));
    }

    isBackendConnected = true;

    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      try {
        const refreshToken = localStorage.getItem('refreshToken');
        if (refreshToken) {
          const response = await axios.post(`${API_BASE_URL}/auth/refresh`, {
            refreshToken,
          });

          const { accessToken } = response.data;
          localStorage.setItem('accessToken', accessToken);

          // Retry original request with new token
          originalRequest.headers.Authorization = `Bearer ${accessToken}`;
          return apiClient(originalRequest);
        }
      } catch (refreshError) {
        // Refresh failed, clear tokens and redirect to login
        localStorage.removeItem('accessToken');
        localStorage.removeItem('refreshToken');
        window.location.href = '/login';
      }
    }

    return Promise.reject(error);
  }
);

// Health check utility
export const checkBackendHealth = async () => {
  try {
    const response = await axios.get(`${API_BASE_URL.replace('/api', '')}/health`, {
      timeout: 5000
    });
    isBackendConnected = true;
    return response.data;
  } catch (error) {
    isBackendConnected = false;
    throw error;
  }
};

export default apiClient;
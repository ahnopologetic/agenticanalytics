import axios, { type AxiosError, type AxiosInstance, type AxiosRequestConfig } from 'axios';
import { supabase } from '../supabaseClient';

export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000';

// Create axios instance
const axiosInstance: AxiosInstance = axios.create({
    baseURL: API_BASE_URL,
    headers: {
        'Content-Type': 'application/json',
    },
});

// Request interceptor for adding auth token
axiosInstance.interceptors.request.use(
    async (config) => {
        const session = (await supabase.auth.getSession()).data.session;
        const token = session?.access_token;

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
axiosInstance.interceptors.response.use(
    (response) => response,
    (error: AxiosError) => {
        // Handle specific error cases
        if (error.response?.status === 401) {
            // Handle unauthorized error (e.g., redirect to login)
            console.error('Authentication error');
            // Could dispatch to auth store or redirect
        }

        return Promise.reject(error);
    }
);

export const createAPIRequest = <T>(config: AxiosRequestConfig): Promise<T> => {
    return axiosInstance(config)
        .then((response) => response.data)
        .catch((error) => {
            console.error('API Error:', error);
            throw error;
        });
};

export default axiosInstance; 
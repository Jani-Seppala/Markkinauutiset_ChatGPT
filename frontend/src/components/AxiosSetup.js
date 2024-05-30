import axios from 'axios';

const axiosInstance = axios.create({
    baseURL: process.env.REACT_APP_API_BASE_URL
});

axiosInstance.interceptors.response.use(
    response => response,
    error => {
        console.error("Interceptor caught an error: ", error.response);
        if (error.response && error.response.status === 401) {
            // Force a redirect to the login page
            window.dispatchEvent(new CustomEvent('token-expiration'));
            window.location.href = '/login';  // Direct manipulation of window.location
        }
        return Promise.reject(error);
    }
);

export default axiosInstance;

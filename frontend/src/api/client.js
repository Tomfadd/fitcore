import axios from 'axios';

const API = axios.create({
  baseURL: process.env.REACT_APP_API_URL || 'http://localhost:8000',
  withCredentials: true,
});

// Attach token to every request
API.interceptors.request.use((config) => {
  const token = sessionStorage.getItem('access_token');
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

// Auto-refresh on 401
API.interceptors.response.use(
  (res) => res,
  async (err) => {
    if (err.response?.status === 401 && !err.config._retry) {
      err.config._retry = true;
      try {
        const { data } = await axios.post('/api/auth/refresh', {}, { withCredentials: true });
        sessionStorage.setItem('access_token', data.access_token);
        err.config.headers.Authorization = `Bearer ${data.access_token}`;
        return API(err.config);
      } catch {
        sessionStorage.removeItem('access_token');
        window.location.href = '/login';
      }
    }
    return Promise.reject(err);
  }
);

export default API;

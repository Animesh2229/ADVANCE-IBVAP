import axios from 'axios';

// Use HTTPS in production. Override with EXPO_PUBLIC_API_URL.
const BASE_URL =
  (typeof process !== 'undefined' && process.env?.EXPO_PUBLIC_API_URL) ||
  'https://YOUR_CENTRAL_HOST/api/v1';

const api = axios.create({
  baseURL: BASE_URL,
  timeout: 15000,
});

export default api;

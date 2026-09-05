import axios from 'axios';

// Change this to your Central server IP when testing on device
const BASE_URL = 'http://YOUR_CENTRAL_IP:8000/api/v1';

const api = axios.create({
  baseURL: BASE_URL,
  timeout: 10000,
});

export default api;

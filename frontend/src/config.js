// Dynamic API and WebSocket configuration supporting both localhost and local Wi-Fi LAN access (e.g. mobile phones)
const hostname = typeof window !== 'undefined' && window.location && window.location.hostname
  ? window.location.hostname
  : 'localhost';

export const API_BASE = import.meta.env.VITE_API_BASE || `http://${hostname}:8000/api/v1`;
export const WS_BASE = import.meta.env.VITE_WS_URL || `ws://${hostname}:8000/ws/bot/`;
export const DEFAULT_DEV_KEY = 'dee2cbd5d1693aa6d5b113a31649a0501d7da3b3661348dcd8481b84584e0e66';

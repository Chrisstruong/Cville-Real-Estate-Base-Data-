const apiBaseUrl = import.meta.env.VITE_API_BASE_URL?.trim().replace(/\/+$/, "") ?? "";

// Relative URLs use the local Vite proxy. Production can point to a separate API.
export function apiUrl(path: `/api/${string}`): string {
  return `${apiBaseUrl}${path}`;
}

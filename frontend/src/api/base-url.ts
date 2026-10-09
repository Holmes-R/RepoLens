export function getApiBaseUrl(configuredUrl?: string): string {
  const baseUrl = (configuredUrl?.trim() || '/api').replace(/\/+$/, '');
  if (!baseUrl) return '/api';

  // Accept a backend origin as well as an explicit API base path.
  if (/^https?:\/\/[^/]+$/i.test(baseUrl)) return `${baseUrl}/api`;
  return baseUrl;
}

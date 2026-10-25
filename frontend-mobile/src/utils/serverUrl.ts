import AsyncStorage from '@react-native-async-storage/async-storage';
import { API_CONFIG, STORAGE_KEYS } from './constants';

const HEALTH_TIMEOUT_MS = 8000;

let cachedUrl: string | null = null;

/** Trims, strips trailing slashes and requires an http(s) scheme; returns null when invalid. */
export function normalizeServerUrl(raw: string): string | null {
  const url = raw.trim().replace(/\/+$/, '');
  return /^https?:\/\/[^\s/]+/i.test(url) ? url : null;
}

/** Resolution order: memory cache, AsyncStorage, then the build-time default. */
export async function getServerUrl(): Promise<string> {
  if (cachedUrl) return cachedUrl;
  try {
    const stored = await AsyncStorage.getItem(STORAGE_KEYS.SERVER_URL);
    const normalized = stored ? normalizeServerUrl(stored) : null;
    if (normalized) {
      cachedUrl = normalized;
      return normalized;
    }
  } catch {
    // Storage unavailable: fall back to the build-time default.
  }
  return API_CONFIG.BASE_URL.replace(/\/+$/, '');
}

/** Removes stored auth so a token issued by one server is never sent to another. */
async function clearStoredSession(): Promise<void> {
  const keys = await AsyncStorage.getAllKeys();
  const authKeys = keys.filter(
    (k) => k === STORAGE_KEYS.JWT_TOKEN || k.startsWith(STORAGE_KEYS.SESSION_PREFIX)
  );
  if (authKeys.length > 0) await AsyncStorage.multiRemove(authKeys);
}

/** Persists the URL; when it differs from the active one, the stored session is cleared first. */
export async function setServerUrl(url: string): Promise<void> {
  const normalized = normalizeServerUrl(url);
  if (!normalized) throw new Error('La URL del servidor no es válida.');
  if (normalized !== (await getServerUrl())) await clearStoredSession();
  await AsyncStorage.setItem(STORAGE_KEYS.SERVER_URL, normalized);
  cachedUrl = normalized;
}

/** True only when `<url>/api/v1/health` answers HTTP 200 within the timeout. */
export async function checkServerHealth(url: string): Promise<boolean> {
  const normalized = normalizeServerUrl(url);
  if (!normalized) return false;
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), HEALTH_TIMEOUT_MS);
  try {
    const res = await fetch(`${normalized}/api/v1/health`, {
      headers: { Accept: 'application/json' },
      signal: controller.signal,
    });
    return res.status === 200;
  } catch {
    return false;
  } finally {
    clearTimeout(timer);
  }
}

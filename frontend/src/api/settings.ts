import type { UserSettings } from '../types'
import { authHeaders, http } from './http'
import { apiUrls } from './urls'

export async function fetchSettings(token: string): Promise<UserSettings> {
  const res = await http.get<UserSettings>(apiUrls.settings.get, {
    headers: authHeaders(token),
  })
  return res.data
}

export async function updateSettings(
  token: string,
  settings: UserSettings,
): Promise<UserSettings> {
  const res = await http.put<UserSettings>(apiUrls.settings.update, settings, {
    headers: authHeaders(token),
  })
  return res.data
}

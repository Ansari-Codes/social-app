import { callAPI, getToken } from '@/Core/api';
import { publishDataChange } from '@/Stores/dataChanges';
import type { ProfileData, ProfilePublic, ProfileUpdatePayload } from '../Types/profile.type';

let myProfileCache: { data: ProfilePublic; viewerKey: string } | null = null;
const inFlightMyProfilePromises = new Map<string, Promise<ProfilePublic>>();

export function invalidateMyProfileCache(): void {
  myProfileCache = null;
}

export async function getMyProfile(force = false): Promise<ProfilePublic> {
  const viewerKey = getToken() ?? 'guest';
  if (!force && myProfileCache?.viewerKey === viewerKey) {
    return myProfileCache.data;
  }

  const inFlight = inFlightMyProfilePromises.get(viewerKey);
  if (inFlight) return inFlight;

  const request = (async () => {
    const res = await callAPI<ProfileData>('/profiles/me');
    if ((getToken() ?? 'guest') === viewerKey) {
      myProfileCache = { data: res.profile, viewerKey };
    }
    return res.profile;
  })().finally(() => {
    inFlightMyProfilePromises.delete(viewerKey);
  });
  inFlightMyProfilePromises.set(viewerKey, request);
  return request;
}

export async function getProfileByUsername(username: string): Promise<ProfilePublic> {
  const res = await callAPI<ProfileData>(
    `/profiles/by-username/${encodeURIComponent(username)}`,
  );
  return res.profile;
}

export async function updateMyProfile(payload: ProfileUpdatePayload): Promise<ProfilePublic> {
  const res = await callAPI<ProfileData>('/profiles/me', {
    method: 'PATCH',
    body: payload,
  });
  myProfileCache = { data: res.profile, viewerKey: getToken() ?? 'guest' };
  publishDataChange({ type: 'profile-updated', profile: res.profile });
  return res.profile;
}

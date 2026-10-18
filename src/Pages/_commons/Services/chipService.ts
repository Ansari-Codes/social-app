import { callAPI } from '@/Core/api';
import { publishDataChange } from '@/Stores/dataChanges';
import type { ProfilePublic } from '../Types/profile.type';
import type { Profile } from '@/Pages/App/Types/feed.type';

interface DataProfile {
    profile: ProfilePublic;
}

interface DataProfiles {
    profiles: ProfilePublic[];
}

function toProfile(data: ProfilePublic): Profile {
    return {
        id: data.id,
        userId: data.user_id,
        username: data.username,
        display_name: data.display_name,
        email: data.email ?? undefined,
        about: data.about ?? undefined,
        powerline: data.powerline ?? undefined,
        bannerColor: data.banner_color ?? undefined,
        emoji: data.emoji ?? undefined,
        phone: data.phone ?? undefined,
        birthday: data.birthday ?? undefined,
        followers: data.followers,
        following: data.following,
        stars: data.stars,
        isOwner: data.is_owner,
        followedByMe: data.followed_by_me,
        starredByMe: data.starred_by_me,
        reactions: data.reactions,
        myReactions: data.my_reactions,
    };
}

export async function setProfileFollow(userId: number, enabled: boolean): Promise<Profile> {
    const data = await callAPI<DataProfile>(`/profiles/${userId}/follow`, {
        method: enabled ? 'POST' : 'DELETE',
    });
    const profile = toProfile(data.profile);
    publishDataChange({ type: 'profile-relation-updated', profile });
    return profile;
}

export async function setProfileStar(userId: number, enabled: boolean): Promise<Profile> {
    const data = await callAPI<DataProfile>(`/profiles/${userId}/star`, {
        method: enabled ? 'POST' : 'DELETE',
    });
    const profile = toProfile(data.profile);
    publishDataChange({ type: 'profile-relation-updated', profile });
    return profile;
}

export async function toggleProfileReaction(userId: number, reaction: string): Promise<Profile> {
    const data = await callAPI<DataProfile>(`/profiles/${userId}/reactions`, {
        method: 'POST',
        body: { reaction },
    });
    const profile = toProfile(data.profile);
    publishDataChange({ type: 'profile-relation-updated', profile });
    return profile;
}

export async function getProfileConnections(
    userId: number,
    direction: 'followers' | 'following',
): Promise<Profile[]> {
    const data = await callAPI<DataProfiles>(`/profiles/${userId}/${direction}`);
    return data.profiles.map(toProfile);
}

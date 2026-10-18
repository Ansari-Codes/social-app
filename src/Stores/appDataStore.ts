import { defineStore } from 'pinia';
import { ref } from 'vue';
import { getToken } from '@/Core/api';
import type { Post, Profile } from '@/Pages/App/Types/feed.type';
import { getDashboardAnalytics } from '@/Pages/_commons/Services/analyticsService';
import { getNotifications, markAllNotificationsRead, markNotificationRead } from '@/Pages/_commons/Services/notificationService';
import { getMyPosts } from '@/Pages/_commons/Services/postService';
import { getProfileConnections } from '@/Pages/_commons/Services/chipService';
import { getMyProfile, getProfileByUsername } from '@/Pages/_commons/Services/profileService';
import type { DashboardAnalyticsData } from '@/Pages/_commons/Types/analytics.type';
import type { NotificationData } from '@/Pages/_commons/Types/notification.type';
import type { ProfilePublic } from '@/Pages/_commons/Types/profile.type';
import { subscribeDataChanges } from './dataChanges';

export const useAppDataStore = defineStore('app-data', () => {
    const myProfile = ref<ProfilePublic | null>(null);
    const myProfileLoaded = ref(false);
    const publicProfiles = ref<Record<string, ProfilePublic>>({});
    const profileConnections = ref<Record<string, Profile[]>>({});
    const analytics = ref<Record<number, DashboardAnalyticsData>>({});
    const analyticsLoaded = ref<Record<number, boolean>>({});
    const notifications = ref<NotificationData | null>(null);
    const notificationsLoaded = ref(false);
    const myPosts = ref<Post[]>([]);
    const myPostsLoaded = ref(false);
    let viewerKey = getToken() ?? 'guest';
    let myProfileRequest: Promise<ProfilePublic> | null = null;
    let notificationsRequest: Promise<NotificationData> | null = null;
    let myPostsRequest: Promise<Post[]> | null = null;
    const profileRequests = new Map<string, Promise<ProfilePublic>>();
    const analyticsRequests = new Map<number, Promise<DashboardAnalyticsData>>();
    const connectionRequests = new Map<string, Promise<Profile[]>>();

    function reset() {
        myProfile.value = null;
        myProfileLoaded.value = false;
        publicProfiles.value = {};
        profileConnections.value = {};
        analytics.value = {};
        analyticsLoaded.value = {};
        notifications.value = null;
        notificationsLoaded.value = false;
        myPosts.value = [];
        myPostsLoaded.value = false;
        myProfileRequest = null;
        notificationsRequest = null;
        myPostsRequest = null;
        profileRequests.clear();
        analyticsRequests.clear();
        connectionRequests.clear();
    }

    function syncViewer() {
        const nextViewerKey = getToken() ?? 'guest';
        if (viewerKey !== nextViewerKey) {
            viewerKey = nextViewerKey;
            reset();
        }
    }

    async function loadMyProfile(force = false): Promise<ProfilePublic> {
        syncViewer();
        if (!force && myProfileLoaded.value && myProfile.value) return myProfile.value;
        if (myProfileRequest) return myProfileRequest;

        const requestedViewer = viewerKey;
        const request = getMyProfile(true).then((profile) => {
            if ((getToken() ?? 'guest') === requestedViewer) {
                myProfile.value = profile;
                myProfileLoaded.value = true;
            }
            return profile;
        }).finally(() => {
            if (myProfileRequest === request) myProfileRequest = null;
        });
        myProfileRequest = request;
        return request;
    }

    async function loadProfile(username: string, force = false): Promise<ProfilePublic> {
        syncViewer();
        const key = username.toLowerCase();
        const cached = publicProfiles.value[key];
        if (!force && cached) return cached;
        const inFlight = profileRequests.get(key);
        if (inFlight) return inFlight;

        const requestedViewer = viewerKey;
        const request = getProfileByUsername(username).then((profile) => {
            if ((getToken() ?? 'guest') === requestedViewer) {
                publicProfiles.value[key] = profile;
            }
            return profile;
        }).finally(() => {
            if (profileRequests.get(key) === request) profileRequests.delete(key);
        });
        profileRequests.set(key, request);
        return request;
    }

    async function loadConnections(
        userId: number,
        direction: 'followers' | 'following',
        force = false,
    ): Promise<Profile[]> {
        syncViewer();
        const key = `${userId}:${direction}`;
        if (!force && profileConnections.value[key]) return profileConnections.value[key];
        const inFlight = connectionRequests.get(key);
        if (inFlight) return inFlight;

        const requestedViewer = viewerKey;
        const request = getProfileConnections(userId, direction).then((profiles) => {
            if ((getToken() ?? 'guest') === requestedViewer) profileConnections.value[key] = profiles;
            return profiles;
        }).finally(() => {
            if (connectionRequests.get(key) === request) connectionRequests.delete(key);
        });
        connectionRequests.set(key, request);
        return request;
    }

    async function loadAnalytics(days: number, force = false): Promise<DashboardAnalyticsData> {
        syncViewer();
        if (!force && analyticsLoaded.value[days]) return analytics.value[days];
        const inFlight = analyticsRequests.get(days);
        if (inFlight) return inFlight;

        const requestedViewer = viewerKey;
        const request = getDashboardAnalytics(days).then((result) => {
            if ((getToken() ?? 'guest') === requestedViewer) {
                analytics.value[days] = result;
                analyticsLoaded.value[days] = true;
            }
            return result;
        }).finally(() => {
            if (analyticsRequests.get(days) === request) analyticsRequests.delete(days);
        });
        analyticsRequests.set(days, request);
        return request;
    }

    async function loadNotifications(force = false): Promise<NotificationData> {
        syncViewer();
        if (!force && notificationsLoaded.value && notifications.value) return notifications.value;
        if (notificationsRequest) return notificationsRequest;

        const requestedViewer = viewerKey;
        const request = getNotifications().then((result) => {
            if ((getToken() ?? 'guest') === requestedViewer) {
                notifications.value = result;
                notificationsLoaded.value = true;
            }
            return result;
        }).finally(() => {
            if (notificationsRequest === request) notificationsRequest = null;
        });
        notificationsRequest = request;
        return request;
    }

    async function markRead(notificationId: number): Promise<void> {
        await markNotificationRead(notificationId);
        if (!notifications.value) return;
        const item = notifications.value.notifications.find((notification) => notification.id === notificationId);
        if (item && !item.is_read) {
            item.is_read = true;
            notifications.value.unread_count = Math.max(0, notifications.value.unread_count - 1);
        }
    }

    async function markAllRead(): Promise<void> {
        await markAllNotificationsRead();
        if (!notifications.value) return;
        notifications.value.notifications = notifications.value.notifications.map((item) => ({ ...item, is_read: true }));
        notifications.value.unread_count = 0;
    }

    async function loadMyPosts(force = false): Promise<Post[]> {
        syncViewer();
        if (!force && myPostsLoaded.value) return myPosts.value;
        if (myPostsRequest) return myPostsRequest;

        const requestedViewer = viewerKey;
        const request = getMyPosts().then((result) => {
            if ((getToken() ?? 'guest') === requestedViewer) {
                myPosts.value = result;
                myPostsLoaded.value = true;
            }
            return result;
        }).finally(() => {
            if (myPostsRequest === request) myPostsRequest = null;
        });
        myPostsRequest = request;
        return request;
    }

    subscribeDataChanges((change) => {
        if (change.type === 'viewer-changed') {
            viewerKey = getToken() ?? 'guest';
            reset();
        } else if (change.type === 'profile-updated') {
            myProfile.value = change.profile;
            myProfileLoaded.value = true;
            publicProfiles.value = {};
            publicProfiles.value[change.profile.username.toLowerCase()] = change.profile;
        } else if (change.type === 'account-updated') {
            if (myProfile.value?.user_id === change.userId) {
                myProfile.value.username = change.username;
                myProfile.value.email = change.email;
            }
            publicProfiles.value = {};
            myPosts.value = myPosts.value.map((post) => post.userId === change.userId
                ? { ...post, profile: { ...post.profile, username: change.username, email: change.email } }
                : post);
        } else if (change.type === 'profile-relation-updated') {
            myProfileLoaded.value = false;
            publicProfiles.value = {};
            profileConnections.value = {};
            analytics.value = {};
            analyticsLoaded.value = {};
        } else if (change.type.startsWith('post-') || change.type === 'comment-created') {
            analytics.value = {};
            analyticsLoaded.value = {};
            if (change.type === 'post-created' && myPostsLoaded.value) {
                if (!myPosts.value.some((post) => post.id === change.post.id)) myPosts.value.unshift(change.post);
            } else if ((change.type === 'post-updated' || change.type === 'post-reaction') && myPostsLoaded.value) {
                const index = myPosts.value.findIndex((post) => post.id === change.post.id);
                if (index !== -1) myPosts.value.splice(index, 1, change.post);
            } else if (change.type === 'post-deleted' || change.type === 'comment-created') {
                myPostsLoaded.value = false;
            }
        }
    });

    return {
        myProfile,
        myProfileLoaded,
        publicProfiles,
        profileConnections,
        analytics,
        analyticsLoaded,
        notifications,
        notificationsLoaded,
        myPosts,
        myPostsLoaded,
        loadMyProfile,
        loadProfile,
        loadConnections,
        loadAnalytics,
        loadNotifications,
        markRead,
        markAllRead,
        loadMyPosts,
        reset,
    };
});
import { defineStore } from 'pinia';
import { ref } from 'vue';
import { getToken } from '@/Core/api';
import type { Post } from '@/Pages/App/Types/feed.type';
import { getFeedPage } from '@/Pages/_commons/Services/feedService';
import { subscribeDataChanges } from './dataChanges';

export const useFeedStore = defineStore('feed', () => {
	const posts = ref<Post[]>([]);
	const nextCursor = ref<number | null>(null);
	const loaded = ref(false);
	const loading = ref(false);
	const loadingMore = ref(false);
	let viewerKey = getToken() ?? 'guest';
	let firstPageRequest: Promise<void> | null = null;
	let moreRequest: Promise<void> | null = null;

	function reset() {
		posts.value = [];
		nextCursor.value = null;
		loaded.value = false;
		loading.value = false;
		loadingMore.value = false;
		firstPageRequest = null;
		moreRequest = null;
	}

	function syncViewer() {
		const nextViewerKey = getToken() ?? 'guest';
		if (viewerKey !== nextViewerKey) {
			viewerKey = nextViewerKey;
			reset();
		}
	}

	async function load(force = false): Promise<void> {
		syncViewer();
		if (loaded.value && !force) return;
		if (firstPageRequest) return firstPageRequest;

		const requestedViewer = viewerKey;
		loading.value = true;
		let request!: Promise<void>;
		request = (async () => {
			try {
				const page = await getFeedPage(undefined, true);
				if ((getToken() ?? 'guest') !== requestedViewer) return;
				posts.value = page.posts;
				nextCursor.value = page.nextCursor;
				loaded.value = true;
			} finally {
				if (firstPageRequest === request) {
					loading.value = false;
					firstPageRequest = null;
				}
			}
		})();
		firstPageRequest = request;
		return request;
	}

	async function loadMore(): Promise<void> {
		syncViewer();
		if (!loaded.value) await load();
		if (nextCursor.value === null || moreRequest) return moreRequest ?? undefined;

		const requestedViewer = viewerKey;
		const cursor = nextCursor.value;
		loadingMore.value = true;
		let request!: Promise<void>;
		request = (async () => {
			try {
				const page = await getFeedPage(cursor, true);
				if ((getToken() ?? 'guest') !== requestedViewer) return;
				const seen = new Set(posts.value.map((post) => post.id));
				posts.value.push(...page.posts.filter((post) => !seen.has(post.id)));
				nextCursor.value = page.nextCursor;
			} finally {
				if (moreRequest === request) {
					loadingMore.value = false;
					moreRequest = null;
				}
			}
		})();
		moreRequest = request;
		return request;
	}

	function addPost(post: Post) {
		if (!loaded.value || posts.value.some((item) => item.id === post.id)) return;
		posts.value.unshift(post);
	}

	function replacePost(post: Post) {
		const index = posts.value.findIndex((item) => item.id === post.id);
		if (index !== -1) posts.value.splice(index, 1, post);
	}

	function removePost(postId: number) {
		posts.value = posts.value.filter((post) => post.id !== postId);
	}

	subscribeDataChanges((change) => {
		if (change.type === 'viewer-changed') {
			viewerKey = getToken() ?? 'guest';
			reset();
		} else if (change.type === 'post-created') {
			addPost(change.post);
		} else if (change.type === 'post-updated' || change.type === 'post-reaction') {
			replacePost(change.post);
		} else if (change.type === 'post-deleted') {
			removePost(change.postId);
		} else if (change.type === 'comment-created') {
			const post = posts.value.find((item) => item.id === change.postId);
			if (post) post.comments += 1;
		} else if (change.type === 'profile-relation-updated') {
			posts.value = posts.value.map((post) => post.profile.userId === change.profile.userId
				? { ...post, profile: { ...post.profile, ...change.profile } }
				: post);
		} else if (change.type === 'profile-updated') {
			posts.value = posts.value.map((post) => post.profile.userId === change.profile.user_id
				? {
					...post,
					profile: {
						...post.profile,
						username: change.profile.username,
						display_name: change.profile.display_name,
						about: change.profile.about ?? undefined,
						powerline: change.profile.powerline ?? undefined,
						bannerColor: change.profile.banner_color ?? undefined,
						emoji: change.profile.emoji ?? undefined,
					},
				}
				: post);
		} else if (change.type === 'account-updated') {
			posts.value = posts.value.map((post) => post.profile.userId === change.userId
				? { ...post, profile: { ...post.profile, username: change.username, email: change.email } }
				: post);
		}
	});

	return {
		posts,
		nextCursor,
		loaded,
		loading,
		loadingMore,
		load,
		loadMore,
		addPost,
		replacePost,
		removePost,
		reset,
	};
});

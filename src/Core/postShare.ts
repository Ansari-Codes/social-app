import { BASE_URL } from '@/Core/config';

export function sharedPostIdFromLocation(): number | null {
    const hashQuery = window.location.hash.split('?')[1] ?? '';
    const value = new URLSearchParams(hashQuery).get('post_id')
        ?? new URLSearchParams(window.location.search).get('post_id');
    const match = value?.match(/^\d+$/);
    return match ? Number(match[0]) : null;
}

export function setSharedPostLocation(postId: number | null): void {
    const url = new URL(window.location.href);
    if (url.hash.startsWith('#/')) {
        const queryIndex = url.hash.indexOf('?');
        const route = queryIndex === -1 ? url.hash : url.hash.slice(0, queryIndex);
        const params = new URLSearchParams(queryIndex === -1 ? '' : url.hash.slice(queryIndex + 1));
        if (postId === null) params.delete('post_id');
        else params.set('post_id', String(postId));
        url.hash = `${route}${params.size ? `?${params}` : ''}`;
    } else {
        if (postId === null) url.searchParams.delete('post_id');
        else url.searchParams.set('post_id', String(postId));
    }
    window.history.replaceState(window.history.state, '', `${url.pathname}${url.search}${url.hash}`);
}

async function copyText(text: string): Promise<void> {
    if (navigator.clipboard?.writeText) {
        await navigator.clipboard.writeText(text);
        return;
    }

    const input = document.createElement('textarea');
    input.value = text;
    input.style.position = 'fixed';
    input.style.opacity = '0';
    document.body.append(input);
    input.select();
    const copied = document.execCommand('copy');
    input.remove();
    if (!copied) throw new Error('Unable to copy the post link.');
}

export async function sharePost(
    postId: number,
    content: string,
    profileId?: number,
): Promise<'shared' | 'copied'> {
    const url = new URL(BASE_URL, window.location.origin);
    const params = new URLSearchParams({ post_id: String(postId) });
    if (profileId !== undefined) params.set('profile_id', String(profileId));
    url.hash = `/post/${postId}?${params}`;

    if (navigator.share) {
        await navigator.share({ title: 'Post on SilenceBook', text: content, url: url.toString() });
        return 'shared';
    }

    await copyText(`${content}\n\n${url.toString()}`);
    return 'copied';
}
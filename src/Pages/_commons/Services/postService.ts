import { callAPI } from '@/Core/api';
import { publishDataChange } from '@/Stores/dataChanges';
import type { Comment, Comments, Post, Profile } from '@/Pages/App/Types/feed.type';
import { invalidateFeedCache } from './feedService';

export interface ApiPost {
  id: number;
  root_post_id: number;
  user_id: number;
  profile: {
    id: number;
    user_id: number;
    username: string;
    display_name: string | null;
    emoji: string | null;
    about: string | null;
    powerline: string | null;
    banner_color: string | null;
    birthday: string | null;
    phone: string | null;
    email: string | null;
    followers: number;
    following: number;
    stars: number;
    followed_by_me: boolean;
    starred_by_me: boolean;
    reactions: Record<string, number>;
    my_reactions: string[];
  };
  content: string;
  reply_to: number | null;
  reply_to_author?: string | null;
  reply_to_snippet?: string | null;
  is_comment: boolean;
  created_at: string;
  updated_at: string;
  reactions: Record<string, number>;
  my_reactions: string[];
  comments: number;
}

export interface DataPosts {
  posts: ApiPost[];
  next_cursor?: number | null;
}

interface DataPost {
  post: ApiPost;
}

interface DataComments {
  post_id: number;
  comments: ApiPost[];
}

interface DataOk {
  ok: boolean;
}

function toProfile(source: ApiPost['profile']): Profile {
  return {
    id: source.id,
    userId: source.user_id,
    username: source.username,
    display_name: source.display_name,
    emoji: source.emoji ?? undefined,
    about: source.about ?? undefined,
    powerline: source.powerline ?? undefined,
    bannerColor: source.banner_color ?? undefined,
    birthday: source.birthday ?? undefined,
    phone: source.phone ?? undefined,
    email: source.email ?? undefined,
    followers: source.followers,
    following: source.following,
    stars: source.stars,
    followedByMe: source.followed_by_me,
    starredByMe: source.starred_by_me,
    reactions: source.reactions,
    myReactions: source.my_reactions,
  };
}

export function mapApiPost(source: ApiPost): Post {
  return {
    id: source.id,
    rootPostId: source.root_post_id,
    userId: source.user_id,
    profile: toProfile(source.profile),
    content: source.content,
    comments: source.comments,
    reactions: source.reactions,
    createdAt: source.created_at,
    updatedAt: source.updated_at,
    replyTo: source.reply_to ?? undefined,
    replyToAuthor: source.reply_to_author ?? undefined,
    replyToSnippet: source.reply_to_snippet ?? undefined,
    isComment: source.is_comment,
    myReactions: source.my_reactions,
  };
}

function toComment(source: ApiPost): Comment {
  return {
    id: source.id,
    rootPostId: source.root_post_id,
    userId: source.user_id,
    profile: toProfile(source.profile),
    replyTo: source.reply_to ?? undefined,
    content: source.content,
    reactions: source.reactions,
    myReactions: source.my_reactions,
    createdAt: source.created_at,
    updatedAt: source.updated_at,
  };
}

export async function getPost(postId: number): Promise<Post> {
  const data = await callAPI<DataPost>(`/posts/${postId}`);
  return mapApiPost(data.post);
}

export async function getMyPosts(): Promise<Post[]> {
  const data = await callAPI<DataPosts>('/posts/me');
  return data.posts.map(mapApiPost);
}

export async function createPost(content: string, replyTo?: number): Promise<Post> {
  const data = await callAPI<DataPost>('/posts/', {
    method: 'POST',
    body: { content, reply_to: replyTo, is_comment: false },
  });
  invalidateFeedCache();
  const post = mapApiPost(data.post);
  publishDataChange({ type: 'post-created', post });
  if (replyTo !== undefined) {
    publishDataChange({ type: 'comment-created', postId: post.rootPostId });
  }
  return post;
}

export async function updatePost(postId: number, content: string): Promise<Post> {
  const data = await callAPI<DataPost>(`/posts/${postId}`, {
    method: 'PATCH',
    body: { content },
  });
  invalidateFeedCache();
  const post = mapApiPost(data.post);
  publishDataChange({ type: 'post-updated', post });
  return post;
}

export async function deletePost(postId: number): Promise<void> {
  const data = await callAPI<DataOk>(`/posts/${postId}`, { method: 'DELETE' });
  if (!data.ok) throw new Error('Post could not be deleted.');
  invalidateFeedCache();
  publishDataChange({ type: 'post-deleted', postId });
}

export async function getPostComments(postId: number): Promise<Comments> {
  const data = await callAPI<DataComments>(`/posts/${postId}/comments`);
  return {
    postId: data.post_id,
    comments: data.comments.map(toComment),
  };
}

export async function createPostComment(
  postId: number,
  content: string,
  replyTo?: number,
): Promise<Comment> {
  const data = await callAPI<DataPost>(`/posts/${postId}/comments`, {
    method: 'POST',
    body: { content, reply_to: replyTo },
  });
  invalidateFeedCache();
  const comment = toComment(data.post);
  publishDataChange({ type: 'comment-created', postId });
  return comment;
}

export async function togglePostReaction(postId: number, reaction: string): Promise<Post> {
  const data = await callAPI<DataPost>(`/posts/${postId}/reactions`, {
    method: 'POST',
    body: { reaction },
  });
  invalidateFeedCache();
  const post = mapApiPost(data.post);
  publishDataChange({ type: 'post-reaction', post });
  return post;
}

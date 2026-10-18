export interface Profile {
    id: number,
    userId?: number,
    username: string,  
    display_name?: string | null,
    followers?: number,
    following?: number,
    stars?: number,
    posts?: number,
    about?: string,
    powerline?: string,
    bannerColor?: string,
    emoji?: string,
    email?: string,
    phone?: string,
    birthday?: string,
    isOwner?: boolean,
    followedByMe?: boolean,
    starredByMe?: boolean,
    reactions?: Record<string, number>,
    myReactions?: string[],
}

export interface Post {
    id: number,
    rootPostId: number,
    userId?: number,
    profile: Profile,
    content: string,
    reactions: Record<string, number>,
    comments: number,
    createdAt: string,
    updatedAt: string,
    replyTo?: number,
    replyToAuthor?: string,
    replyToSnippet?: string,
    isComment?: boolean,
    myReactions?: string[],
}

export interface Comment {
    id: number,
    rootPostId: number,
    userId?: number,
    profile: Profile,
    replyTo?: number,
    content: string,
    reactions: Record<string, number>,
    myReactions?: string[],
    createdAt: string,
    updatedAt: string
}

export interface Comments {
    postId: number,
    comments: Comment[],
    nextCursor?: number
}



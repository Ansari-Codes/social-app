export interface ProfilePublic {
  id: number;
  user_id: number;
  username: string;
  display_name: string | null;
  email: string | null;
  about: string | null;
  powerline: string | null;
  banner_color: string | null;
  emoji: string | null;
  phone: string | null;
  birthday: string | null;
  is_owner: boolean;
  followers: number;
  following: number;
  stars: number;
  followed_by_me: boolean;
  starred_by_me: boolean;
  reactions: Record<string, number>;
  my_reactions: string[];
}

export interface ProfileData {
  profile: ProfilePublic;
}

export interface ProfileUpdatePayload {
  about?: string | null;
  powerline?: string | null;
  banner_color?: string | null;
  emoji?: string | null;
  phone?: string | null;
  birthday?: string | null;
}

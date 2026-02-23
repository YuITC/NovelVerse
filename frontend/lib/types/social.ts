export interface FollowStatus {
  is_following: boolean;
  follower_count: number;
}

export interface BookmarkStatus {
  is_bookmarked: boolean;
}

export interface BookmarkedNovel {
  novel_id: string;
  added_at: string;
  novel: {
    id: string;
    title: string;
    author: string;
    cover_url: string | null;
    status: string;
    total_chapters: number;
    updated_at: string;
  } | null;
}

export interface NominationStatus {
  is_nominated: boolean;
  nominations_remaining: number;
}

export interface LeaderboardNovel {
  id: string;
  title: string;
  author: string;
  cover_url: string | null;
  status: string;
  total_chapters: number;
  total_views: number;
  avg_rating: number;
}

export interface LeaderboardEntry {
  rank: number;
  novel_id: string;
  score: number;
  novel: LeaderboardNovel | null;
}

export interface LeaderboardResponse {
  period: string;
  entries: LeaderboardEntry[];
}

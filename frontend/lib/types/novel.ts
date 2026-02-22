export interface Tag {
  id: string;
  name: string;
  slug: string;
}

export interface NovelUploader {
  id: string;
  username: string;
  avatar_url: string | null;
}

export interface Novel {
  id: string;
  title: string;
  original_title: string | null;
  author: string;
  description: string | null;
  cover_url: string | null;
  status: "ongoing" | "completed" | "dropped";
  uploader_id: string;
  uploader: NovelUploader | null;
  tags: Tag[];
  total_chapters: number;
  total_views: number;
  avg_rating: number;
  rating_count: number;
  total_comments: number;
  is_pinned: boolean;
  created_at: string;
  updated_at: string;
}

export interface NovelListItem {
  id: string;
  title: string;
  original_title: string | null;
  author: string;
  cover_url: string | null;
  status: "ongoing" | "completed" | "dropped";
  uploader_id: string;
  tags: Tag[];
  total_chapters: number;
  total_views: number;
  avg_rating: number;
  rating_count: number;
  is_pinned: boolean;
  updated_at: string;
}

export interface NovelListResponse {
  items: NovelListItem[];
  next_cursor: string | null;
}

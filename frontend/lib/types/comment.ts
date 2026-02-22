export interface Comment {
  id: string;
  novel_id: string;
  chapter_id: string | null;
  user_id: string;
  parent_id: string | null;
  content: string;
  likes: number;
  created_at: string;
  updated_at: string;
}

export interface Review {
  id: string;
  novel_id: string;
  user_id: string;
  rating: number;
  content: string;
  created_at: string;
  updated_at: string;
}

export interface ChapterListItem {
  id: string;
  novel_id: string;
  chapter_number: number;
  title: string | null;
  word_count: number;
  status: "draft" | "scheduled" | "published";
  publish_at: string | null;
  published_at: string | null;
  views: number;
  created_at: string;
  updated_at: string;
}

export interface ChapterContent extends ChapterListItem {
  content: string;
  prev_chapter: number | null;
  next_chapter: number | null;
  novel_title: string | null;
}

export interface ReadingProgress {
  user_id: string;
  novel_id: string;
  last_chapter_read: number;
  chapters_read_list: number[];
  updated_at: string;
}

export interface LibraryItem {
  novel_id: string;
  last_chapter_read: number;
  chapters_read_list: number[];
  updated_at: string;
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

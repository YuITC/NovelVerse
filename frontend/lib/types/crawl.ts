export interface CrawlSource {
  id: string;
  novel_id: string;
  source_url: string;
  last_chapter: number;
  is_active: boolean;
  created_at: string;
}

export interface CrawlQueueItem {
  id: string;
  crawl_source_id: string;
  novel_id: string;
  chapter_number: number;
  raw_content: string | null;
  translated_content: string | null;
  translation_method: string | null;
  status: "pending" | "crawled" | "translated" | "published" | "skipped";
  created_at: string;
  updated_at: string;
}

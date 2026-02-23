/**
 * AI feature types — M16 infrastructure, consumed by M17 (Chat) and M19 (Story Intelligence).
 */

export interface Character {
  id: string;
  novel_id: string;
  name: string;
  description: string | null;
  traits: string[];
  first_chapter: number | null;
}

export interface EmbeddingChunk {
  id: string;
  chapter_id: string;
  chunk_index: number;
  content_preview: string;
  vector_id: string;
}

// M19: stored as JSONB on novels.relationship_graph
export interface RelationshipNode {
  id: string;
  name: string;
}

export interface RelationshipEdge {
  source: string;
  target: string;
  weight: number;
}

export interface RelationshipGraph {
  nodes: RelationshipNode[];
  edges: RelationshipEdge[];
}

// M19: stored as JSONB on novels.arc_timeline
export interface TimelineEvent {
  chapter_number: number;
  event_summary: string;
}

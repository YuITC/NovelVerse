/**
 * AI feature types — M16 infrastructure + M17 Chat + M19 Story Intelligence.
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

// M17: Chat with Characters
export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
  created_at: string;
}

export interface ChatSession {
  id: string;
  novel_id: string;
  character_id: string;
  messages: ChatMessage[];
  created_at: string;
}

export interface ChatSessionListItem {
  id: string;
  character_id: string;
  created_at: string;
}

export interface CharacterListResponse {
  items: Character[];
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

/**
 * Strictly Typed Knowledge Brain API Client.
 * Implements Section 2.4 of the Capstone brief:
 * Consumes Task 1 REST API (/query) without duplicating internal knowledge logic.
 */

export interface SourceItem {
  title: string;
  url: string;
  relevance: number;
}

export interface ImageReference {
  src: string;
  alt?: string;
  context?: string;
  section?: string;
}

export interface QueryResponse {
  answer: string;
  status: 'answered' | 'insufficient_evidence' | 'error';
  sources: SourceItem[];
  image_references: ImageReference[];
  confidence: number;
  needs_human: boolean;
  escalation_id?: string;
}

export class KnowledgeBrainClient {
  private baseUrl: string;

  constructor(baseUrl: string = 'http://127.0.0.1:8000') {
    this.baseUrl = baseUrl;
  }

  async queryKnowledge(question: string, topK: number = 4): Promise<QueryResponse> {
    try {
      const response = await fetch(`${this.baseUrl}/api/query`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question, top_k: topK })
      });

      if (!response.ok) {
        throw new Error(`Knowledge Brain API error: ${response.status} ${response.statusText}`);
      }

      const data: QueryResponse = await response.json();
      return data;
    } catch (err: any) {
      return {
        answer: 'Knowledge Brain service unreachable. Escalated for human assistance.',
        status: 'error',
        sources: [],
        image_references: [],
        confidence: 0.0,
        needs_human: true,
        escalation_id: `ESC-CONN-${Date.now().toString(36).toUpperCase()}`
      };
    }
  }
}

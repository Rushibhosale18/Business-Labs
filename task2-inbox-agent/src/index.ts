/**
 * Enterprise Inbox Agent (TypeScript Orchestrator).
 * Complies with Capstone Sections 2.1 - 2.9.
 */
import { KnowledgeBrainClient, type QueryResponse } from './knowledge-client/client.ts';
import * as fs from 'fs';
import * as path from 'path';

export interface CustomerEmail {
  id: string;
  sender: string;
  subject: string;
  body: string;
  expected_category: string;
  risk_level: 'Low' | 'Moderate' | 'High';
}

export interface SupportDraftResult {
  emailId: string;
  sender: string;
  subject: string;
  predictedCategory: string;
  riskLevel: 'Low' | 'Moderate' | 'High';
  kbStatus: string;
  sourcesCited: string[];
  generatedDraft: string;
  consecutiveStreak: number;
  isAutonomyEligible: boolean;
  requiresHumanReview: boolean;
}

export class InboxAgentService {
  private client: KnowledgeBrainClient;
  private approvalStreaks: Record<string, number> = {
    how_to: 22,
    troubleshooting: 8,
    refund_cancellation: 0,
    complaint: 0
  };

  constructor(apiUrl?: string) {
    this.client = new KnowledgeBrainClient(apiUrl);
  }

  public classifyIntent(body: string): { category: string; risk: 'Low' | 'Moderate' | 'High' } {
    const text = body.toLowerCase();
    if (text.includes('refund') || text.includes('money back') || text.includes('double charge')) {
      return { category: 'refund_cancellation', risk: 'High' };
    }
    if (text.includes('cancel') && text.includes('order')) {
      return { category: 'how_to', risk: 'Low' };
    }
    if (text.includes('broken') || text.includes('error') || text.includes('502') || text.includes('freeze')) {
      return { category: 'troubleshooting', risk: 'Moderate' };
    }
    if (text.includes('quote') || text.includes('cost to') || text.includes('how much')) {
      return { category: 'quote_request', risk: 'Moderate' };
    }
    if (text.includes('urgent') || text.includes('unacceptable') || text.includes('furious')) {
      return { category: 'complaint', risk: 'High' };
    }
    return { category: 'how_to', risk: 'Low' };
  }

  public async processEmail(email: CustomerEmail): Promise<SupportDraftResult> {
    const classification = this.classifyIntent(email.body);
    const kbRes: QueryResponse = await this.client.queryKnowledge(email.body);

    const streak = this.approvalStreaks[classification.category] || 0;
    const isAnswered = kbRes.status === 'answered';

    let draftText = '';
    const citedUrls = kbRes.sources.map(s => s.url);

    if (isAnswered) {
      draftText = `Dear ${email.sender.split('@')[0]},\n\nThank you for reaching out to support.\n\n${kbRes.answer}\n\nOfficial Documentation:\n` +
        kbRes.sources.map(s => `• ${s.title}: ${s.url}`).join('\n') +
        `\n\nSincerely,\nTechnical Solutions Team`;
    } else {
      draftText = `Dear ${email.sender.split('@')[0]},\n\nThank you for reaching out. Your request has been escalated to our engineering lead (Ticket Ref: ${kbRes.escalation_id || 'ESC-PENDING'}).\n\nBest regards,\nSupport Operations`;
    }

    // Autonomy Gate: requires >= 20 consecutive streak, Low Risk, and verified grounded answer
    const canAutoSend = (streak >= 20) && (classification.risk === 'Low') && isAnswered;

    return {
      emailId: email.id,
      sender: email.sender,
      subject: email.subject,
      predictedCategory: classification.category,
      riskLevel: classification.risk,
      kbStatus: kbRes.status,
      sourcesCited: citedUrls,
      generatedDraft: draftText,
      consecutiveStreak: streak,
      isAutonomyEligible: canAutoSend,
      requiresHumanReview: !canAutoSend
    };
  }
}

// Standalone verification run
async function run() {
  const agent = new InboxAgentService();
  const sampleEmail: CustomerEmail = {
    id: 'EML-003',
    sender: 'marcus.k@contractorhub.io',
    subject: 'Cancelling recurring billing for a cancelled member',
    body: 'Can an admin cancel a member recurring monthly charge directly from the backend dashboard without logging into Stripe separately?',
    expected_category: 'how_to',
    risk_level: 'Low'
  };

  console.log('Running TypeScript Inbox Agent processing...');
  const res = await agent.processEmail(sampleEmail);
  console.log(JSON.stringify(res, null, 2));
}

run();

import { NextResponse } from 'next/server';
import { PrismaClient } from '@prisma/client';

const prisma = new PrismaClient();

export async function GET() {
  try {
    const traces = await prisma.spans.findMany({
      where: {
        parent_span_id: null
      },
      orderBy: {
        start_time: 'desc'
      },
      take: 100
    });
    
    // Format them similarly to how the frontend expects
    const formatted = traces.map(t => {
      const attrs = JSON.parse(t.attributes || '{}');
      return {
        id: t.span_id,
        trace_id: t.trace_id,
        name: t.name,
        status: t.status_code,
        latencyMs: Number(t.end_time - t.start_time) / 1000000,
        costUsd: attrs['financial.cost_usd'] || 0,
        faithfulness: attrs['eval.hallucination_score'] ? (1.0 - attrs['eval.hallucination_score']) : null,
        reason: t.status_code === 'ERROR' ? 'TraceGuard Firewall Blocked' : null,
        timestamp: Number(t.start_time) / 1000000,
        spans: 1, // Simplified for Prisma conversion
      };
    });

    return NextResponse.json({ traces: formatted });
  } catch (error: any) {
    return NextResponse.json({ error: error.message }, { status: 500 });
  }
}

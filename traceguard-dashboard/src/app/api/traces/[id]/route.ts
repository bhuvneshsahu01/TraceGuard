import { NextResponse } from 'next/server';
import { PrismaClient } from '@prisma/client';

const prisma = new PrismaClient();

export async function GET(request: Request, { params }: { params: { id: string } }) {
  try {
    const spans = await prisma.spans.findMany({
      where: {
        trace_id: params.id
      },
      orderBy: {
        start_time: 'asc'
      }
    });

    // Build the tree
    const spanMap = new Map();
    const roots: any[] = [];

    spans.forEach(s => {
      spanMap.set(s.span_id, {
        span_id: s.span_id,
        parent_id: s.parent_span_id,
        name: s.name,
        start_time: Number(s.start_time),
        end_time: Number(s.end_time),
        status_code: s.status_code,
        attributes: JSON.parse(s.attributes || '{}'),
        events: JSON.parse(s.events || '[]'),
        children: []
      });
    });

    spanMap.forEach(node => {
      if (node.parent_id && spanMap.has(node.parent_id)) {
        spanMap.get(node.parent_id).children.push(node);
      } else {
        roots.push(node);
      }
    });

    return NextResponse.json({ spans: roots });
  } catch (error: any) {
    return NextResponse.json({ error: error.message }, { status: 500 });
  }
}

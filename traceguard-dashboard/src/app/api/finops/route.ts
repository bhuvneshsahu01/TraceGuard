import { NextResponse } from 'next/server';
import { PrismaClient } from '@prisma/client';

const prisma = new PrismaClient();

export async function GET() {
  try {
    // We will find all spans that represent a tool call
    // In our OTEL spans, these usually have a name like "tool.search_knowledge_base" or attributes describing the tool.
    const allSpans = await prisma.spans.findMany({
      orderBy: { start_time: 'desc' }
    });

    const toolStats: Record<string, { count: number; cost: number; success: number }> = {};
    const DUMMY_COST_PER_CALL = 0.005;

    for (const span of allSpans) {
      let isTool = false;
      let toolName = span.name;
      let attributes = {};

      try {
        attributes = JSON.parse(span.attributes);
        if ((attributes as any)["function.name"]) {
          isTool = true;
          toolName = (attributes as any)["function.name"];
        }
      } catch (e) {
        // ignore JSON parse error
      }

      if (isTool || span.name.includes('search_') || span.name.includes('get_') || span.name.includes('issue_')) {
        const name = isTool ? toolName : span.name;
        
        if (!toolStats[name]) {
          toolStats[name] = { count: 0, cost: 0, success: 0 };
        }
        
        toolStats[name].count += 1;
        toolStats[name].cost += DUMMY_COST_PER_CALL;

        // Naive success proxy: Did it throw an error?
        if (span.status_code !== "ERROR") {
          toolStats[name].success += 1;
        }
      }
    }

    const roiData = Object.keys(toolStats).map(toolName => {
      const stats = toolStats[toolName];
      // ROI = (Successes / Cost) -> Higher is better
      const roi = stats.cost > 0 ? (stats.success / stats.cost) : 0;
      return {
        toolName,
        count: stats.count,
        totalCost: stats.cost,
        successRate: stats.success / stats.count,
        roi
      };
    });

    return NextResponse.json({ roiData });
  } catch (error) {
    console.error("Failed to fetch FinOps data", error);
    return NextResponse.json({ error: "Failed to fetch FinOps data" }, { status: 500 });
  }
}

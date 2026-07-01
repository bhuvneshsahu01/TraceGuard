import { NextResponse } from 'next/server';
import Database from 'better-sqlite3';
import path from 'path';
import fs from 'fs';

const dbPath = path.join(process.cwd(), '..', '.traceguard.db');

function buildTraceTree(spans: any[]) {
  const spanMap = new Map();
  const rootSpans: any[] = [];

  // Parse attributes and events, initialize children array
  spans.forEach(span => {
    try {
      if (span.attributes) span.attributes = JSON.parse(span.attributes);
      if (span.events) span.events = JSON.parse(span.events);
    } catch (e) {
      // Ignore JSON parse errors
    }
    span.children = [];
    spanMap.set(span.span_id, span);
  });

  // Build the tree
  spans.forEach(span => {
    if (span.parent_span_id && spanMap.has(span.parent_span_id)) {
      spanMap.get(span.parent_span_id).children.push(span);
    } else {
      rootSpans.push(span);
    }
  });

  return rootSpans;
}

export async function GET(request: Request, { params }: { params: { id: string } }) {
  if (!fs.existsSync(dbPath)) {
    return NextResponse.json({ error: "Database not found" }, { status: 404 });
  }

  try {
    const db = new Database(dbPath, { readonly: true });
    
    // Check if eval columns exist
    const tableInfo = db.prepare("PRAGMA table_info(spans)").all();
    const hasFaithfulness = tableInfo.some((col: any) => col.name === 'eval_faithfulness');
    
    let query = `SELECT * FROM spans WHERE trace_id = ? ORDER BY start_time ASC`;
    const spans = db.prepare(query).all(params.id);
    db.close();
    
    const tree = buildTraceTree(spans);
    
    return NextResponse.json({ spans: tree });
  } catch (err: any) {
    return NextResponse.json({ error: err.message }, { status: 500 });
  }
}

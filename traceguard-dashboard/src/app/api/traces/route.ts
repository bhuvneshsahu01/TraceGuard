import { NextResponse } from 'next/server';
import Database from 'better-sqlite3';
import path from 'path';
import fs from 'fs';

// Try to find the SQLite database in the parent project directory
const dbPath = path.join(process.cwd(), '..', '.traceguard.db');

export async function GET() {
  if (!fs.existsSync(dbPath)) {
    return NextResponse.json(
      { error: "No database found. Run TraceGuard SDK to generate .traceguard.db" },
      { status: 404 }
    );
  }

    try {
    const db = new Database(dbPath, { readonly: true });
    
    // Check if eval columns exist
    const tableInfo = db.prepare("PRAGMA table_info(spans)").all();
    const hasEval = tableInfo.some((col: any) => col.name === 'eval_faithfulness');
    
    let query = `
      SELECT 
        trace_id, 
        start_time,
        (SELECT COUNT(*) FROM spans WHERE trace_id = traces.trace_id) as span_count,
        (SELECT MAX(end_time) - MIN(start_time) FROM spans WHERE trace_id = traces.trace_id) as latency,
        (SELECT COUNT(*) FROM spans WHERE trace_id = traces.trace_id AND status_code = 'ERROR') as error_count,
        (SELECT SUM(CAST(json_extract(attributes, '$.financial.cost_usd') AS REAL)) FROM spans WHERE trace_id = traces.trace_id AND attributes IS NOT NULL) as total_cost
    `;
    
    if (hasEval) {
      query += `, (SELECT AVG(eval_faithfulness) FROM spans WHERE trace_id = traces.trace_id AND eval_faithfulness IS NOT NULL) as avg_faithfulness`;
    } else {
      query += `, NULL as avg_faithfulness`;
    }
    
    query += ` FROM traces ORDER BY start_time DESC LIMIT 50`;
    
    const traces = db.prepare(query).all();
    db.close();

    // Map output to something frontend friendly
    const formattedTraces = traces.map((t: any) => ({
      id: t.trace_id,
      timestamp: t.start_time,
      spans: t.span_count,
      latencyMs: t.latency ? Math.round(t.latency / 1000000) : 0, // Convert nanoseconds to ms
      status: t.error_count > 0 ? 'ERROR' : 'OK',
      costUsd: t.total_cost || 0.0,
      faithfulness: t.avg_faithfulness
    }));

    return NextResponse.json({ traces: formattedTraces });
  } catch (err: any) {
    return NextResponse.json({ error: err.message }, { status: 500 });
  }
}

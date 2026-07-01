import { NextResponse } from 'next/server';
import Database from 'better-sqlite3';
import path from 'path';
import fs from 'fs';

const dbPath = path.join(process.cwd(), '..', '.traceguard.db');

export async function POST(request: Request) {
  if (!fs.existsSync(dbPath)) {
    return NextResponse.json({ error: "Database not found" }, { status: 404 });
  }

  try {
    const { trace_id, name, spans } = await request.json();
    
    if (!trace_id || !name || !spans) {
      return NextResponse.json({ error: "Missing required fields" }, { status: 400 });
    }

    const db = new Database(dbPath);
    
    const stmt = db.prepare(`
      INSERT OR REPLACE INTO datasets (id, name, created_at, spans)
      VALUES (?, ?, ?, ?)
    `);
    
    stmt.run(trace_id, name, Date.now(), JSON.stringify(spans));
    
    db.close();
    
    return NextResponse.json({ success: true, message: "Added to dataset successfully." });
  } catch (err: any) {
    return NextResponse.json({ error: err.message }, { status: 500 });
  }
}

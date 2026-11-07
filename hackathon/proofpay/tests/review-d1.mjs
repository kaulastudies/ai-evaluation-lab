// Independent verification harness. Models the D1 prepared/batch surface using
// actual SQLite transactions; it does not assert parity with every D1 feature.
import { DatabaseSync } from 'node:sqlite';

export class ReviewD1 {
  constructor(filename) {
    this.filename = filename;
    this.connection = new DatabaseSync(filename);
    this.connection.exec('PRAGMA foreign_keys=ON; PRAGMA busy_timeout=10000;');
  }
  prepare(sql) { return new ReviewStatement(this, sql); }
  async exec(sql) { this.connection.exec(sql); return { count: 1, duration: 0 }; }
  async batch(statements) {
    this.connection.exec('BEGIN IMMEDIATE');
    try {
      const results = [];
      for (const statement of statements) results.push(await statement.all());
      this.connection.exec('COMMIT');
      return results;
    } catch (error) {
      this.connection.exec('ROLLBACK');
      throw error;
    }
  }
  close() { this.connection.close(); }
  withSession() { return this; }
  getBookmark() { return null; }
}

class ReviewStatement {
  constructor(db, sql, params = []) { this.db = db; this.sql = sql; this.params = params; }
  bind(...params) { return new ReviewStatement(this.db, this.sql, params); }
  async first(column) {
    const row = this.db.connection.prepare(this.sql).get(...this.params);
    return row ? column ? row[column] : { ...row } : null;
  }
  async all() {
    const statement = this.db.connection.prepare(this.sql);
    const before = this.db.connection.prepare('SELECT total_changes() AS n').get().n;
    const results = statement.all(...this.params).map(row => ({ ...row }));
    const after = this.db.connection.prepare('SELECT total_changes() AS n, last_insert_rowid() AS id').get();
    return { success: true, results, meta: { changes: after.n - before, last_row_id: after.id, duration: 0 } };
  }
  async run() {
    const result = this.db.connection.prepare(this.sql).run(...this.params);
    return { success: true, results: [], meta: { changes: Number(result.changes), last_row_id: Number(result.lastInsertRowid), duration: 0 } };
  }
  async raw({ columnNames = false } = {}) {
    const statement = this.db.connection.prepare(this.sql);
    const results = statement.all(...this.params).map(row => Object.values(row));
    return columnNames ? [statement.columns().map(column => column.name), ...results] : results;
  }
}

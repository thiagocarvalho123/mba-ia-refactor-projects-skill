const sqlite3 = require("sqlite3").verbose();
const settings = require("./settings");
const { hashPassword } = require("../utils/crypto");

const db = new sqlite3.Database(settings.dbPath);

function run(sql, params = []) {
  return new Promise((resolve, reject) => {
    db.run(sql, params, function (err) {
      if (err) return reject(err);
      resolve({ lastID: this.lastID, changes: this.changes });
    });
  });
}

function get(sql, params = []) {
  return new Promise((resolve, reject) => {
    db.get(sql, params, (err, row) => (err ? reject(err) : resolve(row)));
  });
}

function all(sql, params = []) {
  return new Promise((resolve, reject) => {
    db.all(sql, params, (err, rows) => (err ? reject(err) : resolve(rows)));
  });
}

const SCHEMA = [
  "CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, name TEXT, email TEXT, pass TEXT)",
  "CREATE TABLE IF NOT EXISTS courses (id INTEGER PRIMARY KEY, title TEXT, price REAL, active INTEGER)",
  "CREATE TABLE IF NOT EXISTS enrollments (id INTEGER PRIMARY KEY, user_id INTEGER, course_id INTEGER)",
  "CREATE TABLE IF NOT EXISTS payments (id INTEGER PRIMARY KEY, enrollment_id INTEGER, amount REAL, status TEXT)",
  "CREATE TABLE IF NOT EXISTS audit_logs (id INTEGER PRIMARY KEY, action TEXT, created_at DATETIME)",
];

async function initDb() {
  for (const statement of SCHEMA) {
    await run(statement);
  }

  const courseCount = await get("SELECT COUNT(*) as total FROM courses");
  if (courseCount.total === 0) {
    const userHash = hashPassword("123");
    const user = await run(
      "INSERT INTO users (name, email, pass) VALUES (?, ?, ?)",
      ["Leonan", "leonan@fullcycle.com.br", userHash]
    );
    await run(
      "INSERT INTO courses (title, price, active) VALUES (?, ?, 1), (?, ?, 1)",
      ["Clean Architecture", 997.0, "Docker", 497.0]
    );
    const enrollment = await run(
      "INSERT INTO enrollments (user_id, course_id) VALUES (?, ?)",
      [user.lastID, 1]
    );
    await run(
      "INSERT INTO payments (enrollment_id, amount, status) VALUES (?, ?, ?)",
      [enrollment.lastID, 997.0, "PAID"]
    );
  }
}

module.exports = { db, run, get, all, initDb };

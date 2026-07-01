const db = require("../config/database");

async function findByEmail(email) {
  return db.get("SELECT * FROM users WHERE email = ?", [email]);
}

async function findById(id) {
  return db.get("SELECT id, name, email FROM users WHERE id = ?", [id]);
}

async function create(name, email, passwordHash) {
  const result = await db.run(
    "INSERT INTO users (name, email, pass) VALUES (?, ?, ?)",
    [name, email, passwordHash]
  );
  return result.lastID;
}

async function remove(id) {
  await db.run("DELETE FROM users WHERE id = ?", [id]);
}

module.exports = { findByEmail, findById, create, remove };

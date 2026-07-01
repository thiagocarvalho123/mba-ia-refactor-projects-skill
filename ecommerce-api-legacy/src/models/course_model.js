const db = require("../config/database");

async function findActiveById(id) {
  return db.get("SELECT * FROM courses WHERE id = ? AND active = 1", [id]);
}

async function list() {
  return db.all("SELECT * FROM courses", []);
}

module.exports = { findActiveById, list };

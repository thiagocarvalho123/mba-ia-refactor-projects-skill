const db = require("../config/database");

async function create(userId, courseId) {
  const result = await db.run(
    "INSERT INTO enrollments (user_id, course_id) VALUES (?, ?)",
    [userId, courseId]
  );
  return result.lastID;
}

async function findByUserId(userId) {
  return db.all("SELECT id FROM enrollments WHERE user_id = ?", [userId]);
}

async function removeByUserId(userId) {
  await db.run("DELETE FROM enrollments WHERE user_id = ?", [userId]);
}

module.exports = { create, findByUserId, removeByUserId };

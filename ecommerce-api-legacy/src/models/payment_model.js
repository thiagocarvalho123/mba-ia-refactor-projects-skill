const db = require("../config/database");

async function create(enrollmentId, amount, status) {
  const result = await db.run(
    "INSERT INTO payments (enrollment_id, amount, status) VALUES (?, ?, ?)",
    [enrollmentId, amount, status]
  );
  return result.lastID;
}

async function removeByEnrollmentIds(enrollmentIds) {
  if (!enrollmentIds.length) return;
  const placeholders = enrollmentIds.map(() => "?").join(",");
  await db.run(`DELETE FROM payments WHERE enrollment_id IN (${placeholders})`, enrollmentIds);
}

module.exports = { create, removeByEnrollmentIds };

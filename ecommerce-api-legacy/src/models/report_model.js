const db = require("../config/database");

async function financialReportRows() {
  return db.all(`
    SELECT c.id as course_id, c.title as course_title, e.id as enrollment_id,
           u.name as student_name, p.amount as amount, p.status as status
    FROM courses c
    LEFT JOIN enrollments e ON e.course_id = c.id
    LEFT JOIN users u ON u.id = e.user_id
    LEFT JOIN payments p ON p.enrollment_id = e.id
    ORDER BY c.id
  `);
}

module.exports = { financialReportRows };

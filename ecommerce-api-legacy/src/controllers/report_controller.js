const reportModel = require("../models/report_model");

async function financialReport() {
  const rows = await reportModel.financialReportRows();

  const byCourse = new Map();
  for (const row of rows) {
    if (!byCourse.has(row.course_id)) {
      byCourse.set(row.course_id, { course: row.course_title, revenue: 0, students: [] });
    }
    const courseData = byCourse.get(row.course_id);

    if (row.enrollment_id == null) continue;

    if (row.status === "PAID") {
      courseData.revenue += row.amount;
    }
    courseData.students.push({
      student: row.student_name || "Unknown",
      paid: row.amount != null ? row.amount : 0,
    });
  }

  return Array.from(byCourse.values());
}

module.exports = { financialReport };

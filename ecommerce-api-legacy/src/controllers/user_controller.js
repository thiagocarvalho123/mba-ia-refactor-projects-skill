const userModel = require("../models/user_model");
const enrollmentModel = require("../models/enrollment_model");
const paymentModel = require("../models/payment_model");

async function deleteUser(id) {
  const enrollments = await enrollmentModel.findByUserId(id);
  const enrollmentIds = enrollments.map((enrollment) => enrollment.id);

  await paymentModel.removeByEnrollmentIds(enrollmentIds);
  await enrollmentModel.removeByUserId(id);
  await userModel.remove(id);
}

module.exports = { deleteUser };

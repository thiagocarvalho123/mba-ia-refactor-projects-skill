const courseModel = require("../models/course_model");
const userModel = require("../models/user_model");
const enrollmentModel = require("../models/enrollment_model");
const paymentModel = require("../models/payment_model");
const auditLogModel = require("../models/audit_log_model");
const { hashPassword } = require("../utils/crypto");
const { maskCard } = require("../utils/card");
const logger = require("../utils/logger");

async function checkout({ usr, eml, pwd, c_id, card }) {
  if (!usr || !eml || !c_id || !card) {
    return { status: 400, body: { erro: "Dados obrigatórios ausentes" } };
  }

  const course = await courseModel.findActiveById(c_id);
  if (!course) {
    return { status: 404, body: { erro: "Curso não encontrado" } };
  }

  const existingUser = await userModel.findByEmail(eml);
  const userId = existingUser
    ? existingUser.id
    : await userModel.create(usr, eml, hashPassword(pwd || "123456"));

  logger.info(`Processando pagamento com cartão ${maskCard(card)} para usuário ${userId}`);
  const status = card.startsWith("4") ? "PAID" : "DENIED";
  if (status === "DENIED") {
    return { status: 400, body: { erro: "Pagamento recusado" } };
  }

  const enrollmentId = await enrollmentModel.create(userId, c_id);
  await paymentModel.create(enrollmentId, course.price, status);
  await auditLogModel.create(`Checkout curso ${c_id} por ${userId}`);

  return { status: 200, body: { msg: "Sucesso", enrollment_id: enrollmentId } };
}

module.exports = { checkout };

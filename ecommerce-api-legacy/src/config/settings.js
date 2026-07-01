const dbUser = process.env.DB_USER || "dev_user";
const dbPass = process.env.DB_PASS || "dev-only-insecure-password";
const paymentGatewayKey = process.env.PAYMENT_GATEWAY_KEY || "pk_test_dev_only_change_me";
const smtpUser = process.env.SMTP_USER || "dev@example.com";
const port = parseInt(process.env.PORT || "3000", 10);
const dbPath = process.env.DB_PATH || ":memory:";
const adminToken = process.env.ADMIN_TOKEN || "dev-only-admin-token-change-me";

module.exports = { dbUser, dbPass, paymentGatewayKey, smtpUser, port, dbPath, adminToken };

const express = require("express");
const settings = require("./config/settings");
const { initDb } = require("./config/database");
const checkoutRoutes = require("./routes/checkout_routes");
const adminRoutes = require("./routes/admin_routes");
const { notFound, errorHandler } = require("./middlewares/error_handler");
const logger = require("./utils/logger");

async function main() {
  const app = express();
  app.use(express.json());

  await initDb();

  app.use(checkoutRoutes);
  app.use(adminRoutes);

  app.use(notFound);
  app.use(errorHandler);

  app.listen(settings.port, () => {
    logger.info(`Frankenstein LMS rodando na porta ${settings.port}...`);
  });
}

main();

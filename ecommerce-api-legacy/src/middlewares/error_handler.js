const logger = require("../utils/logger");

function notFound(req, res) {
  res.status(404).json({ erro: "Rota não encontrada" });
}

// eslint-disable-next-line no-unused-vars
function errorHandler(err, req, res, next) {
  logger.error(err.stack || err.message);
  res.status(500).json({ erro: "Erro interno do servidor" });
}

module.exports = { notFound, errorHandler };

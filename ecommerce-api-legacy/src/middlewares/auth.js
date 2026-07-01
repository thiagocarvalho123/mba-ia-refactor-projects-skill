const settings = require("../config/settings");

function requireAdmin(req, res, next) {
  const token = req.header("X-Admin-Token");
  if (token !== settings.adminToken) {
    return res.status(403).json({ erro: "Acesso negado" });
  }
  next();
}

module.exports = { requireAdmin };

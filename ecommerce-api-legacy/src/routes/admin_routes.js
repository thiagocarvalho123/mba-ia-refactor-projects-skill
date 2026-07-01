const express = require("express");
const reportController = require("../controllers/report_controller");
const userController = require("../controllers/user_controller");
const { requireAdmin } = require("../middlewares/auth");

const router = express.Router();

router.get("/api/admin/financial-report", requireAdmin, async (req, res, next) => {
  try {
    const report = await reportController.financialReport();
    res.json(report);
  } catch (err) {
    next(err);
  }
});

router.delete("/api/users/:id", requireAdmin, async (req, res, next) => {
  try {
    await userController.deleteUser(req.params.id);
    res.json({ mensagem: "Usuário deletado" });
  } catch (err) {
    next(err);
  }
});

module.exports = router;

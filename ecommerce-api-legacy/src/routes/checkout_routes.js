const express = require("express");
const checkoutController = require("../controllers/checkout_controller");

const router = express.Router();

router.post("/api/checkout", async (req, res, next) => {
  try {
    const { usr, eml, pwd, c_id, card } = req.body;
    const result = await checkoutController.checkout({ usr, eml, pwd, c_id, card });
    res.status(result.status).json(result.body);
  } catch (err) {
    next(err);
  }
});

module.exports = router;

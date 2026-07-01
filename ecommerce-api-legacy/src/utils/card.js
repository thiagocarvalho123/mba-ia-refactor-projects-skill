function maskCard(card) {
  if (!card || card.length < 4) return "****";
  return `**** **** **** ${card.slice(-4)}`;
}

module.exports = { maskCard };

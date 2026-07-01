function log(level, message) {
  console.log(`${new Date().toISOString()} ${level.toUpperCase()} ${message}`);
}

module.exports = {
  info: (message) => log("info", message),
  warn: (message) => log("warn", message),
  error: (message) => log("error", message),
};

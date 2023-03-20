const { defineConfig } = require("cypress");

module.exports = defineConfig({
  e2e: {
    baseUrl: 'http://www.goodmap.localhost:5000/',
    setupNodeEvents(on, config) {
      return config;
    }
}
});

const { defineConfig } = require("cypress");

module.exports = defineConfig({
  e2e: {
    baseUrl: 'http://localhost:5000/',
    setupNodeEvents(on, config) {
      return config;
    },
    experimentalStudio: true,
}
});

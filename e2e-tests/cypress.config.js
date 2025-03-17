const { defineConfig } = require("cypress");

module.exports = defineConfig({
  e2e: {
    baseUrl: 'http://localhost:5050/',
    setupNodeEvents(on, config) {
      return config;
    },
    experimentalStudio: true,
}
});


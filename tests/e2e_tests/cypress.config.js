const { defineConfig } = require("cypress");
const {
  cypressBrowserPermissionsPlugin,
} = require("cypress-browser-permissions");

module.exports = defineConfig({
  e2e: {
    baseUrl: "http://www.localhost:5000/",
    setupNodeEvents(on, config) {
      config = cypressBrowserPermissionsPlugin(on, config)
      return config;
    },
  },
  env: {
    browserPermissions: {
      geolocation: "allow",
    },
  },
});

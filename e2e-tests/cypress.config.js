const { defineConfig } = require("cypress");
const http = require("http");

module.exports = defineConfig({
  e2e: {
    baseUrl: 'http://localhost:5000/',
    setupNodeEvents(on, config) {
      // Task to fetch from webpack-dev-server
      on('task', {
        fetchWebpackScript() {
          return new Promise((resolve, reject) => {
            http.get('http://localhost:8080/index.js', (res) => {
              let data = '';
              res.on('data', chunk => data += chunk);
              res.on('end', () => resolve(data));
            }).on('error', (err) => reject(err));
          });
        }
      });
      return config;
    },
    experimentalStudio: true,
}
});


const { defineConfig } = require("cypress");
const http = require("http");

module.exports = defineConfig({
  e2e: {
    baseUrl: 'http://localhost:5000/',
    setupNodeEvents(on, config) {
      on('task', {
        fetchWebpackScript() {
          return new Promise((resolve, reject) => {
            const req = http.get('http://localhost:8080/index.js', (res) => {
              if (res.statusCode !== 200) {
                reject(new Error(`HTTP ${res.statusCode}: ${res.statusMessage}`));
                return;
              }
              let data = '';
              res.on('data', chunk => data += chunk);
              res.on('end', () => resolve(data));
            }).on('error', (err) => reject(err));
            req.setTimeout(10000, () => {
              req.destroy();
              reject(new Error('Request timeout after 10s'));
            });
          });
        }
      });
      return config;
    },
    experimentalStudio: true,
}
});


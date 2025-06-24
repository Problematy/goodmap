const { defineConfig } = require('cypress');

module.exports = defineConfig({
    e2e: {
        baseUrl: 'http://www.goodmap.localhost:5000/',
        setupNodeEvents(on, config) {
            on('task', {
                appendToGithubStepSummary(text) {
                    if (process.env.GITHUB_ACTIONS) {
                        const fs = require('fs');
                        fs.appendFileSync(process.env.GITHUB_STEP_SUMMARY, text + '\n');
                    }
                    return null;
                },
            });

            return config;
        },
        experimentalStudio: true,
    },
});

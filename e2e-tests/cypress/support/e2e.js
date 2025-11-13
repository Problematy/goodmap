// ***********************************************************
// This example support/e2e.js is processed and
// loaded automatically before your test files.
//
// This is a great place to put global configuration and
// behavior that modifies Cypress.
//
// You can change the location of this file or turn off
// automatically serving support files with the
// 'supportFile' configuration option.
//
// You can read more here:
// https://on.cypress.io/configuration
// ***********************************************************

// Import commands.js using ES2015 syntax:
import './commands'

// Import cypress-wait-until plugin
import 'cypress-wait-until'

// Alternatively you can use CommonJS syntax:
// require('./commands')

// Workaround for webpack-dev-server ERR_EMPTY_RESPONSE in Cypress
// Fetch script from webpack-dev-server using Node.js task and intercept browser requests
let scriptContent = null;

before(() => {
  // Fetch the script content once using Node.js
  cy.task('fetchWebpackScript').then((content) => {
  if (!content) {
   throw new Error('Failed to fetch webpack script: content is empty');
  }
  scriptContent = content;
  });
});

beforeEach(() => {
  // Intercept requests and serve the cached content
  cy.intercept('GET', 'http://localhost:8080/index.js', (req) => {
    req.reply({
      statusCode: 200,
      headers: {
        'Content-Type': 'application/javascript; charset=utf-8',
        'Access-Control-Allow-Origin': '*',
      },
      body: scriptContent,
    });
  });
});
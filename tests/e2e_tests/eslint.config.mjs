import pluginCypress from 'eslint-plugin-cypress/flat'
export default [
  {
    plugins: {
      cypress: pluginCypress
    },
    rules: {
      'cypress/unsafe-to-chain-command': 'error',
      'cypress/no-unnecessary-waiting': 'error'
    }
  }
]
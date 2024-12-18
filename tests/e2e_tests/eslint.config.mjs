import pluginCypress from 'eslint-plugin-cypress/flat';

export default [
  {
    plugins: {
      cypress: pluginCypress
    },
    rules: {
      'cypress/unsafe-to-chain-command': 'error',
      'cypress/no-unnecessary-waiting': 'error',
      'array-bracket-spacing': 'off',
      'space-in-parens': 'off',
      'no-unused-vars': 'warn',
      'no-console': 'warn',
      'func-names': 'error',
      'no-process-exit': 'error',
      'object-shorthand': 'error',
      'class-methods-use-this': 'error',
      'comma-dangle': 'off',
      'es-x/no-rest-spread-properties': 'off',
      indent: ['error', 2],
    }
  }
];
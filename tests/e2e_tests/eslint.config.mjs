import pluginCypress from 'eslint-plugin-cypress/flat';
import eslintConfigPrettier from 'eslint-config-prettier';

export default [
  pluginCypress.configs.recommended,
  eslintConfigPrettier,
  {
    rules: {
      'cypress/no-unnecessary-waiting': 'error',
      'cypress/unsafe-to-chain-command': 'error',
      'cypress/assertion-before-screenshot': 'error',
      'cypress/no-force': 'error',

      'class-methods-use-this': 'error',
      'func-names': 'error',
      'no-console': 'error',
      'no-process-exit': 'error',
      'no-unused-vars': 'error',
      'object-shorthand': 'error',

      'array-bracket-spacing': 'off',
      'comma-dangle': 'off',
      'es-x/no-rest-spread-properties': 'off',
      'indent': ['error', 4],
      'space-in-parens': 'off',
    }
  }
];

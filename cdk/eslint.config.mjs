import { fixupConfigRules, fixupPluginRules } from '@eslint/compat'
import typescriptEslint from '@typescript-eslint/eslint-plugin'
import tsParser from '@typescript-eslint/parser'
import path from 'node:path'
import { fileURLToPath } from 'node:url'
import js from '@eslint/js'
import { FlatCompat } from '@eslint/eslintrc'

const filename = fileURLToPath(import.meta.url)
const dirname = path.dirname(filename)
const compat = new FlatCompat({
  baseDirectory: dirname,
  recommendedConfig: js.configs.recommended,
  allConfig: js.configs.all,
})

export default [
  {
    ignores: [
      '**/node_modules/**/*',
      'node_modules/**/*',
      '**/build',
      '**/cdk.out',
      '**/cdk.context.json',
      '**/cdk.json',
      '**/*-schema.ts',
      '**/*.js',
    ],
  },
  ...fixupConfigRules(
    compat.extends(
      'plugin:@typescript-eslint/recommended',
      'plugin:import/errors',
      'plugin:import/warnings',
      'plugin:import/typescript',
      'plugin:prettier/recommended',
    ),
  ),
  {
    plugins: {
      '@typescript-eslint': fixupPluginRules(typescriptEslint),
    },

    languageOptions: {
      parser: tsParser,
      ecmaVersion: 2018,
      sourceType: 'module',
    },

    settings: {
      'import/parsers': {
        '@typescript-eslint/parser': ['.ts'],
      },

      'import/resolver': {
        node: {
          paths: ['src'],
          extensions: ['.ts'],
        },
      },
    },

    rules: {
      semi: ['error', 'never'],
      curly: ['error', 'all'],
      quotes: ['error', 'single'],

      // For now, errors like below happen if this rule is not deactivated. We will see later how to fix them
      // Parse errors in imported module '@middy/core': parserPath or languageOptions.parser is required! (undefined:undefined)
      'import/namespace': 'off',

      '@typescript-eslint/naming-convention': [
        'error',
        {
          selector: 'default',
          format: null,
          leadingUnderscore: 'allow',
        },
        {
          selector: 'variableLike',
          format: ['camelCase', 'PascalCase', 'UPPER_CASE'],
        },
        {
          selector: 'parameter',
          format: ['camelCase'],
          leadingUnderscore: 'allow',
        },
        {
          selector: 'typeLike',
          format: ['PascalCase'],
        },
        {
          selector: 'interface',
          format: ['PascalCase'],

          custom: {
            regex: '^I[A-Z]',
            match: true,
          },
        },
      ],

      'import/no-unresolved': 0,
      '@typescript-eslint/ban-ts-ignore': 'off',
      '@typescript-eslint/no-explicit-any': 'off',
      'prefer-const': 'error',
      '@typescript-eslint/no-unused-vars': 0,
      '@typescript-eslint/no-use-before-define': 0,
      '@typescript-eslint/no-require-imports': 0,
      '@typescript-eslint/no-var-requires': 0,
      'require-await': 'warn',
    },
  },
]

import eslint from '@eslint/js'
import tseslint from 'typescript-eslint'
import pluginVue from 'eslint-plugin-vue'
import vueParser from 'vue-eslint-parser'

export default tseslint.config(
  // Global ignores
  { ignores: ['dist/**', 'node_modules/**', '*.config.*'] },

  // Relax some base rules
  {
    rules: {
      'no-empty': ['warn', { allowEmptyCatch: true }],
    },
  },

  // Base JS/TS rules
  eslint.configs.recommended,
  ...tseslint.configs.recommended,

  // Browser globals (localStorage, document, Blob, URL, etc.)
  {
    languageOptions: {
      globals: {
        localStorage: 'readonly',
        document: 'readonly',
        window: 'readonly',
        console: 'readonly',
        fetch: 'readonly',
        Blob: 'readonly',
        URL: 'readonly',
        File: 'readonly',
        FormData: 'readonly',
        confirm: 'readonly',
        alert: 'readonly',
        prompt: 'readonly',
        setTimeout: 'readonly',
        clearTimeout: 'readonly',
        setInterval: 'readonly',
        clearInterval: 'readonly',
        navigator: 'readonly',
        location: 'readonly',
        history: 'readonly',
        HTMLElement: 'readonly',
        HTMLInputElement: 'readonly',
        MouseEvent: 'readonly',
        Event: 'readonly',
        Node: 'readonly',
        MutationObserver: 'readonly',
        AbortController: 'readonly',
        IntersectionObserver: 'readonly',
      },
    },
  },

  // Vue files: use vue-eslint-parser for .vue, TypeScript for <script lang="ts">
  ...pluginVue.configs['flat/essential'],
  {
    files: ['**/*.vue'],
    languageOptions: {
      parser: vueParser,
      parserOptions: {
        parser: tseslint.parser,
        sourceType: 'module',
      },
    },
    rules: {
      'vue/multi-word-component-names': 'off',
      'vue/no-v-model-argument': 'off',
      'vue/no-unused-vars': 'warn',
    },
  },

  // TypeScript-specific rules
  {
    files: ['**/*.ts', '**/*.vue'],
    rules: {
      '@typescript-eslint/no-explicit-any': 'off',
      '@typescript-eslint/no-unused-vars': ['warn', { argsIgnorePattern: '^_' }],
      '@typescript-eslint/no-unused-expressions': ['warn', { allowShortCircuit: true, allowTernary: true }],
    },
  },
)

import js from '@eslint/js'
import { defineConfig, globalIgnores } from 'eslint/config'
import configPrettier from 'eslint-config-prettier'
import pluginVue from 'eslint-plugin-vue'
import tseslint from 'typescript-eslint'

const browserGlobals = {
  console: 'readonly',
  document: 'readonly',
  File: 'readonly',
  Blob: 'readonly',
  URL: 'readonly',
  FileReader: 'readonly',
  localStorage: 'readonly',
  navigator: 'readonly',
  window: 'readonly',
}

export default defineConfig(
  globalIgnores([
    '**/.*',
    '**/node_modules/**',
    '**/dist/**',
    '**/build/**',
    '**/coverage/**',
    '**/*.d.ts',
    'public/**',
    'src/assets/**',
    'src/**/iconfont/**',
  ]),

  js.configs.recommended,
  ...tseslint.configs.recommended,
  ...pluginVue.configs['flat/recommended'],

  {
    files: ['src/**/*.{js,ts,tsx,vue}'],
    languageOptions: {
      globals: browserGlobals,
      parserOptions: {
        ecmaVersion: 'latest',
        sourceType: 'module',
        parser: tseslint.parser,
      },
    },
    rules: {
      // TypeScript 已覆盖变量使用检查，避免与基础规则重复报告。
      'no-unused-vars': 'off',
      '@typescript-eslint/no-unused-vars': [
        'error',
        { argsIgnorePattern: '^_', varsIgnorePattern: '^_' },
      ],
      '@typescript-eslint/consistent-type-imports': [
        'error',
        { fixStyle: 'inline-type-imports', prefer: 'type-imports' },
      ],
      '@typescript-eslint/no-explicit-any': 'off',
      '@typescript-eslint/no-non-null-assertion': 'off',
      'no-debugger': 'error',
      'no-console': ['warn', { allow: ['error', 'warn'] }],

      // 现有项目已使用这些 Vue 写法，保留兼容性但继续采用 Vue 推荐规则。
      'vue/multi-word-component-names': 'off',
      'vue/require-default-prop': 'off',
      'vue/require-explicit-emits': 'off',
      'vue/no-v-html': 'off',
    },
  },

  // Prettier 只负责格式化；此配置关闭与它重叠的 ESLint 风格规则。
  configPrettier
)

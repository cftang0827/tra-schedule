module.exports = {
    root: true,
    env: {
      browser: true,
      node: true,
      es2021: true,
    },
    parser: 'vue-eslint-parser', // 讓 ESLint 支援 .vue 檔
    parserOptions: {
      parser: '@babel/eslint-parser', // 解析 <script> 中的 JS
      ecmaVersion: 2021,
      sourceType: 'module',
      requireConfigFile: false,
    },
    extends: [
      'eslint:recommended',
      'plugin:vue/recommended', // Vue 3 專用設定
    ],
    plugins: ['vue'],
    rules: {
      'vue/multi-word-component-names': 'off',
      'no-console': 'off',
    },
    globals: {
      defineProps: 'readonly',
      defineEmits: 'readonly',
      defineExpose: 'readonly',
      withDefaults: 'readonly',
    },
  }
  
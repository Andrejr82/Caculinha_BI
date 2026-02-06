import js from '@eslint/js';
import tseslint from 'typescript-eslint';
import solidPlugin from 'eslint-plugin-solid/configs/typescript';

export default [
  js.configs.recommended,
  ...tseslint.configs.recommended,
  solidPlugin,
  {
    ignores: ['dist/**', 'node_modules/**', '*.config.*'],
  },
];



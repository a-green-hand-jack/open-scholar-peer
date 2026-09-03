import tseslint from "typescript-eslint";

export default tseslint.config(
  { ignores: ["dist/**", "build/**", "node_modules/**"] },
  {
    files: ["src/**/*.ts", "tests/**/*.ts"],
    languageOptions: { parser: tseslint.parser },
    plugins: { "@typescript-eslint": tseslint.plugin },
    rules: {
      "@typescript-eslint/no-unused-vars": ["error", { argsIgnorePattern: "^_" }],
    },
  },
);

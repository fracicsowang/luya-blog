// Astro config for luyaxyz.com/blog/
// - site = https://luyaxyz.com so canonical URLs + sitemap are correct
// - base = "/blog" so links start with /blog/...
// - build to ./dist; daily publisher rsyncs dist/ -> ../site/blog/ (never point outDir at the live folder)
// - trailingSlash "always" matches GitHub Pages directory-URL behavior
import { defineConfig } from "astro/config";

export default defineConfig({
  site: "https://luyaxyz.com",
  base: "/blog",
  trailingSlash: "always",
  build: { format: "directory", assets: "_astro" },
  markdown: {
    shikiConfig: { theme: "github-light", wrap: true },
  },
});

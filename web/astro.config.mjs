import { defineConfig } from "astro/config";

export default defineConfig({
  site: "https://modelarena.tv",
  build: {
    assets: "_assets",
  },
  vite: {
    build: {
      cssMinify: true,
    },
  },
});

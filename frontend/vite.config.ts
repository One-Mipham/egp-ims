import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import tailwindcss from '@tailwindcss/vite'
import path from 'path'

const BASE = process.env.VITE_BASE || '/'
const LOCALE = process.env.VITE_DEFAULT_LOCALE || 'zh-CN'
const LANG = LOCALE === 'en-US' ? 'en' : 'zh-CN'
const TITLE = LOCALE === 'en-US'
  ? 'Enterprise General-Purpose IMS (EGP-IMS)'
  : '企业通用智能管理系统（EGP-IMS）'

export default defineConfig({
  base: BASE,
  plugins: [
    vue(),
    tailwindcss(),
    {
      name: 'html-env',
      transformIndexHtml(html) {
        return html
          .replace('%BASE%', BASE)
          .replace('%LANG%', LANG)
          .replace('%TITLE%', TITLE)
      },
    },
  ],
  resolve: {
    alias: { '@': path.resolve(__dirname, 'src') },
  },
  server: {
    port: 3000,
    proxy: {
      [`${BASE}api`]: {
        target: 'http://localhost:8000',
        rewrite: (p) => p.replace(new RegExp(`^${BASE}`), '/'),
      },
    },
  },
})

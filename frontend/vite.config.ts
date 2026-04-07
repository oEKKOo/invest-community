import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'
import AutoImport from 'unplugin-auto-import/vite'
import Components from 'unplugin-vue-components/vite'
import { ElementPlusResolver } from 'unplugin-vue-components/resolvers'
import viteCompression from 'vite-plugin-compression'
import { visualizer } from 'rollup-plugin-visualizer'
import { constants as zlibConstants } from 'zlib'

export default defineConfig(({ mode }) => ({
  plugins: [
    vue(),
    AutoImport({
      resolvers: [ElementPlusResolver({ importStyle: 'css' })],
    }),
    Components({
      resolvers: [ElementPlusResolver({ importStyle: 'css' })],
    }),
    viteCompression({
      algorithm: 'gzip',
      ext: '.gz',
      threshold: 10240,
      deleteOriginFile: false
    }),
    viteCompression({
      algorithm: 'brotliCompress',
      ext: '.br',
      threshold: 10240,
      deleteOriginFile: false,
      compressionOptions: {
        params: {
          [zlibConstants.BROTLI_PARAM_QUALITY]: 11
        }
      }
    }),
    mode === 'analyze' &&
      visualizer({
        filename: 'dist/stats.html',
        gzipSize: true,
        brotliSize: true,
        open: false,
      }),
  ].filter(Boolean),
  resolve: {
    alias: {
      '@': resolve(__dirname, 'src'),
    },
    dedupe: ['dayjs', 'echarts', 'vue-echarts', 'zrender'],
  },
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
        secure: false,
      },
    },
  },
  css: {
    preprocessorOptions: {
      scss: {
        additionalData: `@use "@/styles/variables.scss" as *;`,
        silenceDeprecations: ['legacy-js-api']
      },
    },
  },
  build: {
    sourcemap: false,
    minify: 'esbuild',
    esbuild: {
      drop: ['console', 'debugger']
    },
    rollupOptions: {
      output: {
        manualChunks(id, { getModuleInfo }) {
          const normalizedId = id.replace(/\\/g, '/')

          const isImportedByAdminView = (moduleId: string, seen = new Set<string>()): boolean => {
            if (seen.has(moduleId)) return false
            seen.add(moduleId)
            const info = getModuleInfo(moduleId)
            if (!info) return false
            const all = [...info.importers, ...info.dynamicImporters]
            for (const imp of all) {
              const n = imp.replace(/\\/g, '/')
              if (n.includes('/views/admin/') || n.includes('AdminPanel.vue')) {
                return true
              }
              if (isImportedByAdminView(imp, seen)) return true
            }
            return false
          }

          if (
            normalizedId.includes('/node_modules/vue/') ||
            normalizedId.includes('/node_modules/pinia/') ||
            normalizedId.includes('/node_modules/vue-router/')
          ) {
            return 'vendor-vue'
          }
          if (normalizedId.includes('/node_modules/@element-plus/icons-vue/')) {
            return 'vendor-element-icons'
          }
          if (
            normalizedId.includes('/node_modules/element-plus/es/components/table') ||
            normalizedId.includes('/node_modules/element-plus/es/components/form') ||
            normalizedId.includes('/node_modules/element-plus/es/components/select') ||
            normalizedId.includes('/node_modules/element-plus/es/components/pagination') ||
            normalizedId.includes('/node_modules/element-plus/es/components/dialog') ||
            normalizedId.includes('/node_modules/element-plus/es/components/drawer') ||
            normalizedId.includes('/node_modules/element-plus/es/components/upload') ||
            normalizedId.includes('/node_modules/element-plus/es/components/dropdown') ||
            normalizedId.includes('/node_modules/element-plus/es/components/tooltip') ||
            normalizedId.includes('/node_modules/element-plus/es/components/popper') ||
            normalizedId.includes('/node_modules/@floating-ui') ||
            normalizedId.includes('/node_modules/async-validator') ||
            normalizedId.includes('/node_modules/lodash-unified')
          ) {
            if (isImportedByAdminView(id)) {
              return 'vendor-element-admin'
            }
            return 'vendor-element-advanced'
          }
          if (
            normalizedId.includes('/node_modules/echarts/') ||
            normalizedId.includes('/node_modules/zrender/') ||
            normalizedId.includes('/node_modules/vue-echarts/')
          ) {
            // 单一 chunk，避免按页面拆分导致同一份 echarts/zrender 被复制进多个异步包
            return 'vendor-echarts'
          }
          if (normalizedId.includes('/node_modules/lightweight-charts/')) {
            return 'vendor-lightweight-chart'
          }
          if (normalizedId.includes('/node_modules/dayjs/')) {
            return 'vendor-dayjs'
          }
        },
        chunkFileNames: 'assets/js/[name]-[hash].js',
        entryFileNames: 'assets/js/[name]-[hash].js',
        assetFileNames: 'assets/[ext]/[name]-[hash].[ext]'
      }
    },
    reportCompressedSize: false,
    chunkSizeWarningLimit: 900
  }
}))
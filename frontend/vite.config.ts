import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'
import AutoImport from 'unplugin-auto-import/vite'
import Components from 'unplugin-vue-components/vite'
import { ElementPlusResolver } from 'unplugin-vue-components/resolvers'
import viteCompression from 'vite-plugin-compression'
import { constants as zlibConstants } from 'zlib'

export default defineConfig({
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
  ],
  resolve: {
    alias: {
      '@': resolve(__dirname, 'src'),
    },
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
    rollupOptions: {
      output: {
        manualChunks(id, { getModuleInfo }) {
          const normalizedId = id.replace(/\\/g, '/')

          const isImportedByView = (moduleId: string, viewNames: string[], seen = new Set<string>()): boolean => {
            if (seen.has(moduleId)) return false
            seen.add(moduleId)
            const info = getModuleInfo(moduleId)
            if (!info) return false
            const allImporters = [...info.importers, ...info.dynamicImporters]
            for (const importer of allImporters) {
              if (
                viewNames.some(
                  (name) => importer.includes(`/views/${name}.vue`) || importer.includes(`\\views\\${name}.vue`)
                )
              ) {
                return true
              }
              if (isImportedByView(importer, viewNames, seen)) {
                return true
              }
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
            return 'vendor-element-advanced'
          }
          if (
            normalizedId.includes('/node_modules/echarts/') ||
            normalizedId.includes('/node_modules/zrender/') ||
            normalizedId.includes('/node_modules/vue-echarts/')
          ) {
            if (isImportedByView(id, ['Dashboard'])) {
              return 'vendor-echarts-dashboard'
            }
            if (isImportedByView(id, ['Portfolios', 'PortfolioDetail', 'MyHoldings'])) {
              return 'vendor-echarts-portfolio'
            }
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
})
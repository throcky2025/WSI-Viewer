import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import path from 'path'
import fs from 'fs'

// 复制OpenSeadragon图像到public目录
function copyOpenSeadragonImages() {
  const sourceDir = 'node_modules/openseadragon/build/openseadragon/images'
  const targetDir = 'public/openseadragon/images'
  
  try {
    // 确保目标目录存在
    fs.mkdirSync(targetDir, { recursive: true })
    
    // 复制所有图像文件
    const imageFiles = fs.readdirSync(sourceDir)
    imageFiles.forEach(file => {
      if (file.endsWith('.png')) {
        fs.copyFileSync(
          path.join(sourceDir, file),
          path.join(targetDir, file)
        )
        console.log(`Copied OpenSeadragon image: ${file}`)
      }
    })
  } catch (err) {
    console.error('Error copying OpenSeadragon images:', err)
  }
}

// Vite配置
export default defineConfig({
  plugins: [
    vue(),
    {
      name: 'copy-openseadragon-images',
      buildStart() {
        copyOpenSeadragonImages()
      },
      configureServer(server) {
        server.middlewares.use((req, res, next) => {
          if (req.url?.startsWith('/openseadragon/')) {
            // 允许OpenSeadragon资源的CORS
            res.setHeader('Access-Control-Allow-Origin', '*')
          }
          next()
        })
      }
    }
  ],
  
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:5000',
        changeOrigin: true,
        ws: true,
        secure: false,
        timeout: 300000,  // 5分钟超时
        headers: {
          'Connection': 'keep-alive'
        }
      },
      '/static': {
        target: 'http://localhost:5000',
        changeOrigin: true
      },
      '/ws': {
        target: 'ws://localhost:5000',
        ws: true,
        changeOrigin: true
      }
    }
  },
  
  resolve: {
    alias: {
      '@': path.resolve(__dirname, 'src')
    }
  },
  
  build: {
    outDir: '../static/frontend',
    emptyOutDir: true,
    sourcemap: true,
    
    // 优化构建配置
    rollupOptions: {
      output: {
        manualChunks: {
          'vendor': ['vue', 'element-plus'],
          'openseadragon': ['openseadragon']
        },
        chunkFileNames: 'assets/[name]-[hash].js',
        assetFileNames: 'assets/[name]-[hash][extname]'
      }
    },
    
    // 优化代码分割
    chunkSizeWarningLimit: 1000,
    
    // 资源处理
    assetsInlineLimit: 4096,
    
    // 调试优化
    minify: process.env.NODE_ENV === 'production',
    
    // CSS优化
    cssCodeSplit: true,
    
    // 兼容性
    target: 'es2015'
  },
  
  optimizeDeps: {
    include: ['openseadragon']
  }
})
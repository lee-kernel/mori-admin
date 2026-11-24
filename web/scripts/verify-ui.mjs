#!/usr/bin/env node
/**
 * UI 自动化视觉与布局自检脚本（零外部 npm 依赖，基于 Node 24 原生 WebSocket + 本地 Chromium CDP）。
 *
 * 用法：
 *   npm run verify:ui                                  # 自动起 preview 服务并检查全部内置范例页
 *   npm run verify:ui -- /patterns/card-grid           # 检查指定路由
 *   npm run verify:ui -- --screenshots                 # 同时输出浅/深色 × 桌面/窄屏截图到 web/.ui-verify/
 *   npm run verify:ui -- --url http://127.0.0.1:5173   # 连接已运行的前端服务
 */

import { spawn } from 'node:child_process'
import fs from 'node:fs'
import net from 'node:net'
import os from 'node:os'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const WEB_ROOT = path.resolve(__dirname, '..')
const SCREENSHOT_DIR = path.join(WEB_ROOT, '.ui-verify')

const DEFAULT_ROUTES = [
  '/patterns/workspace',
  '/patterns/card-grid',
  '/patterns/detail',
  '/patterns/drawer-form',
]

const MATRICES = [
  { name: 'desktop-light', width: 1440, height: 900, mobile: false, theme: 'light' },
  { name: 'desktop-dark', width: 1440, height: 900, mobile: false, theme: 'dark' },
  { name: 'mobile-light', width: 390, height: 844, mobile: true, theme: 'light' },
  { name: 'mobile-dark', width: 390, height: 844, mobile: true, theme: 'dark' },
]

function parseArgs(argv) {
  const routes = []
  let url = ''
  let screenshots = false

  for (let i = 0; i < argv.length; i += 1) {
    const arg = argv[i]
    if (arg === '--screenshots') {
      screenshots = true
    } else if (arg === '--url' && argv[i + 1]) {
      url = argv[i + 1].replace(/\/+$/, '')
      i += 1
    } else if (arg.startsWith('/')) {
      routes.push(arg)
    }
  }

  return {
    routes: routes.length > 0 ? routes : DEFAULT_ROUTES,
    url,
    screenshots,
  }
}

function findBrowserExecutable() {
  if (process.env.CHROME_PATH && fs.existsSync(process.env.CHROME_PATH)) {
    return process.env.CHROME_PATH
  }

  const candidates =
    process.platform === 'win32'
      ? [
          'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe',
          'C:\\Program Files\\Microsoft\\Edge\\Application\\msedge.exe',
          'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',
          'C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe',
        ]
      : process.platform === 'darwin'
        ? [
            '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
            '/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge',
            '/Applications/Chromium.app/Contents/MacOS/Chromium',
          ]
        : [
            '/usr/bin/google-chrome',
            '/usr/bin/chromium',
            '/usr/bin/chromium-browser',
            '/usr/bin/microsoft-edge',
          ]

  return candidates.find((p) => fs.existsSync(p)) || null
}

function getFreePort() {
  return new Promise((resolve, reject) => {
    const server = net.createServer()
    server.unref()
    server.on('error', reject)
    server.listen(0, '127.0.0.1', () => {
      const addr = server.address()
      const port = typeof addr === 'object' && addr ? addr.port : 0
      server.close(() => resolve(port))
    })
  })
}

async function waitForHttp(targetUrl, timeoutMs = 20000) {
  const deadline = Date.now() + timeoutMs
  while (Date.now() < deadline) {
    try {
      const res = await fetch(targetUrl)
      if (res.ok) return
    } catch {
      // 等待服务启动
    }
    await new Promise((r) => setTimeout(r, 200))
  }
  throw new Error(`等待服务就绪超时：${targetUrl}`)
}

function startPreviewServer(port) {
  const viteBin = path.join(WEB_ROOT, 'node_modules', 'vite', 'bin', 'vite.js')
  const child = spawn(
    process.execPath,
    [viteBin, '--mode', 'preview', '--host', '127.0.0.1', '--port', String(port), '--strictPort'],
    {
      cwd: WEB_ROOT,
      stdio: ['ignore', 'pipe', 'pipe'],
    }
  )

  let stderr = ''
  child.stderr.on('data', (chunk) => {
    stderr += chunk.toString()
  })

  return {
    child,
    getStderr: () => stderr,
  }
}

async function connectCdp(wsUrl) {
  const ws = new WebSocket(wsUrl)
  await new Promise((resolve, reject) => {
    ws.addEventListener('open', resolve, { once: true })
    ws.addEventListener('error', reject, { once: true })
  })

  let nextId = 1
  const pending = new Map()
  const listeners = new Map()

  ws.addEventListener('message', (event) => {
    const msg = JSON.parse(String(event.data))
    if (msg.id) {
      const entry = pending.get(msg.id)
      if (!entry) return
      pending.delete(msg.id)
      if (msg.error) {
        entry.reject(new Error(`CDP ${msg.error.code}: ${msg.error.message}`))
      } else {
        entry.resolve(msg.result)
      }
    } else if (msg.method) {
      const handlers = listeners.get(msg.method)
      if (handlers) {
        for (const fn of handlers) fn(msg.params)
      }
    }
  })

  return {
    send(method, params = {}, timeoutMs = 15000) {
      const id = nextId++
      return new Promise((resolve, reject) => {
        const timer = setTimeout(() => {
          pending.delete(id)
          reject(new Error(`CDP 调用超时 (${timeoutMs}ms): ${method}`))
        }, timeoutMs)
        pending.set(id, {
          resolve: (val) => {
            clearTimeout(timer)
            resolve(val)
          },
          reject: (err) => {
            clearTimeout(timer)
            reject(err)
          },
        })
        ws.send(JSON.stringify({ id, method, params }))
      })
    },
    on(method, fn) {
      if (!listeners.has(method)) listeners.set(method, new Set())
      listeners.get(method).add(fn)
    },
    close() {
      ws.close()
    },
  }
}

async function waitForPageSettled(cdp, expectedRoute, timeoutMs = 8000) {
  const deadline = Date.now() + timeoutMs
  while (Date.now() < deadline) {
    const res = await cdp.send('Runtime.evaluate', {
      expression: `(() => {
        const ready = document.readyState === 'complete';
        const hashPath = (location.hash || '').replace(/^#/, '').split('?')[0];
        const routeMatched = !${JSON.stringify(expectedRoute)} || hashPath === ${JSON.stringify(expectedRoute)};
        const hasLayout = Boolean(document.querySelector('.page-layout'));
        const textLen = (document.body?.innerText || '').trim().length;
        return { ready, routeMatched, hasLayout, textLen, hashPath };
      })()`,
      returnByValue: true,
    })
    const value = res?.result?.value
    if (value?.ready && value?.routeMatched && value?.hasLayout && value?.textLen > 0) {
      await new Promise((r) => setTimeout(r, 400))
      return value
    }
    await new Promise((r) => setTimeout(r, 150))
  }
  return { ready: false, routeMatched: false, hasLayout: false, textLen: 0, hashPath: '' }
}

async function main() {
  const { routes, url, screenshots } = parseArgs(process.argv.slice(2))
  const browserPath = findBrowserExecutable()
  if (!browserPath) {
    console.error(
      '[verify:ui] 未找到本地 Chrome/Edge 浏览器，请通过环境变量 CHROME_PATH 指定可执行文件路径。'
    )
    process.exit(1)
  }

  let baseUrl = url
  let previewProc = null
  let browserProc = null
  let cdp = null
  const userDataDir = fs.mkdtempSync(path.join(os.tmpdir(), 'mori-verify-ui-'))

  try {
    if (!baseUrl) {
      const vitePort = await getFreePort()
      baseUrl = `http://127.0.0.1:${vitePort}`
      previewProc = startPreviewServer(vitePort)
      await waitForHttp(baseUrl)
    }

    const cdpPort = await getFreePort()
    browserProc = spawn(
      browserPath,
      [
        '--headless=new',
        '--disable-gpu',
        '--no-first-run',
        '--no-default-browser-check',
        `--remote-debugging-port=${cdpPort}`,
        `--user-data-dir=${userDataDir}`,
        'about:blank',
      ],
      { stdio: ['ignore', 'ignore', 'pipe'] }
    )

    await waitForHttp(`http://127.0.0.1:${cdpPort}/json/list`, 15000)
    const targets = await (await fetch(`http://127.0.0.1:${cdpPort}/json/list`)).json()
    const pageTarget = targets.find((t) => t.type === 'page' && t.webSocketDebuggerUrl)
    if (!pageTarget) {
      throw new Error('未能获取浏览器调试页目标')
    }

    cdp = await connectCdp(pageTarget.webSocketDebuggerUrl)
    await cdp.send('Page.enable')
    await cdp.send('Runtime.enable')
    await cdp.send('Network.enable')

    let currentErrors = []
    cdp.on('Runtime.exceptionThrown', (params) => {
      const desc =
        params?.exceptionDetails?.exception?.description ||
        params?.exceptionDetails?.text ||
        '未捕获异常'
      currentErrors.push(`JS 异常: ${desc}`)
    })
    cdp.on('Runtime.consoleAPICalled', (params) => {
      if (params.type === 'error') {
        const text = (params.args || []).map((a) => a.value ?? a.description ?? '').join(' ')
        currentErrors.push(`console.error: ${text}`)
      }
    })
    cdp.on('Network.responseReceived', (params) => {
      const status = params?.response?.status
      const reqUrl = params?.response?.url || ''
      if (status >= 400 && !reqUrl.endsWith('/favicon.ico')) {
        currentErrors.push(`HTTP ${status}: ${reqUrl}`)
      }
    })

    if (screenshots) {
      fs.mkdirSync(SCREENSHOT_DIR, { recursive: true })
    }

    // 先打开一次同源页以便写入 localStorage
    await cdp.send('Page.navigate', { url: `${baseUrl}/#${routes[0]}` })
    await waitForPageSettled(cdp, routes[0])

    const failures = []
    let passedCount = 0

    for (const route of routes) {
      for (const matrix of MATRICES) {
        currentErrors = []

        await cdp.send('Emulation.setDeviceMetricsOverride', {
          width: matrix.width,
          height: matrix.height,
          deviceScaleFactor: 1,
          mobile: matrix.mobile,
        })
        await cdp.send('Emulation.setEmulatedMedia', {
          features: [{ name: 'prefers-color-scheme', value: matrix.theme }],
        })
        await cdp.send('Runtime.evaluate', {
          expression: `localStorage.setItem('mori_admin_theme_mode', ${JSON.stringify(matrix.theme)})`,
        })

        // 强制切换路由并等待重载完成，避免截到上一路由的残留 DOM
        const loadPromise = new Promise((resolve) => {
          const handler = () => resolve()
          cdp.on('Page.loadEventFired', handler)
          setTimeout(resolve, 5000)
        })
        await cdp.send('Runtime.evaluate', {
          expression: `location.replace(${JSON.stringify(`${baseUrl}/#${route}`)}); location.reload();`,
        })
        await loadPromise
        const settled = await waitForPageSettled(cdp, route)

        const metricsRes = await cdp.send('Runtime.evaluate', {
          expression: `(() => {
            const docOverflow = document.documentElement.scrollWidth - window.innerWidth;
            const bodyOverflow = document.body.scrollWidth - window.innerWidth;
            const hasPageLayout = Boolean(document.querySelector('.page-layout'));
            return { docOverflow, bodyOverflow, hasPageLayout };
          })()`,
          returnByValue: true,
        })
        const metrics = metricsRes?.result?.value || {
          docOverflow: 0,
          bodyOverflow: 0,
          hasPageLayout: false,
        }

        const caseErrors = [...currentErrors]
        if (!settled.hasLayout || !metrics.hasPageLayout) {
          caseErrors.push('未检测到 .page-layout 根节点或页面未完成渲染')
        }
        if (metrics.docOverflow > 1 || metrics.bodyOverflow > 1) {
          caseErrors.push(
            `存在横向溢出（document=${metrics.docOverflow}px, body=${metrics.bodyOverflow}px）`
          )
        }

        if (screenshots) {
          const slug = route.replace(/^\/+/, '').replace(/[^a-zA-Z0-9-_]+/g, '_') || 'root'
          const shot = await cdp.send('Page.captureScreenshot', { format: 'png' })
          const outPath = path.join(SCREENSHOT_DIR, `${slug}-${matrix.name}.png`)
          fs.writeFileSync(outPath, Buffer.from(shot.data, 'base64'))
        }

        const label = `${route} [${matrix.name} ${matrix.width}x${matrix.height}]`
        if (caseErrors.length > 0) {
          console.error(`  ✗ ${label}`)
          for (const err of caseErrors) {
            console.error(`    - ${err}`)
          }
          failures.push({ label, errors: caseErrors })
        } else {
          passedCount += 1
          console.log(`  ✓ ${label}`)
        }
      }
    }

    if (screenshots) {
      console.log(`\n[verify:ui] 截图已保存至 ${path.relative(WEB_ROOT, SCREENSHOT_DIR)}/`)
    }

    if (failures.length > 0) {
      console.error(`\n[verify:ui] 检查失败：${failures.length} 项未通过，${passedCount} 项通过。`)
      process.exit(1)
    }

    console.log(`\n[verify:ui] 全部 ${passedCount} 项视口与主题检查通过。`)
  } finally {
    if (cdp) cdp.close()
    if (browserProc) browserProc.kill()
    if (previewProc) previewProc.child.kill()
    try {
      fs.rmSync(userDataDir, { recursive: true, force: true })
    } catch {
      // 忽略 Windows 临时目录释放延迟
    }
  }
}

main().catch((err) => {
  console.error('[verify:ui] 执行异常：', err)
  process.exit(1)
})

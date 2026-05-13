#!/usr/bin/env node
/*
 * Helper de comunicação ATEM para a GUI Python.
 *
 * Ele mantém a lógica comprovada do projeto original com atem-connection,
 * escreve o TXT de uma linha para o OBS e envia eventos JSON para a GUI.
 */

const { Atem } = require('atem-connection')
const fs = require('fs')
const path = require('path')

function parseArgs(argv) {
  const args = {
    ip: '192.168.2.146',
    fps: 60,
    output: path.join(process.cwd(), 'rec-live.txt'),
    updateMs: 100,
    reconnectMs: 5000,
  }

  for (let i = 2; i < argv.length; i++) {
    const key = argv[i]
    const value = argv[i + 1]
    if (!value) continue

    if (key === '--ip') args.ip = value
    if (key === '--fps') args.fps = Number(value) || 60
    if (key === '--output') args.output = value
    if (key === '--update-ms') args.updateMs = Number(value) || 100
    if (key === '--reconnect-ms') args.reconnectMs = Number(value) || 5000

    if (key.startsWith('--')) i++
  }
  return args
}

const config = parseArgs(process.argv)
const ATEM_IP = config.ip
const FPS = config.fps
const TXT_FILE = path.resolve(config.output)
const UPDATE_INTERVAL_MS = config.updateMs
const RECONNECT_INTERVAL_MS = config.reconnectMs

function emit(type, payload = {}) {
  const event = { type, ...payload, ts: new Date().toISOString() }
  process.stdout.write(JSON.stringify(event) + '\n')
}

function pad(num, size = 2) {
  return String(num).padStart(size, '0')
}

function formatTimecode(tc) {
  if (!tc) return '---:--:--:--'
  return `${pad(tc.hours)}:${pad(tc.minutes)}:${pad(tc.seconds)}:${pad(tc.frames)}`
}

function tcToFrames(tc, fps) {
  const hours = tc.hours || 0
  const minutes = tc.minutes || 0
  const seconds = tc.seconds || 0
  const frames = tc.frames || 0
  return (((hours * 60 + minutes) * 60 + seconds) * fps) + frames
}

function framesToTc(totalFrames, fps) {
  const frames = totalFrames % fps
  const totalSeconds = Math.floor(totalFrames / fps)
  const seconds = totalSeconds % 60
  const totalMinutes = Math.floor(totalSeconds / 60)
  const minutes = totalMinutes % 60
  const hours = Math.floor(totalMinutes / 60)
  return { hours, minutes, seconds, frames }
}

let lastFileText = ''
let lastEmittedText = ''

function renderFile(text) {
  if (text === lastFileText) return
  lastFileText = text

  const dir = path.dirname(TXT_FILE)
  fs.mkdirSync(dir, { recursive: true })
  const tmp = TXT_FILE + '.tmp'
  fs.writeFile(tmp, text, err => {
    if (err) {
      emit('error', { text: `Erro ao escrever arquivo temporário: ${err.message}` })
      return
    }
    fs.rename(tmp, TXT_FILE, err2 => {
      if (err2) {
        emit('error', { text: `Erro ao renomear TXT: ${err2.message}` })
      }
    })
  })
}

function publish(type, text, force = false) {
  renderFile(text)
  if (force || text !== lastEmittedText || type === 'recording') {
    lastEmittedText = text
    emit(type, { text, output: TXT_FILE })
  }
}

let baseFrames = null
let baseSystemTime = null
let hasRecBase = false
let lastShownTc = null
let mode = 'idle'
let isConnected = false
let reconnectTimer = null

const atem = new Atem()

function attemptConnect() {
  if (!isConnected) {
    try {
      atem.connect(ATEM_IP)
    } catch (err) {
      emit('error', { text: `Erro ao conectar: ${err.message}` })
    }
  }
}

function setupReconnectTimer() {
  if (reconnectTimer) clearInterval(reconnectTimer)
  reconnectTimer = setInterval(() => {
    if (!isConnected) {
      emit('log', { text: 'Tentando reconectar à ATEM...' })
      attemptConnect()
    }
  }, RECONNECT_INTERVAL_MS)
}

emit('log', { text: `Conectando à ATEM em ${ATEM_IP} (FPS: ${FPS})...` })

atem.on('connected', () => {
  isConnected = true
  emit('connected', { text: 'Conectado! Sincronizando com o REC...' })

  if (reconnectTimer) {
    clearInterval(reconnectTimer)
    reconnectTimer = null
  }

  const frameDurationMs = 1000 / FPS

  if (atem._mainLoop) clearInterval(atem._mainLoop)

  const mainLoop = setInterval(() => {
    if (!isConnected) {
      clearInterval(mainLoop)
      return
    }

    const now = Date.now()
    const recording = atem.state?.recording
    const recState = recording?.status?.state
    const recTc = recording?.duration
    const isRecording = (recState === 1)

    if (!isRecording) {
      if (mode === 'recording') {
        mode = 'stopped'
        hasRecBase = false
        const text = `⏹ REC PARADO em: ${formatTimecode(lastShownTc)}`
        publish('stopped', text, true)
      } else if (mode === 'idle') {
        publish('idle', '⏺ Aguardando REC na ATEM...')
      }
      return
    }

    if (mode !== 'recording') {
      if (!recTc) {
        mode = 'recording'
        publish('waiting_tc', '🔴 REC DETECTADO, aguardando TC...', true)
        return
      }

      baseFrames = tcToFrames(recTc, FPS)
      baseSystemTime = now
      hasRecBase = true
      lastShownTc = recTc
      mode = 'recording'
      publish('recording', `🎥 REC INICIADO | ${formatTimecode(recTc)}`, true)
      return
    }

    if (mode === 'recording' && hasRecBase) {
      const elapsedMs = now - baseSystemTime
      const addedFrames = Math.floor(elapsedMs / frameDurationMs)
      const totalFrames = baseFrames + addedFrames
      const localTc = framesToTc(totalFrames, FPS)
      lastShownTc = localTc
      publish('recording', `🔴 GRAVANDO | REC TIME: ${formatTimecode(localTc)}`)
    }
  }, UPDATE_INTERVAL_MS)

  atem._mainLoop = mainLoop
})

atem.on('disconnected', () => {
  isConnected = false
  emit('disconnected', { text: 'Desconectado da ATEM. Tentando reconectar...' })

  if (atem._mainLoop) {
    clearInterval(atem._mainLoop)
    atem._mainLoop = null
  }

  setupReconnectTimer()
})

atem.on('error', (err) => {
  isConnected = false
  emit('error', { text: `Erro na ATEM: ${err.message}` })
})

function shutdown() {
  if (reconnectTimer) clearInterval(reconnectTimer)
  if (atem._mainLoop) clearInterval(atem._mainLoop)
  try {
    atem.disconnect()
  } catch (_) {}
  emit('log', { text: 'Encerrado.' })
  process.exit(0)
}

process.on('SIGINT', shutdown)
process.on('SIGTERM', shutdown)

attemptConnect()
setupReconnectTimer()

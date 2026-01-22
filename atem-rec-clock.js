// atem-rec-clock.js
// Mostra REC TIME sincronizado com a ATEM
// e grava em um TXT de UMA LINHA, estável pra usar no OBS (Read from file)
// VERSÃO MELHORADA: Monitora continuamente, sincroniza ao iniciar durante gravação, detecta parada rápido

const { Atem } = require('atem-connection')
const fs = require('fs')
const path = require('path')

// ===== CONFIGURAÇÕES =====
const ATEM_IP = '192.168.2.157'
const FPS = Number(process.argv[2]) || 60          // ex: node atem-rec-clock.js 25
const TXT_FILE = path.join(__dirname, 'rec-live.txt')
const UPDATE_INTERVAL_MS = 100                     // 100ms é suave pro OBS
const DEBOUNCE_MS = 500                            // 500ms pra detectar parada (reduzido de 1500ms)
const RECONNECT_INTERVAL_MS = 5000                 // Tentar reconectar a cada 5s se desconectar

// ===== FUNÇÕES =====
process.stdout.write('\x1b[?25l') // esconde cursor no terminal

function pad(num, size = 2) {
  return num.toString().padStart(size, '0')
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

let lastTerminalLine = ''
let lastFileText = ''

function renderTerminal(text) {
  if (text !== lastTerminalLine) {
    lastTerminalLine = text
    process.stdout.write('\r\x1b[2K' + text)
  }
}

// Escreve de forma "atômica": primeiro em .tmp, depois renomeia
function renderFile(text) {
  if (text === lastFileText) return
  lastFileText = text

  const tmp = TXT_FILE + '.tmp'
  fs.writeFile(tmp, text, err => {
    if (err) {
      console.error('Erro ao escrever .tmp:', err)
      return
    }
    fs.rename(tmp, TXT_FILE, err2 => {
      if (err2) {
        console.error('Erro ao renomear TXT:', err2)
      }
    })
  })
}

// ===== CLOCK =====
let baseFrames = null
let baseSystemTime = null
let hasRecBase = false
let lastShownTc = null

// estados: 'idle' | 'recording' | 'stopped'
let mode = 'idle'
let lastRecSeenAt = 0
let isConnected = false
let reconnectTimer = null

console.log(`Conectando à ATEM em ${ATEM_IP} (FPS: ${FPS})...`)
const atem = new Atem()

// ===== FUNÇÕES DE CONEXÃO =====
function attemptConnect() {
  if (!isConnected) {
    try {
      atem.connect(ATEM_IP)
    } catch (err) {
      console.error('Erro ao conectar:', err.message)
    }
  }
}

function setupReconnectTimer() {
  if (reconnectTimer) clearInterval(reconnectTimer)
  reconnectTimer = setInterval(() => {
    if (!isConnected) {
      console.log('🔄 Tentando reconectar à ATEM...')
      attemptConnect()
    }
  }, RECONNECT_INTERVAL_MS)
}

// ===== EVENT LISTENERS =====
atem.on('connected', () => {
  isConnected = true
  console.log('✅ Conectado! Sincronizando com o REC...\n')
  
  // Limpa timer de reconexão se estava ativo
  if (reconnectTimer) {
    clearInterval(reconnectTimer)
    reconnectTimer = null
  }

  const frameDurationMs = 1000 / FPS

  // ===== LOOP PRINCIPAL DE MONITORAMENTO =====
  const mainLoop = setInterval(() => {
    if (!isConnected) {
      clearInterval(mainLoop)
      return
    }

    const now = Date.now()
    const recTc = atem.state?.recording?.duration

    // ===== DETECÇÃO DE TC ATIVO =====
    if (recTc) {
      lastRecSeenAt = now
    }

    // Debounce: considera REC ativo se vimos TC nos últimos DEBOUNCE_MS
    const recSignalActive = (now - lastRecSeenAt) < DEBOUNCE_MS

    // ========== SEM REC / REC PARADO ==========
    if (!recSignalActive) {
      if (mode === 'recording') {
        // Transição recording -> stopped
        mode = 'stopped'
        const text = `⏹ REC PARADO em: ${formatTimecode(lastShownTc)}`
        renderTerminal(text)
        renderFile(text)
      } else if (mode === 'idle') {
        const text = '⏺ Aguardando REC na ATEM...'
        renderTerminal(text)
        renderFile(text)
      }
      // não zera baseFrames / lastShownTc, pra manter última info
      return
    }

    // ========== REC ATIVO DETECTADO ==========

    // ========== REC ACABOU DE COMEÇAR (ou já estava rodando) ==========
    if (mode !== 'recording') {
      // Primeira vez que detecta REC ativo
      
      if (!recTc) {
        // REC ativo mas sem TC ainda (raro, mas pode acontecer)
        const text = '🔴 REC DETECTADO, aguardando TC...'
        renderTerminal(text)
        renderFile(text)
        mode = 'recording'
        return
      }

      // ✅ SINCRONIZAÇÃO: REC já estava rodando quando o script iniciou
      // Aqui sincronizamos com o TC atual da ATEM
      baseFrames = tcToFrames(recTc, FPS)
      baseSystemTime = now
      hasRecBase = true
      lastShownTc = recTc
      mode = 'recording'

      const text = `🎥 REC INICIADO | ${formatTimecode(recTc)}`
      renderTerminal(text)
      renderFile(text)
      return
    }

    // ========== REC RODANDO (modo contínuo) ==========
    if (mode === 'recording' && hasRecBase) {
      const elapsedMs = now - baseSystemTime
      const addedFrames = Math.floor(elapsedMs / frameDurationMs)
      const totalFrames = baseFrames + addedFrames

      const localTc = framesToTc(totalFrames, FPS)
      lastShownTc = localTc

      const text = `🔴 GRAVANDO | REC TIME: ${formatTimecode(localTc)}`
      renderTerminal(text)
      renderFile(text)
      return
    }

  }, UPDATE_INTERVAL_MS)

  // Armazena a referência do loop para poder limpar depois
  atem._mainLoop = mainLoop
})

atem.on('disconnected', () => {
  isConnected = false
  console.log('\n❌ Desconectado da ATEM. Tentando reconectar...')
  
  // Limpa o loop anterior se existir
  if (atem._mainLoop) {
    clearInterval(atem._mainLoop)
    atem._mainLoop = null
  }

  // Inicia tentativas de reconexão
  setupReconnectTimer()
})

atem.on('error', (err) => {
  console.error('❌ Erro na ATEM:', err.message)
  isConnected = false
})

// ===== GRACEFUL SHUTDOWN =====
process.on('SIGINT', () => {
  process.stdout.write('\r\x1b[2K')
  process.stdout.write('\x1b[?25h')
  
  if (reconnectTimer) clearInterval(reconnectTimer)
  if (atem._mainLoop) clearInterval(atem._mainLoop)
  
  console.log('\n⏹ Encerrado.')
  process.exit(0)
})

// ===== INICIAR CONEXÃO =====
attemptConnect()
setupReconnectTimer()

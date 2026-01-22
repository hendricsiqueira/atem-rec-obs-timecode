// atem-rec-clock-debug.js
// Versão DEBUG para inspecionar o que a ATEM está enviando

const { Atem } = require('atem-connection')

// ===== CONFIGURAÇÕES =====
const ATEM_IP = '192.168.2.146'

console.log(`Conectando à ATEM em ${ATEM_IP}...`)
const atem = new Atem()
atem.connect(ATEM_IP)

atem.on('connected', () => {
  console.log('✅ Conectado!\n')
  console.log('=== MODO DEBUG ===')
  console.log('Vou mostrar TODOS os dados de recording que a ATEM envia.')
  console.log('Inicie e pare o REC para vermos o que muda.\n')

  setInterval(() => {
    const recording = atem.state?.recording
    
    if (recording) {
      console.log('--- Estado Recording ---')
      console.log('Full object:', JSON.stringify(recording, null, 2))
      console.log('------------------------\n')
    } else {
      console.log('⚠️ recording = undefined ou null\n')
    }
  }, 1000) // A cada 1 segundo
})

atem.on('disconnected', () => {
  console.log('\n❌ Desconectado da ATEM.')
})

atem.on('error', (err) => {
  console.error('❌ Erro:', err.message)
})

process.on('SIGINT', () => {
  console.log('\n⏹ Encerrado.')
  process.exit(0)
})

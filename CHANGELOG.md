# Changelog

## [2.0.0] - 2026-01-22

### ✨ Melhorias Principais

#### 🔄 Monitoramento Contínuo
- O script agora fica constantemente ouvindo o status da ATEM, mesmo sem REC ativo
- Não mais "congela" esperando por um REC que nunca vem
- Mostra status "Aguardando REC na ATEM..." enquanto não há gravação

#### 🎯 Sincronização Automática
- Se o script for iniciado durante uma gravação em andamento, sincroniza automaticamente com o TC atual
- Não perde mais o timecode se iniciar no meio de uma gravação
- Calcula corretamente o `baseFrames` e `baseSystemTime` no primeiro ciclo

#### ⚡ Detecção Rápida de Parada
- Reduzido o debounce de 1500ms para 500ms
- Detecta parada de REC muito mais rápido (~500ms vs ~1.5s antes)
- Melhor responsividade ao parar a gravação

#### 🔗 Reconexão Automática
- Se a ATEM desconectar, o script tenta reconectar automaticamente a cada 5 segundos
- Não precisa mais reiniciar o script manualmente após desconexão
- Mostra mensagens de status sobre tentativas de reconexão

#### 🛡️ Melhor Tratamento de Erros
- Adicionados listeners para `error` e `disconnected`
- Melhor limpeza de recursos (timers e intervals)
- Graceful shutdown ao pressionar Ctrl+C

### 🔧 Mudanças Técnicas

#### Novas Constantes
```js
const DEBOUNCE_MS = 500                    // Reduzido de 1500ms
const RECONNECT_INTERVAL_MS = 5000         // Novo: reconexão automática
```

#### Novas Funções
- `attemptConnect()`: Tenta conectar à ATEM
- `setupReconnectTimer()`: Configura timer de reconexão automática

#### Novos Event Listeners
- `atem.on('error', ...)`: Captura erros de conexão
- Melhorado `atem.on('disconnected', ...)`: Inicia reconexão automática

#### Melhorias no Loop Principal
- Armazenamento de referência do loop em `atem._mainLoop` para limpeza correta
- Melhor controle de estado de conexão com `isConnected`
- Sincronização imediata ao detectar REC ativo pela primeira vez

### 📝 Documentação
- README atualizado com informações sobre as melhorias
- Adicionadas instruções de ajustes avançados
- Melhorado troubleshooting

### 🐛 Bugs Corrigidos
- ✅ Script não ficava ouvindo sem REC ativo
- ✅ Sincronização falha ao iniciar durante gravação
- ✅ Desconexão não era tratada adequadamente
- ✅ Timers não eram limpos ao desconectar

## [1.0.0] - Inicial

### Features
- Conexão com ATEM via IP
- Leitura de timecode de REC
- Escrita atômica em arquivo TXT
- Suporte a FPS customizável
- Integração com OBS via "Read from file"

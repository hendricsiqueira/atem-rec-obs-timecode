# Guia de Testes - ATEM REC Timecode

Este documento descreve os testes recomendados para validar o funcionamento da versão melhorada.

## Pré-requisitos

- ATEM Mini Extreme ISO conectada à rede
- Mac com Python 3.11 ou superior instalado
- Dependências Python instaladas com `python3 -m pip install --user --break-system-packages -r python-gui/requirements.txt`
- IP da ATEM configurado na interface gráfica Python

## Cenários de Teste

### Teste 1: Inicialização Sem REC Ativo

**Objetivo**: Verificar se o script fica ouvindo quando a ATEM não está gravando.

**Passos**:
1. Certifique-se de que a ATEM NÃO está gravando (REC desligado)
2. Execute a GUI Python: `cd python-gui && python3 app.py`
3. Observe o terminal

**Resultado Esperado**:
- Script conecta à ATEM com mensagem "✅ Conectado! Sincronizando com o REC..."
- Terminal mostra: "⏺ Aguardando REC na ATEM..."
- Arquivo `rec-live.txt` é criado com o mesmo conteúdo
- Script fica aguardando sem erros ou travamentos

**Status**: ✅ Passou / ❌ Falhou

---

### Teste 2: Iniciar REC Após Script Rodando

**Objetivo**: Verificar se o script detecta e sincroniza quando REC é iniciado.

**Passos**:
1. Deixe a GUI Python conforme Teste 1 (aguardando REC)
2. Na ATEM, pressione REC para iniciar gravação
3. Observe o terminal e o arquivo `rec-live.txt`

**Resultado Esperado**:
- Terminal muda para: "🎥 REC INICIADO | HH:MM:SS:FF"
- Timecode começa a contar: "🔴 GRAVANDO | REC TIME: HH:MM:SS:FF"
- Arquivo `rec-live.txt` é atualizado em tempo real
- Timecode incrementa corretamente a cada frame

**Status**: ✅ Passou / ❌ Falhou

---

### Teste 3: Parar REC

**Objetivo**: Verificar se o script detecta parada de gravação rapidamente.

**Passos**:
1. Com o script rodando e REC ativo (Teste 2)
2. Na ATEM, pressione REC novamente para parar
3. Observe o terminal e o arquivo `rec-live.txt`

**Resultado Esperado**:
- Terminal muda para: "⏹ REC PARADO em: HH:MM:SS:FF"
- Timecode congela no último valor
- Detecção ocorre em ~500ms (não demora 1.5s)
- Arquivo `rec-live.txt` é atualizado

**Status**: ✅ Passou / ❌ Falhou

---

### Teste 4: Sincronização Durante Gravação

**Objetivo**: Verificar se o script sincroniza corretamente ao iniciar durante uma gravação em andamento.

**Passos**:
1. Na ATEM, inicie uma gravação (REC ativo)
2. Aguarde alguns segundos (ex: 5-10 segundos de gravação)
3. Execute a GUI Python: `cd python-gui && python3 app.py`
4. Observe o terminal

**Resultado Esperado**:
- Script conecta e detecta REC já ativo
- Mostra: "🎥 REC INICIADO | HH:MM:SS:FF" (com TC sincronizado)
- Timecode continua de onde a ATEM estava (não reinicia em 00:00:00:00)
- Próximas atualizações mostram: "🔴 GRAVANDO | REC TIME: HH:MM:SS:FF"
- Timecode incrementa corretamente a partir do ponto sincronizado

**Status**: ✅ Passou / ❌ Falhou

---

### Teste 5: Múltiplos Ciclos REC

**Objetivo**: Verificar se o script funciona corretamente em múltiplos ciclos de gravação.

**Passos**:
1. Execute a GUI Python
2. Inicie REC na ATEM (deixe gravar por 5-10 segundos)
3. Pare REC (deixe parado por 2-3 segundos)
4. Inicie REC novamente
5. Pare REC novamente
6. Repita 2-3 vezes

**Resultado Esperado**:
- Script detecta cada início e parada corretamente
- Timecode sincroniza corretamente em cada novo ciclo
- Não há erros ou travamentos
- Arquivo `rec-live.txt` é atualizado em cada transição

**Status**: ✅ Passou / ❌ Falhou

---

### Teste 6: Desconexão e Reconexão

**Objetivo**: Verificar se o script reconecta automaticamente após desconexão.

**Passos**:
1. Execute a GUI Python
2. Desconecte a ATEM da rede (ou desligue-a)
3. Observe o terminal por 10-15 segundos
4. Reconecte a ATEM à rede (ou ligue-a)
5. Observe o terminal

**Resultado Esperado**:
- Script detecta desconexão: "❌ Desconectado da ATEM. Tentando reconectar..."
- Terminal mostra: "🔄 Tentando reconectar à ATEM..." a cada 5 segundos
- Quando ATEM volta, script reconecta automaticamente
- Mostra: "✅ Conectado! Sincronizando com o REC..."
- Volta a funcionar normalmente

**Status**: ✅ Passou / ❌ Falhou

---

### Teste 7: FPS Customizado

**Objetivo**: Verificar se o script funciona corretamente com diferentes FPS.

**Passos**:
1. Abra a GUI Python: `cd python-gui && python3 app.py`
2. Selecione 30 FPS no campo de FPS da interface
3. Inicie REC e deixe gravar por 10 segundos
4. Observe o incremento de frames (deve chegar a ~300 frames em 10s com 30 FPS)
5. Repita selecionando 60 FPS na interface
6. Observe o incremento de frames (deve chegar a ~600 frames em 10s com 60 FPS)

**Resultado Esperado**:
- Com 30 FPS: frames incrementam até 29, depois resetam para 0
- Com 60 FPS: frames incrementam até 59, depois resetam para 0
- Timecode incrementa corretamente em ambos os casos
- Sincronização funciona para ambos os FPS

**Status**: ✅ Passou / ❌ Falhou

---

### Teste 8: Integração com OBS

**Objetivo**: Verificar se o arquivo `rec-live.txt` funciona corretamente no OBS.

**Passos**:
1. Execute a GUI Python
2. No OBS, adicione uma fonte "Text (GDI+)"
3. Marque "Read from file"
4. Selecione o arquivo `rec-live.txt`
5. Inicie REC na ATEM
6. Observe o overlay no OBS

**Resultado Esperado**:
- Overlay no OBS mostra o conteúdo de `rec-live.txt`
- Atualiza em tempo real conforme o script executa
- Mostra "⏺ Aguardando REC na ATEM..." quando não está gravando
- Mostra "🔴 GRAVANDO | REC TIME: HH:MM:SS:FF" quando gravando
- Mostra "⏹ REC PARADO em: HH:MM:SS:FF" quando parado

**Status**: ✅ Passou / ❌ Falhou

---

### Teste 9: Shutdown Gracioso

**Objetivo**: Verificar se o script encerra corretamente.

**Passos**:
1. Execute a GUI Python
2. Deixe rodando por alguns segundos
3. Pressione Ctrl+C no terminal

**Resultado Esperado**:
- Cursor reaparece no terminal
- Mensagem: "⏹ Encerrado."
- Script encerra sem erros
- Nenhum processo fica rodando em background

**Status**: ✅ Passou / ❌ Falhou

---

## Checklist de Validação

- [ ] Teste 1: Inicialização Sem REC Ativo
- [ ] Teste 2: Iniciar REC Após Script Rodando
- [ ] Teste 3: Parar REC
- [ ] Teste 4: Sincronização Durante Gravação
- [ ] Teste 5: Múltiplos Ciclos REC
- [ ] Teste 6: Desconexão e Reconexão
- [ ] Teste 7: FPS Customizado
- [ ] Teste 8: Integração com OBS
- [ ] Teste 9: Shutdown Gracioso

## Notas de Teste

Espaço para anotações durante os testes:

```
[Adicione suas observações aqui]
```

## Problemas Encontrados

Se encontrar algum problema, descreva:

1. **Descrição**: O que aconteceu?
2. **Passos para Reproduzir**: Como reproduzir o problema?
3. **Resultado Esperado**: O que deveria ter acontecido?
4. **Resultado Obtido**: O que realmente aconteceu?
5. **Logs**: Copie qualquer mensagem de erro do terminal

```
[Adicione problemas encontrados aqui]
```

## Performance

Teste a performance do script:

- **Uso de CPU**: Verifique com `top` ou Activity Monitor
- **Uso de Memória**: Verifique com `top` ou Activity Monitor
- **Tempo de Resposta**: Meça o tempo entre REC start/stop e detecção
- **Latência de Atualização**: Verifique se o OBS atualiza suavemente

## Conclusão

Todos os testes passaram? ✅ SIM / ❌ NÃO

Se sim, o software está pronto para produção!
Se não, revise os problemas encontrados e repita os testes.

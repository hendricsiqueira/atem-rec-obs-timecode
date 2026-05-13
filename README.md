# ATEM REC Timecode -> OBS (TXT de 1 linha)

Este pacote conecta na sua **Blackmagic ATEM Mini Extreme ISO**, mostra o **timecode de REC** no Terminal e atualiza um arquivo **`rec-live.txt`** com **apenas 1 linha** (perfeito para usar no OBS via **Text (GDI+) / Read from file**).

## ✨ Versão Melhorada

A versão atual inclui as seguintes melhorias:

- ✅ **Monitoramento contínuo**: Fica ouvindo mesmo sem REC ativo
- ✅ **Sincronização automática**: Se iniciado durante uma gravação, sincroniza com o TC atual
- ✅ **Detecção rápida**: Para de gravar assim que o REC é interrompido (~500ms)
- ✅ **Reconexão automática**: Tenta reconectar automaticamente se a ATEM desconectar
- ✅ **Melhor tratamento de erros**: Listeners para desconexão e erros

## Versão Python com GUI para macOS

Além do script original em Node.js, este repositório agora inclui uma nova interface desktop em **Python/PySide6**, preparada para uso em **macOS 26 com Apple Silicon**. Ela fica na pasta [`python-gui`](./python-gui/) e permite configurar o IP da ATEM, FPS, arquivo TXT do OBS, status de conexão, status de REC e logs pela interface gráfica.

A GUI agora usa comunicação ATEM **nativa em Python** com `pyatem`, portanto **não precisa de Node.js** para instalar, executar ou gerar o `.app`.

Para instalar todas as bibliotecas necessárias e testar a GUI no macOS ou Linux, usando o Python direto do sistema, primeiro tente:

```bash
cd python-gui
python3 -m pip install -r requirements.txt
python3 app.py
```

Se o Python do seu Mac foi instalado pelo Homebrew e aparecer o erro `externally-managed-environment`, use a instalação no espaço do usuário:

```bash
cd python-gui
python3 -m pip install --user --break-system-packages -r requirements.txt
python3 app.py
```

No Windows, o mesmo fluxo normalmente fica assim:

```powershell
cd python-gui
py -m pip install -r requirements.txt
py app.py
```

Se preferir usar os atalhos via npm, eles continuam disponíveis apenas como conveniência de desenvolvimento:

```bash
cd python-gui
npm run setup
npm run start
```

A documentação completa da versão com GUI está em [`python-gui/README.md`](./python-gui/README.md).
## Requisitos
- Para o script original: macOS + Node.js LTS recomendado
- Para a GUI Python: macOS, Linux ou Windows + Python 3.11 ou superior, sem Node.js obrigatório
- ATEM e computador na mesma rede

## Instalação
Para usar a **GUI Python**, entre na pasta `python-gui` e instale as dependências Python:

```bash
cd python-gui
python3 -m pip install --user --break-system-packages -r requirements.txt
python3 app.py
```

A parte em Node.js é mantida apenas como implementação legada do script original. Para o aplicativo com interface gráfica, **não há Node.js obrigatório**.

## Configuração
Abra o arquivo **`atem-rec-clock.js`** e ajuste o IP da ATEM nesta linha:

```js
const ATEM_IP = '192.168.2.157'
```

> O FPS padrão está em **60**. Você pode passar outro FPS como argumento (ex: `30`).

### Ajustes Avançados (Opcional)

Se necessário, você pode ajustar os seguintes parâmetros no topo do arquivo:

```js
const DEBOUNCE_MS = 500              // Tempo para detectar parada (padrão: 500ms)
const RECONNECT_INTERVAL_MS = 5000   // Intervalo de reconexão (padrão: 5s)
const UPDATE_INTERVAL_MS = 100       // Intervalo de atualização (padrão: 100ms)
```

## Como rodar

### Padrão (60 fps)
```bash
npm start
# ou
node atem-rec-clock.js
```

### Forçando FPS
```bash
node atem-rec-clock.js 60
node atem-rec-clock.js 30
```

## Arquivo gerado
O arquivo **`rec-live.txt`** é criado/atualizado na mesma pasta do script e contém sempre **uma única linha**, por exemplo:

- Aguardando REC:
```
⏺ Aguardando REC na ATEM...
```

- REC Detectado (aguardando TC):
```
🔴 REC DETECTADO, aguardando TC...
```

- Gravando:
```
🔴 GRAVANDO | REC TIME: 00:09:00:48
```

- Parado:
```
⏹ REC PARADO em: 00:10:32:15
```

A escrita é feita de forma **atômica** (`.tmp` + rename) para o OBS não ler o arquivo "pela metade".

## Configurar no OBS
1. Adicione uma fonte **Text (GDI+)** (ou "Texto").
2. Marque **Read from file / Ler de arquivo**.
3. Selecione o arquivo **`rec-live.txt`** dentro desta pasta.

Pronto: o overlay vai atualizar automaticamente.

## Dica
Se o texto estiver atualizando rápido demais no OBS, aumente:

```js
const UPDATE_INTERVAL_MS = 100
```

para `200` ou `250`.

Se quiser que o sistema detecte a parada de REC mais rápido ou mais lento, ajuste:

```js
const DEBOUNCE_MS = 500  // Aumentar para 1000 se quiser mais tolerância
```

## Fluxo de Funcionamento

1. **Inicialização**: Script conecta à ATEM e começa a monitorar
2. **Aguardando**: Mostra "Aguardando REC na ATEM..." enquanto não há gravação
3. **REC Iniciado**: Detecta o início da gravação e sincroniza com o TC
4. **Gravando**: Mostra o timecode em tempo real, sincronizado com a ATEM
5. **REC Parado**: Detecta a parada e congela o último timecode
6. **Reconexão**: Se desconectar, tenta reconectar automaticamente a cada 5 segundos

## Troubleshooting

### "Conectando à ATEM..." mas não conecta
- Verifique se o IP da ATEM está correto
- Certifique-se de que a ATEM e o Mac estão na mesma rede
- Teste a conectividade com: `ping 192.168.2.157`

### O timecode não atualiza
- Verifique se a ATEM está gravando (REC ativo)
- Confirme que o FPS está correto
- Tente aumentar o `UPDATE_INTERVAL_MS` se houver lag

### O arquivo `rec-live.txt` não é criado
- Verifique as permissões da pasta
- Tente rodar com `sudo` se necessário

# ATEM REC OBS Timecode — GUI Python para macOS

Esta pasta contém uma nova versão desktop do projeto **ATEM REC OBS Timecode**, criada em **Python com PySide6** e pensada para uso em **macOS 26 com processador Apple Silicon**. O objetivo é oferecer uma interface gráfica simples para configurar o IP da ATEM, selecionar o FPS, escolher o arquivo TXT lido pelo OBS e acompanhar o estado de gravação em tempo real.

A aplicação mantém o mesmo fluxo do projeto original: ela monitora o estado de REC da ATEM, calcula o timecode localmente a partir do timecode recebido e grava um arquivo `rec-live.txt` com **uma única linha**, adequado para a fonte de texto do OBS configurada com leitura de arquivo.

## Arquitetura

A interface é escrita em Python/PySide6. Para a comunicação ATEM, esta primeira versão usa um helper local em Node.js baseado em `atem-connection`, a mesma biblioteca já usada pelo projeto original. Essa decisão preserva compatibilidade com o estado `recording.status.state` e `recording.duration` que o projeto atual já utiliza com sucesso.

| Camada | Tecnologia | Função |
|---|---:|---|
| GUI | Python + PySide6 | Interface desktop, configuração, status, logs e escolha do TXT do OBS. |
| Backend local | Node.js + `atem-connection` | Conexão com a ATEM, leitura de REC/timecode e escrita atômica do TXT. |
| Integração OBS | Arquivo `.txt` | Fonte de texto do OBS em modo **Read from file / Ler de arquivo**. |

> Esta é uma aplicação Python com GUI, mas ainda usa um helper local Node.js para a camada de protocolo ATEM porque a biblioteca Python avaliada não expõe, de forma equivalente e confirmada, os campos de gravação/timecode usados pelo projeto atual.

## Requisitos no macOS 26 Apple Silicon

Antes de executar, instale os seguintes componentes no Mac:

| Requisito | Versão recomendada | Observação |
|---|---:|---|
| Python | 3.11 ou superior | Preferencialmente versão ARM64 nativa para Apple Silicon. |
| Node.js | LTS | Necessário para o helper `atem-connection`. |
| OBS | Atual | Para ler o arquivo TXT como fonte de texto. |
| ATEM e Mac | mesma rede | O IP configurado precisa apontar para a ATEM. |

## Instalação para desenvolvimento/uso local

Dentro da pasta `python-gui`, execute:

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
npm install
python3 app.py
```

Se preferir não usar ambiente virtual, é possível instalar diretamente no Python do sistema, mas o ambiente virtual é recomendado para evitar conflitos.

## Uso

Ao abrir a aplicação, informe o **IP da ATEM**, selecione o **FPS** usado na gravação e escolha o arquivo TXT que será lido pelo OBS. Depois, clique em **Conectar e iniciar**. A janela mostrará o status de conexão, o estado de REC e uma prévia exata do texto enviado ao arquivo.

No OBS, adicione uma fonte de texto e habilite **Read from file / Ler de arquivo**. Selecione o TXT configurado na aplicação. O conteúdo será atualizado automaticamente enquanto a ATEM estiver gravando.

## Mensagens geradas

| Estado | Texto enviado ao OBS |
|---|---|
| Aguardando REC | `⏺ Aguardando REC na ATEM...` |
| REC detectado sem TC | `🔴 REC DETECTADO, aguardando TC...` |
| REC iniciado | `🎥 REC INICIADO \| 00:00:00:00` |
| Gravando | `🔴 GRAVANDO \| REC TIME: 00:09:00:48` |
| REC parado | `⏹ REC PARADO em: 00:10:32:15` |

## Gerar `.app` no macOS

No Mac, execute:

```bash
cd python-gui
chmod +x scripts/build_macos_app.sh
./scripts/build_macos_app.sh
```

Ao final, o aplicativo será criado em:

```text
dist/ATEM REC OBS Timecode.app
```

Nesta primeira versão, o `.app` empacota a GUI Python e inclui o helper JavaScript como recurso interno, mas ainda exige que o **Node.js LTS** esteja instalado no macOS. Um próximo refinamento pode embutir o binário Node ARM64 dentro do `.app`, eliminando essa dependência externa para distribuição.

## Troubleshooting

| Problema | Causa provável | Solução |
|---|---|---|
| “Node.js não encontrado” | Node.js não está instalado ou não está no `PATH`. | Instale Node.js LTS para macOS ARM64 e reabra o app/Terminal. |
| “Dependências Node ausentes” | `npm install` não foi executado em `python-gui`. | Execute `npm install` nessa pasta. |
| Não conecta na ATEM | IP incorreto ou redes diferentes. | Confirme o IP no ATEM Software Control e teste `ping IP_DA_ATEM`. |
| OBS não atualiza | Fonte de texto não está lendo o arquivo correto. | Verifique se o OBS aponta para o mesmo TXT selecionado na aplicação. |
| Timecode em velocidade errada | FPS configurado diferente da gravação. | Ajuste o FPS na interface para 30, 60 ou o valor usado no projeto. |

## Próximos passos recomendados

Os próximos refinamentos naturais são criar um ícone `.icns`, embutir Node.js ARM64 no `.app`, adicionar assinatura/notarização para distribuição fora do seu Mac e, se necessário, pesquisar/implementar uma camada ATEM totalmente nativa em Python para remover o helper Node.js.

# ATEM REC OBS Timecode — GUI Python

Esta pasta contém a versão desktop do projeto **ATEM REC OBS Timecode**, criada em **Python com PySide6** e pensada principalmente para uso em **macOS 26 com processador Apple Silicon**, mas mantendo execução simples também em outros sistemas que tenham Python compatível. O objetivo é oferecer uma interface gráfica simples para configurar o IP da ATEM, selecionar o FPS, escolher o arquivo TXT lido pelo OBS e acompanhar o estado de gravação em tempo real.

A aplicação mantém o mesmo fluxo do projeto original: ela monitora o estado de REC da ATEM, calcula o timecode localmente a partir do timecode recebido e grava um arquivo `rec-live.txt` com **uma única linha**, adequado para a fonte de texto do OBS configurada com leitura de arquivo.

## Arquitetura

A interface é escrita em Python/PySide6 e a comunicação com a ATEM agora é feita de forma **nativa em Python** usando `pyatem`. Portanto, esta versão **não depende de Node.js** para instalar, executar ou gerar o `.app`.

| Camada | Tecnologia | Função |
|---|---:|---|
| GUI | Python + PySide6 | Interface desktop, configuração, status, logs e escolha do TXT do OBS. |
| Backend ATEM | Python + `pyatem` | Conexão com a ATEM, leitura dos campos `recording-status` e `recording-duration`, cálculo de timecode e escrita atômica do TXT. |
| Integração OBS | Arquivo `.txt` | Fonte de texto do OBS em modo **Read from file / Ler de arquivo**. |

> A biblioteca PyATEMMax também foi avaliada. Ela possui uma boa estrutura de conexão/eventos, mas a versão inspecionada não expõe claramente os campos de gravação e duração necessários para este fluxo. Por isso, a implementação nativa usa `pyatem`, que já decodifica `RTMS` como `recording-status` e `RTMR` como `recording-duration`.

## Requisitos

Antes de executar pelo código-fonte, instale os seguintes componentes no computador:

| Requisito | Versão recomendada | Observação |
|---|---:|---|
| Python | 3.11 ou superior | No macOS Apple Silicon, preferencialmente versão ARM64 nativa. No Windows, use o instalador oficial do Python e o comando `py`. |
| OBS | Atual | Para ler o arquivo TXT como fonte de texto. |
| ATEM e computador | mesma rede | O IP configurado precisa apontar para a ATEM. |

## Instalação para desenvolvimento/uso local

A instalação agora segue o fluxo mais direto possível: **usar o Python do sistema**, instalar as bibliotecas nele e abrir a aplicação com `python3 app.py`. Nenhum ambiente virtual `.venv` é criado ou exigido.

No macOS ou Linux, dentro da pasta `python-gui`, primeiro tente o comando normal:

```bash
python3 -m pip install -r requirements.txt
python3 app.py
```

Em muitos Macs com Python instalado pelo Homebrew, o `pip` pode mostrar o erro `externally-managed-environment`. Isso é uma proteção do Homebrew/PEP 668 para evitar instalação global acidental dentro do Python gerenciado pelo sistema. Nesse caso, use o comando abaixo, que instala as bibliotecas no espaço do seu usuário e não cria `.venv`:

```bash
python3 -m pip install --user --break-system-packages -r requirements.txt
python3 app.py
```

Se preferir instalar informando as bibliotecas manualmente com o Python oficial do macOS, use:

```bash
python3 -m pip install --user PySide6 pyatem pyusb pyinstaller
python3 app.py
```

No Windows, depois de instalar o Python 3.11 ou superior, o comando normalmente fica assim dentro da pasta `python-gui`:

```powershell
py -m pip install PySide6 pyatem pyusb pyinstaller
py app.py
```

Também existe um instalador de conveniência para macOS/Linux:

```bash
./scripts/install_all.sh
```

Esse script tenta a instalação normal e, se o Python do Homebrew bloquear com `externally-managed-environment`, refaz automaticamente a instalação com `--user --break-system-packages`. **Node.js não é necessário** para instalar, executar ou empacotar a GUI Python.

| Sistema | Instalar bibliotecas | Abrir a GUI |
|---|---|---|
| macOS/Linux normal ou Python oficial do macOS | `python3 -m pip install --user -r requirements.txt` | `python3 app.py` |
| macOS com Homebrew bloqueando pip | `python3 -m pip install --user --break-system-packages -r requirements.txt` | `python3 app.py` |
| Windows | `py -m pip install -r requirements.txt` | `py app.py` |

Se você preferir usar os atalhos definidos no `package.json`, também pode executar `npm run setup` e `npm run start`, mas eles são apenas conveniência de desenvolvimento. Eles não significam que o aplicativo dependa de Node.js.

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

O `.app` gerado pelo PyInstaller inclui o Python, PySide6, `pyatem`, PyUSB e as demais bibliotecas Python necessárias. Assim, **quem apenas for rodar o aplicativo final não precisa instalar Python, PySide6, pyatem ou Node.js separadamente**, desde que esteja usando um Mac compatível com o build gerado.

Para Windows, a ideia é a mesma, mas o executável precisa ser gerado em uma máquina Windows. Em outras palavras: o código-fonte pode ser baixado e executado no Windows com `py app.py`, mas o pacote final para operador Windows deve ser criado no próprio Windows usando PyInstaller.

## Troubleshooting

| Problema | Causa provável | Solução |
|---|---|---|
| “Biblioteca pyatem não encontrada” ou `No module named 'usb'` | As dependências ainda não foram instaladas no Python usado para abrir o app. | No macOS/Linux, execute `python3 -m pip install -r requirements.txt`; se aparecer `externally-managed-environment`, use `python3 -m pip install --user --break-system-packages -r requirements.txt`; no Windows, execute `py -m pip install -r requirements.txt`. |
| Não conecta na ATEM | IP incorreto ou redes diferentes. | Confirme o IP no ATEM Software Control e teste `ping IP_DA_ATEM`. |
| OBS não atualiza | Fonte de texto não está lendo o arquivo correto. | Verifique se o OBS aponta para o mesmo TXT selecionado na aplicação. |
| Timecode em velocidade errada | FPS configurado diferente da gravação. | Ajuste o FPS na interface para 30, 60 ou o valor usado no projeto. |
| macOS bloqueia o app | Aplicativo ainda não assinado/notarizado. | Clique com botão direito em **Abrir** na primeira execução ou faça assinatura/notarização para distribuição. |

## Próximos passos recomendados

Os próximos refinamentos naturais são criar um ícone `.icns`, adicionar assinatura/notarização para distribuição fora do seu Mac e testar a leitura de `recording-status`/`recording-duration` em todos os modelos ATEM que serão usados na operação.

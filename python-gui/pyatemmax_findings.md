# Achados sobre PyATEMMax

A documentação inicial da PyATEMMax indica que a biblioteca é Python puro, sem dependências externas, compatível com Windows/Mac/Linux, e permite monitorar/controlar switchers ATEM. O exemplo básico usa `PyATEMMax.ATEMMax()`, `connect(ip)` e `waitForConnection()`.

Na página inicial não há menção explícita a `record`, `recording`, `timecode` ou duração de gravação. A navegação da documentação possui seções de exemplos, métodos, dados e eventos, que ainda precisam ser verificadas.

Em inspeção local do pacote `PyATEMMax` instalado, foram encontrados métodos relacionados a gravação de macro, mas não campos claros de `recording-status`, `recording-duration` ou `timecode` equivalentes aos campos `RTMS`, `RTMR` e `Timecode` necessários para o overlay do OBS.

## Verificação adicional

A página `docs/data/state/` lista `switcher.lastStateChange.timeCode.*`, mas esse campo representa o timecode do último comando/alteração de estado recebido, não necessariamente a duração da gravação do encoder. A mesma página lista apenas `switcher.macro.recordingStatus.*`, que é status de gravação de macro, não gravação de mídia/USB da ATEM Mini Pro/ISO.

No código instalado da PyATEMMax, a busca por comandos `RTMS`, `RTMR`, `RTMD` e `RMSu` não encontrou handlers. Esses comandos são justamente os campos usados por bibliotecas mais recentes para `recording-status`, `recording-duration`, discos de gravação e configurações de gravação. Portanto, a PyATEMMax parece adequada para controle geral da ATEM, mas não cobre diretamente o recurso específico que este projeto precisa: REC real do encoder e duração/timecode da gravação.

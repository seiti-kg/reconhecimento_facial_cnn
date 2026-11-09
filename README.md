# Reconhecimento facial com CNN

Reconhecimento de identidade com CNN treinada por você, classe **Desconhecido** e análise de emoções — pela webcam ou por uma foto. Todo o processamento acontece localmente.

`CNN própria` · `YuNet` · `enet_b2_7` · `Flask` · `OpenCV`

## Documentação

### Começando

- [Instalação e primeira execução](docs/comecando.md) — dependências, coleta de fotos, treino e demo.
- [Interface web](docs/ui.md) — câmera ao vivo, upload, limiar e leitura dos resultados.

### Referência

- [Modelo de identidade](docs/modelo.md) — CNN, alinhamento, classes, limiar e métricas.
- [Emoções](docs/emocao.md) — `enet_b2_7`, classes, validação e limites.
- [Dados e privacidade](docs/dados.md) — coleta, LFW, desconhecidos, `.gitignore` e zips.

### Projeto

- [Desenvolvimento e build](docs/desenvolvimento.md) — estrutura, dependências, verificação, publicação e créditos.

## Fotos e modelo

O repositório é só código. As pastas `dados/` e `modelos/` são ignoradas pelo Git: cada pessoa coleta as próprias fotos e treina a própria CNN. Para usar o modelo treinado do grupo, veja [Dados e privacidade](docs/dados.md).

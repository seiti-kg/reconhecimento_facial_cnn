# Interface web

[← README](../README.md)

A UI web fica em `src/app_demo.py` e usa a mesma CNN de identidade e o mesmo
modelo de emoção da demo OpenCV. Tudo roda em `127.0.0.1`.

## Como abrir

```powershell
python src/app_demo.py
# http://127.0.0.1:5000
```

A UI exige `modelos/modelo_rostos.keras` e `modelos/classes.txt`. Se eles ainda
não existem, rode o notebook; veja [Instalação e primeira execução](comecando.md).

## Modos

### Ao vivo

- Usa `getUserMedia` do navegador; a câmera só abre em `localhost`,
  `127.0.0.1` ou HTTPS.
- O vídeo é desenhado a cada quadro da tela; as caixas são atualizadas quando
  cada análise termina e interpoladas entre análises para não piscar.
- Com um rosto, mostra as três emoções mais prováveis e suaviza as últimas
  8 leituras. Com vários rostos, mostra a principal e usa as caixas numeradas
  `#1`, `#2`, `#3`; os detalhes ficam na leitura ao lado.
- O rodapé técnico mostra resolução do frame analisado, número de rostos,
  latência e análises por segundo (`AN/S`).

### Foto

- Arraste uma imagem ou clique para escolher; aceita JPG, PNG, WEBP e BMP até
  32 MB.
- A orientação EXIF de foto de celular é corrigida antes da detecção.
- Um rosto: identidade, confiança, emoção e top-3 na leitura. Vários rostos:
  caixas numeradas e uma seção por rosto.
- Imagem sem rosto: a foto continua visível e a leitura explica o que fazer.

## Identidade e desconhecido

A identidade é a CNN treinada pelo grupo. A classe `Desconhecido` é uma classe
treinada e há um segundo filtro: se a maior probabilidade ficar abaixo de
`CONFIANCA_MINIMA` (0,80), a UI mostra `Desconhecido`, mesmo que a CNN aponte
um nome. A leitura mostra a confiança e, quando existe, o palpite mais próximo.

O modelo e o `classes.txt` precisam ser da mesma execução. Use
`python src/verificar_modelo.py` antes da demo.

## Emoção

A UI usa o `enet_b2_7`: EfficientNet-B2 treinado no AffectNet com 7 expressões
(sem a classe "Desprezo"). O modelo e o motivo da troca estão em
[Emoções](emocao.md).

## Performance

- O frame enviado ao servidor é reduzido para até 960 px no maior lado e JPEG
  0,78; o vídeo local continua na resolução da câmera.
- Só uma requisição fica em voo por vez.
- Em uma máquina comum, uma pessoa fica em torno de 6–8 análises/s; três rostos
  reduzem a taxa.
- Se a máquina estiver lenta, use a demo OpenCV com `--emocao atual` (modelo
  leve) ou reduza a resolução da câmera.

## Demo OpenCV

A alternativa sem navegador é:

```powershell
python src/demo_reconhecimento.py --emocao
```

Ela usa a mesma CNN e o modelo de emoção, com suavização de 10 quadros. A tecla
`Q` encerra.

## Privacidade

As imagens são enviadas apenas para o servidor local em `127.0.0.1` e não são
gravadas. `dados/` e `modelos/` ficam fora do Git. Veja
[Dados e privacidade](dados.md).

## Próximos passos

- [Modelo de identidade](modelo.md)
- [Emoções](emocao.md)
- [Dados e privacidade](dados.md)

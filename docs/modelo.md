# Modelo de identidade

[← README](../README.md)

A identidade é uma CNN treinada no notebook `atividade_cnn_rostos.ipynb`. Cada
pasta em `dados/integrantes/` vira uma classe; `dados/desconhecidos/` e o LFW
formam a classe extra `Desconhecido`.

## Pré-processamento

Toda foto passa pela mesma cadeia usada na captura e na demo:

1. **YuNet** detecta o rosto e devolve 5 pontos (olhos, nariz e cantos da boca).
2. **Alinhamento** por similaridade: o rosto é girado e escalado para os pontos
   caírem no padrão ArcFace 112×112.
3. **Cinza 64×64 + CLAHE**: equalização local de contraste para reduzir a
   diferença de iluminação entre sessões.
4. Normalização para `[0, 1]`.

A CNN recebe `64×64×1`. A arquitetura tem quatro convoluções (32, 64, 128 e 128
filtros), `MaxPooling` entre elas, `Flatten`, uma camada densa de 128 unidades,
`Dropout(0.5)` e uma saída `softmax` com o número de classes. São cerca de 500
mil parâmetros.

## Classes e limiar

- **Integrantes**: uma pasta por pessoa; o nome da pasta é o rótulo.
- **Desconhecido**: pessoas que não são do grupo. O notebook usa o LFW e todas
  as pastas de `dados/desconhecidos/`.
- **Limiar**: `CONFIANCA_MINIMA = 0.80` em `src/config.py`. Abaixo disso, a UI
  e a demo mostram `Desconhecido` mesmo que a CNN aponte um nome.

O limiar troca dois erros: aceitar um estranho como integrante ou rejeitar um
integrante. O notebook avalia os dois lados e permite ajustar o valor.

## Treino e avaliação

- Divisão **70% treino / 30% teste** com `StratifiedGroupKFold`.
- O grupo é o bloco de 20 fotos seguidas da webcam (fotos vizinhas são quase
  iguais) ou a pessoa no LFW (desconhecidos de teste são pessoas nunca vistas).
- Aumento de dados: flip, rotação, translação, zoom, brilho e contraste leves.
- Métricas: matriz de confusão, acurácia, precisão, recall e F1 por classe.

O notebook gera `modelos/modelo_rostos.keras` e `modelos/classes.txt`. Os dois
arquivos precisam ser da mesma execução; o nome interno do modelo é conferido
pela demo.

## Verificação

```powershell
python src/verificar_modelo.py
```

O script confere:

- se o modelo e o `classes.txt` existem;
- se o nome interno do modelo é o esperado;
- se o número de saídas bate com a lista de classes;
- se o modelo reconhece as fotos locais de cada integrante.

Ele deve terminar com `OK` antes da apresentação. Se as fotos locais não forem
reconhecidas, o modelo pode ser de outra execução ou de outra condição de luz.

## Limitações

- Desconhecidos de outras câmeras (LFW) não ensinam a rede a rejeitar um
  estranho na frente da **sua** webcam. Para melhorar, colete pessoas de fora
  com `--desconhecido` nos mesmos ambientes da demo.
- O modelo aprende o que está nas fotos. Se todos os integrantes foram
  fotografados sorrindo, a identidade pode cair para `Desconhecido` em uma
  expressão muito diferente.
- O limiar é um compromisso; não existe um valor que zere os dois erros.

## Próximos passos

- [Instalação e primeira execução](comecando.md)
- [Interface web](ui.md)
- [Emoções](emocao.md)
- [Dados e privacidade](dados.md)

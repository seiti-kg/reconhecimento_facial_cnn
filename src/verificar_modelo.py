"""Confere se ESTA maquina tem o modelo certo e se ele funciona nas fotos certas.

Rode antes da demo -- especialmente numa maquina que nao e a que treinou:
    python src/verificar_modelo.py

O erro classico e copiar o modelo de uma maquina e o classes.txt de outra (ou de uma
execucao antiga). O modelo devolve numeros por classe; se a lista de nomes nao casar,
todos os nomes saem trocados, sem dar erro nenhum.
"""

import datetime

import numpy as np
from tensorflow import keras

from config import (
    ARQUIVO_CLASSES, ARQUIVO_MODELO, CONFIANCA_MINIMA, IMG_SIZE, NOME_MODELO, PASTA_INTEGRANTES,
)
from deteccao import ler_imagem, preparar_para_cnn

for arquivo in (ARQUIVO_MODELO, ARQUIVO_CLASSES):
    if not arquivo.exists():
        raise SystemExit(
            f"Falta {arquivo}\n"
            "Copie o modelo E o classes.txt JUNTOS (a pasta modelos/ inteira), da mesma "
            "execucao do notebook."
        )

modificado = lambda a: datetime.datetime.fromtimestamp(a.stat().st_mtime)
CLASSES = ARQUIVO_CLASSES.read_text(encoding="utf-8").splitlines()
modelo = keras.models.load_model(ARQUIVO_MODELO)
saida_modelo = modelo.output_shape[-1]

print(f"classes.txt   {modificado(ARQUIVO_CLASSES):%d/%m/%Y %H:%M}  -> {CLASSES}")
print(f"modelo        {modificado(ARQUIVO_MODELO):%d/%m/%Y %H:%M}  -> {saida_modelo} saidas")

if modelo.name != NOME_MODELO:
    raise SystemExit(
        f"\nVERSAO ANTIGA: o modelo se chama '{modelo.name}', esperado '{NOME_MODELO}'.\n"
        "Foi treinado por um notebook antigo (sem alinhamento/CLAHE). Feche a aba do "
        "notebook SEM salvar, abra de novo e rode todas as celulas."
    )

if len(CLASSES) != saida_modelo:
    raise SystemExit(
        f"\nINCONSISTENTE: o modelo tem {saida_modelo} classes e o classes.txt tem "
        f"{len(CLASSES)} nomes.\nSao de execucoes diferentes. Copie os dois arquivos "
        "juntos, da mesma rodada do notebook."
    )

if saida_modelo < 3:
    print(f"\nATENCAO: so {saida_modelo - 1} integrante treinado. Toda pessoa que nao for "
          "essa vai ser forcada no nome dela -- e exatamente o sintoma de 'tudo vira "
          "uma pessoa so'. Retreine com os integrantes que ja tem fotos.")

integrantes = sorted(p for p in PASTA_INTEGRANTES.iterdir() if p.is_dir()) if PASTA_INTEGRANTES.exists() else []

if not integrantes:
    print("\nSem fotos em dados/integrantes/ nesta maquina -- so a checagem dos arquivos foi feita.")
    raise SystemExit(0)

print()
falhou = False
for p in integrantes:
    arquivos = sorted(p.glob("*.jpg"))[:50]
    if not arquivos:
        print(f"  {p.name:12} pasta vazia")
        continue
    X = np.stack([preparar_para_cnn(ler_imagem(a), IMG_SIZE) for a in arquivos])
    probs = modelo(X[..., None], training=False).numpy()
    conf, pred = probs.max(1), probs.argmax(1)
    rotulos = [CLASSES[i] if c >= CONFIANCA_MINIMA else "Desconhecido" for i, c in zip(pred, conf)]
    acertos = rotulos.count(p.name)
    if p.name not in CLASSES:
        print(f"  {p.name:12} NAO esta na lista de classes do classes.txt")
        falhou = True
        continue
    taxa = acertos / len(rotulos)
    print(f"  {p.name:12} {acertos:3}/{len(rotulos)} ({taxa:5.1%}) acertado como o proprio nome")
    if taxa < 0.80:
        falhou = True

print(f"\n{'PROBLEMA' if falhou else 'OK'}: " + (
    "o modelo nao reconhece as fotos desta maquina com folga -- provavelmente e de outra "
    "execucao ou as fotos sao de outra condicao." if falhou else
    "modelo e classes.txt batem e o modelo acerta as fotos locais. Pode apresentar."))

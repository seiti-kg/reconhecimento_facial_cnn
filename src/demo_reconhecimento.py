"""Demonstração ao vivo: webcam -> CNN -> nome do integrante ou "Desconhecido".

Uso (da raiz do projeto):
    python src/demo_reconhecimento.py              (tecla Q encerra)
    python src/demo_reconhecimento.py --camera 1   (segunda webcam)
    python src/demo_reconhecimento.py --emocao     (+ expressão facial, modelo pesado)
    python src/demo_reconhecimento.py --emocao atual  (+ expressão com o modelo leve)

Requer o modelo treinado pelo notebook (modelos/modelo_rostos.keras + modelos/classes.txt).
Com --emocao, usa também um modelo pré-treinado de expressões (src/emocao.py).
"""

import argparse
import unicodedata
from collections import deque

import cv2
import numpy as np
from tensorflow import keras

from config import (
    ARQUIVO_CLASSES, ARQUIVO_MODELO, CONFIANCA_MINIMA, IMG_SIZE, NOME_MODELO, TAMANHO_MINIMO_ROSTO,
)
from deteccao import alinhar, caixa, criar_detector, detectar_rostos, preparar_para_cnn
from emocao import criar_modelo_emocao, detectar_emocao, resumir_emocao

argumentos = argparse.ArgumentParser(description="Demo ao vivo do reconhecimento facial.")
argumentos.add_argument("--camera", type=int, default=0,
                        help="índice da webcam (0 = padrão; 1, 2... para as outras)")
argumentos.add_argument("--emocao", nargs="?", const="pesado", choices=("atual", "pesado"),
                        default=None, metavar="MODELO",
                        help="mostra a expressão facial; MODELO='pesado' (padrão, AffectNet, "
                             "7 classes) ou 'atual' (RAF-DB, 7 classes, mais rápido)")
argumentos = argumentos.parse_args()

JANELA_SUAVIZACAO = 10    # média das últimas N leituras (só com 1 rosto no quadro)


def sem_acentos(texto):
    # as fontes do OpenCV não desenham acentos
    return unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()


if not ARQUIVO_MODELO.exists() or not ARQUIVO_CLASSES.exists():
    raise SystemExit(
        "Modelo de identidade não encontrado em modelos/.\n"
        "Rode o notebook atividade_cnn_rostos.ipynb depois de coletar as fotos "
        "com src/captura_faces.py."
    )

modelo = keras.models.load_model(ARQUIVO_MODELO)
if modelo.name != NOME_MODELO:
    raise SystemExit(
        f"{ARQUIVO_MODELO.name} veio de uma versão antiga do notebook (modelo '{modelo.name}', "
        f"esperado '{NOME_MODELO}').\nFeche a aba do notebook SEM salvar, abra de novo e "
        "rode todas as células."
    )
CLASSES = ARQUIVO_CLASSES.read_text(encoding="utf-8").splitlines()

detector = criar_detector()
modelo_emocao = criar_modelo_emocao(argumentos.emocao) if argumentos.emocao else None
if modelo_emocao is not None:
    print(f"Emoção: modelo {modelo_emocao.nome} "
          f"({len(modelo_emocao.classes)} classes, {modelo_emocao.lado}x{modelo_emocao.lado})")

captura = cv2.VideoCapture(argumentos.camera)
if not captura.isOpened():
    raise SystemExit(
        f"Webcam {argumentos.camera} indisponível: verifique se ela está em uso por outro programa, "
        "ou tente outro índice com --camera 1, 2..."
    )

historico = deque(maxlen=JANELA_SUAVIZACAO)
historico_emocao = deque(maxlen=JANELA_SUAVIZACAO)

while True:
    ok, frame = captura.read()
    if not ok:
        break

    rostos = detectar_rostos(detector, frame, TAMANHO_MINIMO_ROSTO)

    if len(rostos) > 0:
        # mesmo alinhamento + pré-processamento das fotos de treino (deteccao.py)
        entradas = np.stack([preparar_para_cnn(alinhar(frame, r), IMG_SIZE) for r in rostos])
        # chamada direta, não predict(): o predict() do Keras paga ~110 ms de
        # overhead por chamada e derrubava a demo para ~9 fps
        probabilidades = modelo(entradas[..., None], training=False).numpy()

        # média das últimas leituras mata o piscar de rótulo entre quadros; com mais
        # de um rosto no quadro não há como casar as leituras, então vai sem suavizar
        if len(rostos) == 1:
            historico.append(probabilidades[0])
            probabilidades = np.mean(historico, axis=0, keepdims=True)
        else:
            historico.clear()

        # emoção calculada antes de desenhar: o recorte sai do quadro limpo
        emocoes = (
            [detectar_emocao(modelo_emocao, frame, r) for r in rostos]
            if modelo_emocao is not None else None
        )
        # mesma lógica da identidade: só dá para casar leituras com um rosto no quadro
        if emocoes is not None and len(rostos) == 1:
            historico_emocao.append(emocoes[0][2])
            probabilidades_emocao = [np.mean(historico_emocao, axis=0)]
        else:
            historico_emocao.clear()
            probabilidades_emocao = (
                [emocao[2] for emocao in emocoes] if emocoes is not None else None
            )

        for i, (rosto, probs) in enumerate(zip(rostos, probabilidades)):
            x, y, w, h = caixa(rosto)
            indice = int(np.argmax(probs))
            confianca = float(probs[indice])
            rotulo = CLASSES[indice] if confianca >= CONFIANCA_MINIMA else "Desconhecido"
            cor = (0, 0, 255) if rotulo == "Desconhecido" else (0, 255, 0)
            cv2.rectangle(frame, (x, y), (x + w, y + h), cor, 2)
            cv2.putText(
                frame,
                f"{sem_acentos(rotulo)} {confianca:.0%}",
                (x, y - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                cor,
                2,
            )
            if probabilidades_emocao is not None:
                # com vários rostos as linhas de top-3 se sobrepõem; aí só o mais provável
                quantidade = 3 if len(rostos) == 1 else 1
                principais = resumir_emocao(modelo_emocao, probabilidades_emocao[i], quantidade)
                texto = " | ".join(
                    f"{sem_acentos(nome)} {probabilidade:.0%}"
                    for nome, probabilidade in principais
                )
                posicao = (x, y - 38) if y > 40 else (x, y + h + 22)
                cv2.putText(
                    frame,
                    texto,
                    posicao,
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.5,
                    (0, 255, 255),
                    1,
                )
    else:
        historico.clear()
        historico_emocao.clear()

    cv2.imshow("Reconhecimento (Q para sair)", frame)
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

captura.release()
cv2.destroyAllWindows()

"""Detecção, alinhamento e pré-processamento de rostos, compartilhados por todos
os scripts (captura, demo, galeria, verificação) e pelo notebook.

Detector: YuNet (rede neural do OpenCV, cv2.FaceDetectorYN). O Haar cascade
frontal usado antes só achava rostos praticamente de frente: com ~15 graus de
giro para o lado ou cabeça levemente para cima/baixo o rosto sumia. O YuNet
aguenta giros bem maiores e ainda devolve 5 pontos do rosto (olhos, nariz e
cantos da boca).

Alinhamento: com os 5 pontos, o rosto é girado/escalado para que olhos, nariz e
boca caiam sempre na mesma posição do recorte. Isso tira inclinação e distância
da conta (a CNN não precisa aprender isso) e corta o fundo e quase todo o
cabelo -- o fundo do quarto onde as fotos foram tiradas era uma pista falsa de
"integrante" para a rede.

Todo recorte, de qualquer origem, TEM que passar por alinhar() e
preparar_para_cnn(): treino e demo precisam ver exatamente o mesmo tipo de imagem.
"""

import re
import urllib.request

import cv2
import numpy as np

from config import ARQUIVO_YUNET

URL_YUNET = (
    "https://github.com/opencv/opencv_zoo/raw/main/models/"
    "face_detection_yunet/face_detection_yunet_2023mar.onnx"
)
CONFIANCA_DETECCAO = 0.8    # o padrão do YuNet (0.9) perde rosto virado
TAMANHO_RECORTE = 112       # lado do recorte alinhado salvo em disco

# olho direito, olho esquerdo, nariz e cantos da boca num recorte 112x112 (padrão
# ArcFace) -- a mesma ordem dos pontos devolvidos pelo YuNet
ARCFACE = np.array(
    [
        [38.2946, 51.6963],
        [73.5318, 51.5014],
        [56.0252, 71.7366],
        [41.5493, 92.3655],
        [70.7299, 92.2041],
    ],
    dtype=np.float32,
)
# o padrão ArcFace vai além da caixa do Haar das fotos antigas e o realinhamento
# delas ficaria com faixas sem imagem; ampliado 30% e com os
# olhos mais para cima, o recorte cabe dentro da caixa antiga
REFERENCIA = (
    ((ARCFACE - ARCFACE[:2].mean(axis=0)) * 1.3 + [56, 33]) * (TAMANHO_RECORTE / 112)
).astype(np.float32)
# o modelo de expressões (opencv_zoo) foi treinado no ArcFace puro, sem o zoom de
# 1.3 usado na identidade; cada modelo recebe o recorte que espera
REFERENCIA_EMOCAO = (ARCFACE * (TAMANHO_RECORTE / 112)).astype(np.float32)

_clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(4, 4))


def ler_imagem(caminho):
    # cv2.imread não abre caminho com acento no Windows
    return cv2.imdecode(np.fromfile(str(caminho), np.uint8), cv2.IMREAD_COLOR)


def salvar_recorte(pasta, recorte):
    """Grava o recorte como pasta/img_XXXX.jpg, sem sobrescrever nenhuma foto."""
    # max + 1, não contagem + 1: o realinhamento antigo descartou fotos e deixou
    # buracos na numeração, e contagem + 1 sobrescreveria uma foto existente
    numeros = [int(m.group(1)) for a in pasta.glob("img_*.jpg")
               if (m := re.fullmatch(r"img_(\d+)\.jpg", a.name))]
    pasta.mkdir(parents=True, exist_ok=True)
    caminho = pasta / f"img_{max(numeros, default=0) + 1:04d}.jpg"
    # imencode + tofile: o cv2.imwrite falha calado com acento no caminho (Windows)
    cv2.imencode(".jpg", recorte)[1].tofile(str(caminho))
    return caminho


def criar_detector():
    if not ARQUIVO_YUNET.exists():
        print(f"Baixando o detector YuNet para {ARQUIVO_YUNET} ...")
        ARQUIVO_YUNET.parent.mkdir(parents=True, exist_ok=True)
        urllib.request.urlretrieve(URL_YUNET, ARQUIVO_YUNET)
    return cv2.FaceDetectorYN.create(
        str(ARQUIVO_YUNET), "", (320, 320), score_threshold=CONFIANCA_DETECCAO
    )


def detectar_rostos(detector, imagem_bgr, tamanho_minimo=60):
    """Devolve uma linha por rosto: [x, y, w, h, 10 coordenadas dos pontos, score]."""
    altura, largura = imagem_bgr.shape[:2]
    detector.setInputSize((largura, altura))
    _, rostos = detector.detect(imagem_bgr)
    if rostos is None:
        return []
    return [r for r in rostos if min(r[2], r[3]) >= tamanho_minimo]


def caixa(rosto):
    x, y, w, h = (int(round(v)) for v in rosto[:4])
    return max(x, 0), max(y, 0), w, h


def alinhar(imagem_bgr, rosto, referencia=REFERENCIA, tamanho=TAMANHO_RECORTE):
    """Recorta o rosto alinhado; `tamanho` existe para modelos que pedem mais que 112."""
    pontos = rosto[4:14].reshape(5, 2).astype(np.float32)
    matriz, _ = cv2.estimateAffinePartial2D(pontos, referencia, method=cv2.LMEDS)
    return cv2.warpAffine(
        imagem_bgr, matriz, (tamanho, tamanho),
        borderMode=cv2.BORDER_REPLICATE,
    )


def preparar_para_cnn(recorte, tamanho):
    """Recorte alinhado (BGR ou cinza, qualquer lado) -> matriz float32 [0, 1]."""
    if recorte.ndim == 3:
        recorte = cv2.cvtColor(recorte, cv2.COLOR_BGR2GRAY)
    recorte = cv2.resize(recorte, (tamanho, tamanho), interpolation=cv2.INTER_AREA)
    # equalização local: a mesma pessoa com luz de lado, de cima ou mais fraca fica
    # parecida; sem isto a iluminação da sessão de coleta vira pista de identidade
    return _clahe.apply(recorte).astype(np.float32) / 255.0

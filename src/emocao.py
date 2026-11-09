"""Expressão facial com modelos pré-treinados (OpenCV Zoo e EmotiEffLib).

O professor liberou modelo pronto apenas para o sentimento; a identidade
continua sendo a CNN treinada pelo grupo no notebook. Este módulo é isolado:
nada aqui é usado pelo treino nem pela classificação de quem é a pessoa.

    python src/demo_reconhecimento.py --emocao          # modelo pesado (padrão)
    python src/demo_reconhecimento.py --emocao atual    # modelo leve

Modelos:
- "atual": OpenCV Zoo, MobileFaceNet treinado no RAF-DB (7 expressões, 88,27%),
  112x112 alinhado no padrão ArcFace, RGB normalizado para [-1, 1]; ~3 ms/rosto.
- "pesado": EmotiEffLib enet_b2_7 (EfficientNet-B2) treinado no AffectNet
  (7 expressões, 66,34% no AffectNet), 260x260 RGB com média/desvio do ImageNet;
  ~35 ms/rosto. Sem a classe "Desprezo": o sorriso não é mais roubado por ela.

Procedência:
- OpenCV Zoo, "Progressive Teacher" com backbone MobileFaceNet, Apache 2.0.
- EmotiEffLib (sb-ai-lab), modelos AffectNet, Apache 2.0.
"""

from __future__ import annotations

import urllib.request
from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np

from config import ARQUIVO_EMOCAO, ARQUIVO_EMOCAO_PESADA
from deteccao import ARCFACE, REFERENCIA_EMOCAO, alinhar

URL_EMOCAO = (
    "https://github.com/opencv/opencv_zoo/raw/main/models/"
    "facial_expression_recognition/"
    "facial_expression_recognition_mobilefacenet_2022july.onnx"
)
URL_EMOCAO_PESADA = (
    "https://github.com/sb-ai-lab/EmotiEffLib/raw/main/models/"
    "affectnet_emotions/onnx/enet_b2_7.onnx"
)

# mesma ordem da saída de cada modelo
EMOCOES_ATUAL = ("Bravo", "Nojo", "Medo", "Alegre", "Neutro", "Triste", "Surpreso")
EMOCOES_PESADO = ("Bravo", "Nojo", "Medo", "Alegre", "Neutro", "Triste", "Surpreso")

# o enet_b2_7 foi treinado com rostos 260x260; alinhar direto nesse tamanho
# preserva mais detalhe do que ampliar o recorte 112 usado pelo modelo leve
LADO_PESADO = 260
REFERENCIA_PESADO = (ARCFACE * (LADO_PESADO / 112)).astype(np.float32)
MEDIA_IMAGENET = np.array([0.485, 0.456, 0.406], dtype=np.float32)
DESVIO_IMAGENET = np.array([0.229, 0.224, 0.225], dtype=np.float32)

ESPECIFICACOES = {
    "atual": (ARQUIVO_EMOCAO, URL_EMOCAO, EMOCOES_ATUAL, 112),
    "pesado": (ARQUIVO_EMOCAO_PESADA, URL_EMOCAO_PESADA, EMOCOES_PESADO, LADO_PESADO),
}


@dataclass(frozen=True)
class ModeloEmocao:
    nome: str
    rede: cv2.dnn.Net
    classes: tuple[str, ...]
    lado: int
    caminho: Path


def criar_modelo_emocao(nome: str = "pesado") -> ModeloEmocao:
    """Carrega o modelo pedido, baixando o ONNX se ele ainda não estiver em modelos/."""
    if nome not in ESPECIFICACOES:
        raise ValueError(f"modelo de emoção desconhecido: {nome!r}")
    caminho, url, classes, lado = ESPECIFICACOES[nome]
    if not caminho.exists():
        print(f"Baixando o modelo de expressões para {caminho} ...")
        caminho.parent.mkdir(parents=True, exist_ok=True)
        urllib.request.urlretrieve(url, caminho)
    return ModeloEmocao(nome, cv2.dnn.readNet(str(caminho)), classes, lado, caminho)


def _softmax(logits: np.ndarray) -> np.ndarray:
    exp = np.exp(logits - logits.max())
    return exp / exp.sum()


def _probabilidades(modelo: ModeloEmocao, imagem_bgr: np.ndarray, rosto: np.ndarray):
    """Probabilidades das expressões para um rosto devolvido pelo YuNet."""
    if modelo.nome == "atual":
        recorte = alinhar(imagem_bgr, rosto, REFERENCIA_EMOCAO)
        # x/255 -> (x/255 - 0.5) / 0.5 = x/127.5 - 1, trocando BGR por RGB
        blob = cv2.dnn.blobFromImage(
            recorte, 1 / 127.5, (112, 112), (127.5, 127.5, 127.5), swapRB=True
        )
        modelo.rede.setInput(blob, "data")
        logits = modelo.rede.forward(["label"])[0][0]
    else:
        recorte = alinhar(imagem_bgr, rosto, REFERENCIA_PESADO, modelo.lado)
        rgb = cv2.cvtColor(recorte, cv2.COLOR_BGR2RGB).astype(np.float32) / 255.0
        normalizado = (rgb - MEDIA_IMAGENET) / DESVIO_IMAGENET
        blob = normalizado.transpose(2, 0, 1)[np.newaxis].astype(np.float32)
        modelo.rede.setInput(blob)
        logits = modelo.rede.forward(["output"])[0][0]
    return _softmax(logits)


def detectar_emocao(modelo: ModeloEmocao, imagem_bgr: np.ndarray, rosto: np.ndarray):
    """Devolve (expressão, confiança, probabilidades) para um rosto do YuNet."""
    probabilidades = _probabilidades(modelo, imagem_bgr, rosto)
    indice = int(np.argmax(probabilidades))
    return modelo.classes[indice], float(probabilidades[indice]), probabilidades


def resumir_emocao(modelo: ModeloEmocao, probabilidades: np.ndarray, quantidade: int = 3):
    """As `quantidade` expressões mais prováveis, em ordem decrescente."""
    indices = np.argsort(probabilidades)[::-1][:quantidade]
    return [(modelo.classes[int(i)], float(probabilidades[int(i)])) for i in indices]

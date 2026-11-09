"""UI local da demo: câmera ao vivo + upload de foto.

    python src/app_demo.py
    abra http://127.0.0.1:5000

A identidade usa a CNN treinada pelo grupo; a emoção usa o enet_b2_7
(EmotiEffLib / AffectNet). O navegador envia quadros ou uma foto para
127.0.0.1 e desenha as caixas localmente; nada é gravado.
"""

from __future__ import annotations

import io
import threading
import time

import cv2
import numpy as np
from flask import Flask, jsonify, render_template, request
from PIL import Image, ImageOps
from tensorflow import keras

from config import (
    ARQUIVO_CLASSES,
    ARQUIVO_MODELO,
    CONFIANCA_MINIMA,
    IMG_SIZE,
    NOME_MODELO,
    TAMANHO_MINIMO_ROSTO,
)
from deteccao import alinhar, caixa, criar_detector, detectar_rostos, preparar_para_cnn
from emocao import criar_modelo_emocao, detectar_emocao

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 32 * 1024 * 1024   # 32 MB
app.json.sort_keys = False

LADO_MAXIMO = 1400
LIMITE_ANALISE = threading.Lock()

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
        f"esperado '{NOME_MODELO}'). Rode todas as células do notebook novamente."
    )
CLASSES = ARQUIVO_CLASSES.read_text(encoding="utf-8").splitlines()
if len(CLASSES) != modelo.output_shape[-1]:
    raise SystemExit(
        f"{ARQUIVO_MODELO.name} tem {modelo.output_shape[-1]} saídas e "
        f"{ARQUIVO_CLASSES.name} tem {len(CLASSES)} nomes. Copie os dois da mesma execução."
    )
detector = criar_detector()
modelo_emocao = criar_modelo_emocao("pesado")


def limitar(imagem: np.ndarray) -> np.ndarray:
    """Reduz o maior lado para no máximo 1400 px (fotos de celular)."""
    altura, largura = imagem.shape[:2]
    lado = max(altura, largura)
    if lado > LADO_MAXIMO:
        escala = LADO_MAXIMO / lado
        return cv2.resize(
            imagem,
            (int(largura * escala), int(altura * escala)),
            interpolation=cv2.INTER_AREA,
        )
    return imagem


def ler_upload(arquivo) -> np.ndarray:
    dados = arquivo.read()
    try:
        imagem = Image.open(io.BytesIO(dados))
        imagem = ImageOps.exif_transpose(imagem).convert("RGB")
    except Exception as exc:
        raise ValueError("Não foi possível ler a imagem. Use JPG, PNG ou WEBP.") from exc
    return cv2.cvtColor(np.array(imagem), cv2.COLOR_RGB2BGR)


def analisar(imagem_bgr: np.ndarray) -> dict:
    """Detecta rostos, identidade e emoção; devolve dados para o cliente desenhar."""
    inicio = time.perf_counter()
    imagem = limitar(imagem_bgr)
    altura, largura = imagem.shape[:2]

    with LIMITE_ANALISE:
        rostos = detectar_rostos(detector, imagem, TAMANHO_MINIMO_ROSTO)

        if not rostos:
            return {
                "largura": largura,
                "altura": altura,
                "tempo_ms": round((time.perf_counter() - inicio) * 1000, 1),
                "rostos": [],
            }

        entradas = np.stack(
            [preparar_para_cnn(alinhar(imagem, rosto), IMG_SIZE) for rosto in rostos]
        )
        probabilidades = modelo(entradas[..., None], training=False).numpy()
        emocoes = [detectar_emocao(modelo_emocao, imagem, rosto) for rosto in rostos]

    resultados = []
    for rosto, probs, emocao in zip(rostos, probabilidades, emocoes):
        indice = int(np.argmax(probs))
        palpite = CLASSES[indice]
        confianca = float(probs[indice])
        desconhecido = confianca < CONFIANCA_MINIMA or palpite == "Desconhecido"
        nome = "Desconhecido" if desconhecido else palpite

        nome_emocao, confianca_emocao, probs_emocao = emocao
        resultados.append({
            "caixa": list(caixa(rosto)),
            "identidade": {
                "nome": nome,
                "palpite": palpite,
                "confianca": round(confianca, 4),
                "desconhecido": desconhecido,
                "probabilidades": {
                    classe: round(float(probabilidade), 4)
                    for classe, probabilidade in zip(CLASSES, probs)
                },
            },
            "emocao": {
                "nome": nome_emocao,
                "confianca": round(float(confianca_emocao), 4),
                "probabilidades": {
                    classe: round(float(probabilidade), 4)
                    for classe, probabilidade in zip(modelo_emocao.classes, probs_emocao)
                },
            },
        })

    return {
        "largura": largura,
        "altura": altura,
        "tempo_ms": round((time.perf_counter() - inicio) * 1000, 1),
        "rostos": resultados,
    }


@app.get("/")
def index():
    config = {
        "classes_identidade": CLASSES,
        "classes_emocao": list(modelo_emocao.classes),
        "limiar": CONFIANCA_MINIMA,
        "modelo_identidade": NOME_MODELO,
        "modelo_emocao": modelo_emocao.caminho.stem,
    }
    return render_template("demo.html", config=config)


@app.post("/api/analisar")
def api_analisar():
    arquivo = request.files.get("foto")
    if arquivo is None or not arquivo.filename:
        return jsonify({"erro": "Envie uma imagem no campo 'foto'."}), 400
    try:
        imagem = ler_upload(arquivo)
    except ValueError as exc:
        return jsonify({"erro": str(exc)}), 400
    except Exception:
        app.logger.exception("Falha ao ler o upload")
        return jsonify({"erro": "Não foi possível ler a imagem."}), 400
    try:
        return jsonify(analisar(imagem))
    except Exception:
        app.logger.exception("Falha ao analisar a imagem")
        return jsonify({"erro": "Falha ao analisar a imagem."}), 500


@app.errorhandler(413)
def imagem_grande(_erro):
    return jsonify({"erro": "A imagem passa de 32 MB."}), 413


if __name__ == "__main__":
    print("Demo em http://127.0.0.1:5000")
    app.run(host="127.0.0.1", port=5000, debug=False, use_reloader=False)

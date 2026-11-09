"""Caminhos e parâmetros compartilhados pelos scripts e pelo notebook.

Os caminhos partem da raiz do projeto (não da pasta onde o comando foi rodado),
então qualquer script funciona chamado de qualquer lugar.

    dados/integrantes/<nome>/       uma pasta por integrante = uma classe da CNN
    dados/desconhecidos/<origem>/   gente de fora (lfw, wider, galeria, webcam)
    modelos/                        detector YuNet + CNN treinada + classes.txt
    videos/                         vídeos brutos para o extrair_video.py (opcional)
"""

from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent

PASTA_DADOS = RAIZ / "dados"
PASTA_INTEGRANTES = PASTA_DADOS / "integrantes"
PASTA_DESCONHECIDOS = PASTA_DADOS / "desconhecidos"

PASTA_MODELOS = RAIZ / "modelos"
ARQUIVO_YUNET = PASTA_MODELOS / "face_detection_yunet_2023mar.onnx"
ARQUIVO_MODELO = PASTA_MODELOS / "modelo_rostos.keras"
ARQUIVO_CLASSES = PASTA_MODELOS / "classes.txt"
# modelos pré-treinados só para expressão facial (a identidade é a CNN do notebook)
ARQUIVO_EMOCAO = PASTA_MODELOS / "facial_expression_recognition_mobilefacenet_2022july.onnx"
ARQUIVO_EMOCAO_PESADA = PASTA_MODELOS / "enet_b2_7.onnx"

# o notebook dá este nome ao modelo; a demo recusa modelo com outro nome. Um notebook
# antigo aberto no editor (sem alinhamento/CLAHE) gerava modelo "cnn_rostos", e a demo
# o aceitava calada e marcava todo mundo como Desconhecido
NOME_MODELO = "cnn_rostos_alinhado"

IMG_SIZE = 64               # entrada da CNN: rosto 64x64 em tons de cinza
CONFIANCA_MINIMA = 0.80     # abaixo disso a demo responde "Desconhecido" (ver tabela do notebook)
TAMANHO_MINIMO_ROSTO = 80   # rosto menor que isso (px) é ignorado na captura e na demo

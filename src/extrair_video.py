"""Extrai rostos de um video (celular, webcam gravada) para a base de dados, no MESMO
formato do captura_faces.py (deteccao.py: YuNet + alinhamento).

Como usar (da raiz do projeto):
    python src/extrair_video.py <video> <nome>
    python src/extrair_video.py <video> <nome> --desconhecido

Video e um jeito rapido de juntar variedade: grave ~1 min girando a cabeca devagar
para os lados e para cima/baixo (ate uns 45 graus), aproximando e afastando, e repita
em outros lugares/luzes. Pega 1 quadro a cada INTERVALO_S segundos (quadros vizinhos
sao quase iguais) e so o maior rosto de cada quadro -- quem esta ao fundo nao entra.
"""

import argparse
from pathlib import Path

import cv2

from config import PASTA_DESCONHECIDOS, PASTA_INTEGRANTES, TAMANHO_MINIMO_ROSTO
from deteccao import alinhar, criar_detector, detectar_rostos, salvar_recorte

INTERVALO_S = 0.3   # mesmo ritmo do modo automatico do captura_faces.py
LADO_MAXIMO = 640   # video de celular e bem mais nitido que a webcam (ver recortar_galeria.py)


def main():
    argumentos = argparse.ArgumentParser(description="Extrai rostos de um video.")
    argumentos.add_argument("video", type=Path)
    argumentos.add_argument("nome", help="nome da pessoa (pasta de destino)")
    argumentos.add_argument("--desconhecido", action="store_true",
                            help="pessoa de fora do grupo (classe Desconhecido)")
    argumentos = argumentos.parse_args()

    if not argumentos.video.is_file():
        raise SystemExit(f"Video nao encontrado: {argumentos.video}")
    base = PASTA_DESCONHECIDOS if argumentos.desconhecido else PASTA_INTEGRANTES
    pasta = base / argumentos.nome

    captura = cv2.VideoCapture(str(argumentos.video))
    if not captura.isOpened():
        raise SystemExit(f"O OpenCV nao conseguiu abrir {argumentos.video} (tente converter para .mp4).")
    fps = captura.get(cv2.CAP_PROP_FPS) or 30
    passo = max(1, round(fps * INTERVALO_S))

    detector = criar_detector()

    quadro = salvas = sem_rosto = 0
    while True:
        ok, imagem = captura.read()
        if not ok:
            break
        quadro += 1
        if (quadro - 1) % passo:
            continue

        altura, largura = imagem.shape[:2]
        escala = LADO_MAXIMO / max(altura, largura)
        if escala < 1:
            imagem = cv2.resize(imagem, (int(largura * escala), int(altura * escala)),
                                interpolation=cv2.INTER_AREA)

        rostos = detectar_rostos(detector, imagem, TAMANHO_MINIMO_ROSTO)
        if not rostos:
            sem_rosto += 1
            continue
        salvar_recorte(pasta, alinhar(imagem, max(rostos, key=lambda r: r[2] * r[3])))
        salvas += 1
        print(f"\r{salvas} rostos...", end="")

    captura.release()
    print(f"\n{salvas} rostos salvos em {pasta} "
          f"({sem_rosto} quadros amostrados sem rosto de pelo menos {TAMANHO_MINIMO_ROSTO} px)")


if __name__ == "__main__":
    main()

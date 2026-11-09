"""Transforma fotos comuns (galeria do celular) em recortes de rosto no MESMO
formato do captura_faces.py (deteccao.py: YuNet + alinhamento), prontos para
entrar na pasta de um integrante ou na classe "Desconhecido" do notebook.

Como usar (da raiz do projeto):
    python src/recortar_galeria.py fotos_galeria celular                  # desconhecidos
    python src/recortar_galeria.py fotos_galeria <nome> --integrante      # dados/integrantes/
    (depois: Run All no notebook)

  - fotos_galeria/  pasta com as fotos de origem (jpg, jpeg, png, webp)
  - celular         nome da pasta de saida: dados/desconhecidos/celular/
  - --integrante    grava em dados/integrantes/<nome>/ em vez de desconhecidos

Os recortes nao sobrescrevem nada: continuam a numeracao img_XXXX.jpg da pasta.
Foto com varias pessoas: na classe Desconhecido entra um recorte por rosto; com
--integrante entra so o maior rosto (os outros nao sao aquela pessoa).
"""

import argparse
from pathlib import Path

import cv2

from config import PASTA_DESCONHECIDOS, PASTA_INTEGRANTES, TAMANHO_MINIMO_ROSTO
from deteccao import alinhar, criar_detector, detectar_rostos, ler_imagem, salvar_recorte

LADO_MAXIMO = 640            # mesmo lado de um quadro de webcam (ver nota abaixo)
EXTENSOES = ("*.jpg", "*.jpeg", "*.png", "*.webp")

# Nota sobre LADO_MAXIMO: foto de celular tem 4000 px, webcam tem 640. Reduzir a foto
# antes de detectar faz o recorte sair com a mesma nitidez dos recortes da webcam --
# e e a nitidez que a CNN usa como pista entre "integrante" e "desconhecido".


def main():
    argumentos = argparse.ArgumentParser(description="Recorta rostos de fotos comuns (galeria).")
    argumentos.add_argument("origem", type=Path, help="pasta com as fotos de origem")
    argumentos.add_argument("nome", help="nome da pasta de saida")
    argumentos.add_argument("--integrante", action="store_true",
                            help="grava em dados/integrantes/ em vez de dados/desconhecidos/")
    argumentos = argumentos.parse_args()

    origem = argumentos.origem
    base = PASTA_INTEGRANTES if argumentos.integrante else PASTA_DESCONHECIDOS
    saida = base / argumentos.nome
    if not origem.is_dir():
        raise SystemExit(f"Pasta de fotos nao encontrada: {origem}")
    detector = criar_detector()

    arquivos = sorted(a for ext in EXTENSOES for a in origem.glob(ext))
    if not arquivos:
        raise SystemExit(f"Nenhuma imagem em {origem} ({', '.join(EXTENSOES)}).")

    recortes = 0
    sem_rosto = 0
    for arquivo in arquivos:
        imagem = ler_imagem(arquivo)
        if imagem is None:
            sem_rosto += 1
            continue
        altura, largura = imagem.shape[:2]
        escala = LADO_MAXIMO / max(altura, largura)
        if escala < 1:
            imagem = cv2.resize(imagem, (int(largura * escala), int(altura * escala)))
        rostos = detectar_rostos(detector, imagem, TAMANHO_MINIMO_ROSTO)
        if len(rostos) == 0:
            sem_rosto += 1
            continue
        if argumentos.integrante:
            # so um rosto por foto: numa foto de grupo, os outros entrariam na pasta
            # do integrante com o rotulo errado (extrair_video.py usa o mesmo criterio)
            rostos = [max(rostos, key=lambda r: r[2] * r[3])]
        for rosto in rostos:
            recortes += 1
            salvar_recorte(saida, alinhar(imagem, rosto))
        print(f"\r{recortes} recortes...", end="")

    print(f"\n{recortes} recortes em {saida}")
    print(f"{sem_rosto} de {len(arquivos)} fotos nao renderam recorte (sem rosto detectado)")
    if recortes == 0:
        raise SystemExit("Nenhum rosto detectado -- confira se as fotos tem rosto visivel e de frente.")


if __name__ == "__main__":
    main()

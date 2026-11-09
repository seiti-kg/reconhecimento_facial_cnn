"""Captura de rostos pela webcam para a base de dados da CNN.

Como usar (da raiz do projeto):
    python src/captura_faces.py <nome>                  # dados/integrantes/<nome>/
    python src/captura_faces.py --desconhecido <nome>   # dados/desconhecidos/<nome>/
    python src/captura_faces.py                        # sem nome: lista de exemplo
    python src/captura_faces.py <nome> --camera 1       # segunda webcam

Cada integrante roda o script com o proprio nome (o nome da pasta e o rotulo
da classe no modelo, entao todos precisam usar exatamente o mesmo texto) e
depois manda a pasta dados/integrantes/<nome>/ para quem vai treinar a CNN.
Com --desconhecido, a pessoa (amigo, parente) entra na classe Desconhecido.

  - ESPACO: captura o rosto detectado
  - A: liga/desliga captura automatica (1 foto a cada AUTO_INTERVALO_MS)
  - N: passa para a proxima pessoa (so no modo sem nome)
  - Q: sai

As fotos ficam ja alinhadas (112x112, ver deteccao.py). O canto superior direito
mostra o ultimo recorte salvo.

Dicas de coleta -- variedade vale mais que quantidade:
  - pose: gire a cabeca para os lados e para cima/baixo (ate uns 30 graus), alem
    de frente; no modo automatico, mexa a cabeca devagar o tempo todo
  - luz: colete em pelo menos 2-3 sessoes com luz diferente (janela de dia, luz do
    teto a noite, luminaria de lado, monitor como unica luz)
  - distancia (perto e a ~1 m), expressoes, com e sem oculos
  - desconhecidos: colete tambem gente de fora do grupo com ESTA webcam e NESTES
    ambientes; e isso que ensina a rede que o quarto/a camera nao sao a pessoa
"""

import argparse
import time

import cv2

from config import PASTA_DESCONHECIDOS, PASTA_INTEGRANTES, TAMANHO_MINIMO_ROSTO
from deteccao import alinhar, caixa, criar_detector, detectar_rostos, salvar_recorte

NOMES_EXEMPLO = ["Pessoa1", "Pessoa2", "Pessoa3"]
META_POR_PESSOA = 200
AUTO_INTERVALO_MS = 300      # modo automatico: 1 foto a cada 300 ms (~3/s)
TAMANHO_PREVIEW = 120        # lado do ultimo recorte mostrado na tela


def contar_fotos(pasta):
    return len(list(pasta.glob("*.jpg")))


def main():
    argumentos = argparse.ArgumentParser(description="Captura rostos pela webcam.")
    argumentos.add_argument("nomes", nargs="*", help="nome(s) da(s) pessoa(s)")
    argumentos.add_argument("--desconhecido", action="store_true",
                            help="pessoa de fora do grupo (classe Desconhecido)")
    argumentos.add_argument("--camera", type=int, default=0,
                            help="índice da webcam (0 = padrão; 1, 2... para as outras)")
    argumentos = argumentos.parse_args()

    nomes = argumentos.nomes or NOMES_EXEMPLO
    base = PASTA_DESCONHECIDOS if argumentos.desconhecido else PASTA_INTEGRANTES
    pastas = [base / nome for nome in nomes]

    detector = criar_detector()
    for pasta in pastas:
        pasta.mkdir(parents=True, exist_ok=True)

    print(f"Gravando em: {', '.join(str(pasta) for pasta in pastas)}")

    captura = cv2.VideoCapture(argumentos.camera)
    if not captura.isOpened():
        raise SystemExit(
            f"Webcam {argumentos.camera} indisponivel: verifique se ela esta em uso por outro "
            "programa, ou tente outro indice com --camera 1, 2..."
        )

    indice = 0
    auto = False
    ultima_captura = 0.0
    ultimo_rosto = None
    while True:
        ok, frame = captura.read()
        if not ok:
            break

        rostos = detectar_rostos(detector, frame, TAMANHO_MINIMO_ROSTO)

        # tudo e desenhado numa copia: o recorte sai do frame limpo. O script antigo
        # desenhava no proprio frame e o retangulo/texto iam parar nas fotos
        tela = frame.copy()
        nome, pasta = nomes[indice], pastas[indice]
        n_fotos = contar_fotos(pasta)
        for rosto in rostos:
            x, y, w, h = caixa(rosto)
            cv2.rectangle(tela, (x, y), (x + w, y + h), (0, 255, 0), 2)
            for px, py in rosto[4:14].reshape(5, 2):
                cv2.circle(tela, (int(px), int(py)), 2, (0, 255, 255), -1)

        cv2.putText(tela, f"{nome}: {n_fotos}/{META_POR_PESSOA}", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)
        proxima = "  N=proxima" if len(nomes) > 1 else ""
        cv2.putText(tela, f"ESPACO=capturar  A=auto:{'ON' if auto else 'OFF'}{proxima}  Q=sair",
                    (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
        if ultimo_rosto is not None and min(tela.shape[:2]) > TAMANHO_PREVIEW + 20:
            # recorte mais recente, no canto: serve de conferencia do enquadramento
            margem = TAMANHO_PREVIEW + 10
            coluna = tela.shape[1] - margem
            tela[10:margem, coluna:coluna + TAMANHO_PREVIEW] = cv2.resize(
                ultimo_rosto, (TAMANHO_PREVIEW, TAMANHO_PREVIEW))
            cv2.rectangle(tela, (coluna, 10), (tela.shape[1] - 10, margem),
                          (255, 255, 255), 2)
        cv2.imshow("Captura de rostos", tela)

        tecla = cv2.waitKey(1) & 0xFF
        if tecla == ord("q"):
            break
        if tecla == ord("a"):
            auto = not auto
        if tecla == ord("n"):
            indice = (indice + 1) % len(nomes)

        quer_capturar = tecla == ord(" ") or (
            auto and time.time() - ultima_captura >= AUTO_INTERVALO_MS / 1000
        )
        if quer_capturar and len(rostos) > 0:
            rosto = alinhar(frame, max(rostos, key=lambda r: r[2] * r[3]))
            salvar_recorte(pasta, rosto)
            ultimo_rosto = rosto
            ultima_captura = time.time()

    captura.release()
    cv2.destroyAllWindows()
    for nome, pasta in zip(nomes, pastas):
        print(f"{nome}: {contar_fotos(pasta)} fotos salvas")


if __name__ == "__main__":
    main()

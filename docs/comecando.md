# Instalação e primeira execução

[← README](../README.md)

Este guia leva do clone até a UI web e a demo OpenCV. O projeto usa Python 3.11,
uma webcam e internet na primeira execução.

## Requisitos

- Python 3.11
- Webcam (a UI também aceita upload de foto)
- Internet na primeira execução: o detector YuNet, o modelo de emoção
  `enet_b2_7` e a base LFW são baixados automaticamente.

## Instalação

Da raiz do projeto:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## 1. Coletar as fotos

Cada integrante roda o script com o próprio nome. O nome da pasta vira o rótulo
da classe no modelo, então use exatamente o mesmo texto em todos os lugares:

```powershell
python src/captura_faces.py <nome>
```

Pessoas de fora do grupo entram na classe `Desconhecido`:

```powershell
python src/captura_faces.py --desconhecido <nome>
```

Dicas:

- Colete ~200 fotos por integrante, variando pose, distância e luz.
- Colete desconhecidos com a mesma webcam e nos mesmos ambientes da demo.
- Para vídeo: `python src/extrair_video.py <video> <nome>`.
- Para fotos de celular: `python src/recortar_galeria.py <pasta> <nome> --integrante`.

Os comandos criam `dados/integrantes/<nome>/` ou
`dados/desconhecidos/<nome>/`.

## 2. Treinar a CNN

Abra `atividade_cnn_rostos.ipynb` no VS Code ou Jupyter e execute todas as
células. Na primeira execução o notebook baixa o LFW (classe `Desconhecido`).

No fim, ele grava:

- `modelos/modelo_rostos.keras`
- `modelos/classes.txt`

As métricas da atividade (matriz de confusão, acurácia, precisão, recall e F1)
são geradas nessa execução. O notebook publicado está sem outputs para não
expor fotos ou nomes; os números aparecem quando você roda.

## 3. Verificar

```powershell
python src/verificar_modelo.py
```

Esse comando confere se o modelo e o `classes.txt` são da mesma execução e se o
modelo reconhece as fotos locais. Corrija o que ele apontar antes de apresentar.

## 4. Rodar

UI web (câmera ao vivo + upload):

```powershell
python src/app_demo.py
# abra http://127.0.0.1:5000
```

Demo OpenCV:

```powershell
python src/demo_reconhecimento.py --emocao
```

A câmera do navegador exige `localhost`/`127.0.0.1` ou HTTPS. O upload de foto
funciona mesmo sem webcam.

## Usar um modelo já treinado

Se o grupo enviar `modelo_treinado.zip`, copie os dois arquivos para `modelos/`:

```text
modelos/modelo_rostos.keras
modelos/classes.txt
```

Eles precisam ser da mesma execução. Depois rode `python src/verificar_modelo.py`
e a UI.

## Problemas comuns

- `Modelo de identidade não encontrado`: rode o notebook depois de coletar as
  fotos; ele gera `modelo_rostos.keras` e `classes.txt`.
- `Nenhuma foto em ...`: a pasta do integrante está vazia; colete as fotos
  novamente.
- `Webcam indisponível`: feche o programa que está usando a câmera ou tente
  `--camera 1`.
- A câmera não abre no navegador: use `http://127.0.0.1:5000` ou HTTPS; em outro
  dispositivo da rede, o navegador exige HTTPS.
- O modelo reconhece errado: veja [Modelo de identidade](modelo.md) e
  [Dados e privacidade](dados.md).

## Próximos passos

- [Interface web](ui.md)
- [Modelo de identidade](modelo.md)
- [Emoções](emocao.md)
- [Dados e privacidade](dados.md)
- [Desenvolvimento e build](desenvolvimento.md)

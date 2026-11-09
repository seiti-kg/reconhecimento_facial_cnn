# Reconhecimento facial com CNN

Projeto de reconhecimento de identidade com uma CNN treinada pelo grupo e
reconhecimento de emoção com um modelo pré-treinado. Inclui uma UI web local
(câmera ao vivo + upload de foto) e uma demo OpenCV.

O repositório contém apenas o código. As fotos usadas no treino e o modelo
treinado **não** são versionados: cada pessoa coleta as próprias fotos e treina
a própria CNN.

## O que não está no repositório

- `dados/` — fotos de integrantes e de pessoas de fora.
- `modelos/` — modelo `modelo_rostos.keras`, `classes.txt` e modelos de terceiros
  baixados automaticamente.
- Qualquer `*.zip` com fotos ou modelo.

O [`.gitignore`](.gitignore) já bloqueia esses arquivos. Se você recebeu um
`modelo_treinado.zip` do grupo, extraia `modelo_rostos.keras` e `classes.txt`
em `modelos/`. Se recebeu `fotos_treinadas.zip`, extraia em `dados/` e rode o
notebook para treinar.

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

As métricas da atividade (matriz de confusão, acurácia, precisão, recall e
F1) são geradas nessa execução. O notebook publicado está sem outputs para não
expor fotos ou nomes; os números aparecem quando você roda.

## 3. Verificar e rodar

```powershell
python src/verificar_modelo.py
```

Esse comando confere se o modelo e o `classes.txt` são da mesma execução e se o
modelo reconhece as fotos locais.

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

## Privacidade

As fotos e o modelo ficam na sua máquina. A UI processa tudo em `127.0.0.1` e
não grava as imagens. Nunca comite `dados/`, `modelos/` ou os zips privados.

## Créditos

- Detector facial e modelo de expressão do [OpenCV Zoo](https://github.com/opencv/opencv_zoo).
- Modelo de emoção [EmotiEffLib](https://github.com/sb-ai-lab/EmotiEffLib)
  (`enet_b2_7`, AffectNet).
- Base [LFW](http://vis-www.cs.umass.edu/lfw/) via `scikit-learn`.
- Os modelos de terceiros mantêm suas licenças originais.

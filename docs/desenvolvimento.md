# Desenvolvimento e build

[← README](../README.md)

## Estrutura

```text
atividade_cnn_rostos.ipynb   treino, avaliação e métricas
src/
    app_demo.py              UI web (câmera + upload)
    demo_reconhecimento.py   demo OpenCV
    captura_faces.py         coleta pela webcam
    extrair_video.py         coleta a partir de vídeo
    recortar_galeria.py      coleta a partir de fotos
    deteccao.py              YuNet, alinhamento e pré-processamento
    emocao.py                modelo de expressão pré-treinado
    config.py                caminhos e parâmetros
    verificar_modelo.py      checagem antes da demo
    templates/demo.html
    static/demo.css
    static/demo.js
dados/                       ignorado no Git
modelos/                     ignorado no Git
```

## Dependências

O ambiente de referência está em `requirements.txt`: Python 3.11, TensorFlow,
OpenCV, scikit-learn, pandas, matplotlib, seaborn, Pillow e Flask.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Na primeira execução, o código baixa o detector YuNet e o modelo de emoção
`enet_b2_7`. O notebook baixa o LFW. Sem internet, copie os ONNX para
`modelos/` e o LFW para o cache do scikit-learn.

## Verificação

```powershell
python -m py_compile src/app_demo.py src/demo_reconhecimento.py `
  src/captura_faces.py src/extrair_video.py src/recortar_galeria.py `
  src/deteccao.py src/emocao.py src/config.py src/verificar_modelo.py
```

```powershell
python src/verificar_modelo.py
```

A checagem confere modelo, `classes.txt` e reconhecimento das fotos locais.
Para testar a UI:

```powershell
python src/app_demo.py
# http://127.0.0.1:5000
```

Não há suíte de testes automatizada; a verificação é feita pelo script acima e
por smoke tests da UI (upload de uma foto conhecida, uma foto de fora, foto sem
rosto e câmera).

## Adicionar um integrante

1. Colete as fotos com `python src/captura_faces.py <nome>`.
2. Rode o notebook inteiro; ele lê as pastas de `dados/integrantes/` e gera um
   novo `classes.txt` e modelo.
3. Rode `python src/verificar_modelo.py` e a demo.

Não edite `classes.txt` à mão: a ordem e o número de classes precisam bater com
a saída do modelo.

## Ajustar o limiar

`CONFIANCA_MINIMA` fica em `src/config.py`. Subir o limiar reduz falsos
positivos de integrante e aumenta rejeições; descer faz o contrário. O notebook
mostra a tabela de limiares no conjunto de teste. Depois de alterar, reinicie a
UI/demo.

## Publicar no GitHub

O `.gitignore` já bloqueia dados, modelos e zips. Antes de commitar:

```powershell
git status --short
git ls-files | Select-String "^(dados|modelos)/"
```

O segundo comando deve ficar vazio. Depois:

```powershell
git add .
git commit -m "Reconhecimento facial com CNN e UI local"
git branch -M main
git remote add origin https://github.com/<usuario>/<repositorio>.git
git push -u origin main
```

Crie o repositório vazio no GitHub antes do push. Se ele já tiver README, rode
`git pull --rebase origin main` antes. Autenticação é pelo navegador/token; não
commite token.

## Créditos

- Detector facial e modelo de expressão do
  [OpenCV Zoo](https://github.com/opencv/opencv_zoo).
- Modelo de emoção [EmotiEffLib](https://github.com/sb-ai-lab/EmotiEffLib)
  (`enet_b2_7`, AffectNet).
- Base [LFW](http://vis-www.cs.umass.edu/lfw/) via `scikit-learn`.
- Os modelos de terceiros mantêm suas licenças originais.

## Próximos passos

- [Instalação e primeira execução](comecando.md)
- [Modelo de identidade](modelo.md)
- [Emoções](emocao.md)
- [Dados e privacidade](dados.md)

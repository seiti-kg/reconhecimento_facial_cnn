# Dados e privacidade

[← README](../README.md)

As fotos e o modelo treinado ficam fora do Git. O repositório público é apenas
código; o `.gitignore` bloqueia `dados/`, `modelos/` e `*.zip`.

## Estrutura

```text
dados/
    integrantes/<nome>/       uma pasta por integrante = uma classe
    desconhecidos/<origem>/   gente de fora = classe Desconhecido
modelos/
    modelo_rostos.keras       gerado pelo notebook (ignorado)
    classes.txt               gerado pelo notebook (ignorado)
    *.onnx                    YuNet e emoção (baixados, ignorados)
```

## Coleta

Integrante:

```powershell
python src/captura_faces.py <nome>
```

Pessoa de fora:

```powershell
python src/captura_faces.py --desconhecido <nome>
```

O script grava recortes alinhados de 112×112, com o mesmo detector e
alinhamento da demo. Use o mesmo nome de pasta em todos os lugares: ele é o
rótulo da classe.

Boas práticas:

- ~200 fotos por integrante, em pelo menos duas sessões de luz.
- Varie pose (até ~30 graus), distância (perto e ~1 m) e expressão.
- Colete desconhecidos com a **mesma webcam** e nos mesmos ambientes da demo;
  isso ensina que o quarto/câmera não é a pessoa.
- Para vídeo: `python src/extrair_video.py <video> <nome>`.
- Para fotos de celular: `python src/recortar_galeria.py <pasta> <nome> --integrante`.

## Desconhecidos e LFW

O notebook baixa o LFW automaticamente na primeira execução e usa até duas
fotos por pessoa, formando a classe `Desconhecido`. As pastas de
`dados/desconhecidos/` entram como pessoas de fora adicionais.

O LFW é útil para variedade de identidades, mas vem de outras câmeras. Se o
objetivo é rejeitar um amigo na frente da sua webcam, colete esse amigo com
`--desconhecido` nos mesmos ambientes.

## Privacidade

- A UI processa tudo em `127.0.0.1`; as imagens não são gravadas.
- `dados/` e `modelos/` nunca devem ser commitados.
- Não coloque zips com fotos ou modelo no repositório; `*.zip` está no
  `.gitignore`.
- Antes de publicar, confira `git status` e `git ls-files`.
- Para enviar ao grupo, use um canal privado (Drive, WhatsApp, etc.), não o
  GitHub público.

## Zips privados

Fotos para quem vai retreinar:

```powershell
Compress-Archive -Path dados\integrantes,dados\desconhecidos `
  -DestinationPath "$env:USERPROFILE\Desktop\fotos_treinadas.zip" -Force
```

Modelo + classes para quem só quer rodar:

```powershell
Compress-Archive -Path modelos\modelo_rostos.keras,modelos\classes.txt `
  -DestinationPath "$env:USERPROFILE\Desktop\modelo_treinado.zip" -Force
```

O `modelo_treinado.zip` deve ser extraído em `modelos/`; o
`fotos_treinadas.zip` em `dados/`. O modelo e o `classes.txt` precisam ser da
mesma execução.

## Próximos passos

- [Instalação e primeira execução](comecando.md)
- [Modelo de identidade](modelo.md)
- [Desenvolvimento e build](desenvolvimento.md)

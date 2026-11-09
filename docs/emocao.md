# Emoções

[← README](../README.md)

A emoção usa um modelo pronto do EmotiEffLib, permitido pela atividade; a
identidade continua sendo a CNN treinada pelo grupo. O módulo é
`src/emocao.py`.

## Modelo padrão: `enet_b2_7`

- EfficientNet-B2 treinado no AffectNet com **7 classes**: Bravo, Nojo, Medo,
  Alegre, Neutro, Triste e Surpreso.
- Acurácia publicada: **66,34%** no AffectNet de 7 classes.
- Entrada: recorte 260×260 em RGB, normalizado com média e desvio do ImageNet.
- Custo: cerca de 35 ms por rosto em CPU; o modelo é baixado automaticamente
  para `modelos/enet_b2_7.onnx`.

O recorte é alinhado no padrão ArcFace em 260 px, maior que o recorte de 112 px
usado pela CNN de identidade. Isso preserva detalhe para o modelo de emoção.

## Por que não o `enet_b2_8`

O `enet_b2_8` tem uma oitava classe, **Desprezo**. Em testes com um sorriso
real, ele colocou 49,8% em Desprezo e apenas 24% em Alegre; variações de
recorte e margem mantiveram o erro. O `enet_b2_7` é treinado nativamente com as
7 expressões e classificou o mesmo sorriso como **Alegre 91,4%**.

A troca também foi validada na imagem oficial do EmotiEffLib com três rostos:
o `enet_b2_7` devolveu Alegre, Bravo e Medo, os três rótulos esperados.

## Modelo alternativo

O modelo do OpenCV Zoo (`facial_expression_recognition_mobilefacenet`) também
está disponível:

```powershell
python src/demo_reconhecimento.py --emocao atual
```

- 7 expressões, RAF-DB, 88,27% publicado.
- Cerca de 3 ms por rosto; é o mais rápido.
- Nas fotos de identidade ele é muito confiante e tende a dizer "Alegre"; na
  imagem oficial de teste ele errou dois dos três rótulos.
- A UI web usa o `enet_b2_7` por padrão; `atual` fica como opção de velocidade
  na demo OpenCV.

## Limitações

- Não existe uma base rotulada de expressões dos integrantes; a escolha do
  modelo foi feita por validação oficial e por casos reais, não por uma matriz
  de confusão própria.
- Bases diferentes não se comparam diretamente: 88,27% no RAF-DB e 66,34% no
  AffectNet medem dificuldades diferentes.
- O modelo é sensível a oclusão, óculos, iluminação e recorte. A suavização de
  8 quadros no ao vivo reduz o piscar de rótulo, mas não corrige um erro
  sistemático.
- Para uma avaliação robusta, colete alguns segundos de cada expressão por
  integrante e compare os modelos nessa base.

## Próximos passos

- [Modelo de identidade](modelo.md)
- [Interface web](ui.md)
- [Dados e privacidade](dados.md)

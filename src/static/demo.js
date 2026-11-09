"use strict";

const CONFIG = window.DEMO_CONFIG || {};
const LIMIAR = Number(CONFIG.limiar ?? 0.8);
const LIMIAR_TXT = LIMIAR.toLocaleString("pt-BR", {
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
});
const HISTORY_LIMIT = 8;
const LIVE_INTERVAL = 30;
const STALE_MS = 2000;
const MAX_UPLOAD = 32 * 1024 * 1024;
const CAPTURE_MAX = 960;
const JPEG_QUALITY = 0.78;
const STAGE_OK = "#4ade80";
const STAGE_DANGER = "#fb7185";
const STAGE_WARN = "#fbbf24";
const FONT_MONO = '600 12px "Cascadia Mono", Consolas, monospace';
const FONT_MONO_SM = '500 11px "Cascadia Mono", Consolas, monospace';

const $ = (id) => document.getElementById(id);
const dom = {
  modeLive: $("mode-live"),
  modePhoto: $("mode-photo"),
  status: $("status"),
  statusDot: $("status-dot"),
  statusText: $("status-text"),
  cameraToggle: $("camera-toggle"),
  photoButton: $("photo-button"),
  photoInput: $("photo-input"),
  errorBanner: $("error-banner"),
  errorText: $("error-text"),
  errorClose: $("error-close"),
  stage: $("stage"),
  scene: $("scene"),
  stageEmpty: $("stage-empty"),
  stageEmptyTitle: $("stage-empty-title"),
  stageEmptyBody: $("stage-empty-body"),
  dropzone: $("dropzone"),
  stageLoading: $("stage-loading"),
  stageBadge: $("stage-badge"),
  badgeDot: $("badge-dot"),
  badgeText: $("badge-text"),
  stageFooter: $("stage-footer"),
  techRes: $("tech-res"),
  techFaces: $("tech-faces"),
  techLatency: $("tech-latency"),
  techRate: $("tech-rate"),
  faceCount: $("face-count"),
  results: $("results"),
  readoutFooter: $("readout-footer"),
  video: $("video"),
};

const ctx = dom.scene.getContext("2d");
const frameCanvas = document.createElement("canvas");
const frameCtx = frameCanvas.getContext("2d");

let mode = "live";
let stream = null;
let cameraToken = 0;
let animationId = null;
let analysisTimer = null;
let inFlight = false;
let controller = null;
let history = [];
let lastResult = null;
let lastResultAt = 0;
let analysisTimes = [];
let boxesSuaves = [];
let boxEm = 0;
let photoUrl = null;
let photoImage = null;
let photoView = null;
let photoController = null;
let statusKey = "";
let stageSize = { largura: 1, altura: 1 };

const nfPct = new Intl.NumberFormat("pt-BR", { maximumFractionDigits: 1 });
const nfRate = new Intl.NumberFormat("pt-BR", {
  minimumFractionDigits: 1,
  maximumFractionDigits: 1,
});

function formatPct(value) {
  return `${nfPct.format(Math.max(0, Math.min(1, Number(value) || 0)) * 100)}%`;
}

function formatRate(value) {
  return `${nfRate.format(value)} an/s`;
}

function topEntries(probabilidades, quantidade) {
  return Object.entries(probabilidades || {})
    .sort((a, b) => b[1] - a[1])
    .slice(0, quantidade);
}

function averageProbabilities(lista) {
  const total = {};
  for (const probabilidades of lista) {
    for (const [chave, valor] of Object.entries(probabilidades || {})) {
      total[chave] = (total[chave] || 0) + Number(valor || 0);
    }
  }
  for (const chave of Object.keys(total)) {
    total[chave] /= lista.length;
  }
  return total;
}

function montarFace(face, probabilidadesIdentidade, probabilidadesEmocao) {
  const [palpite, confianca] = topEntries(probabilidadesIdentidade, 1)[0] || ["Desconhecido", 0];
  const desconhecido = confianca < LIMIAR || palpite === "Desconhecido";
  const [emocao, confiancaEmocao] = topEntries(probabilidadesEmocao, 1)[0] || ["—", 0];
  return {
    caixa: face.caixa,
    identidade: {
      nome: desconhecido ? "Desconhecido" : palpite,
      palpite,
      confianca,
      desconhecido,
      probabilidades: probabilidadesIdentidade,
    },
    emocao: {
      nome: emocao,
      confianca: confiancaEmocao,
      probabilidades: probabilidadesEmocao,
    },
  };
}

function smoothFaces(data) {
  if (!data.rostos || data.rostos.length !== 1) {
    history = [];
    return data;
  }
  const face = data.rostos[0];
  history.push(face);
  if (history.length > HISTORY_LIMIT) {
    history.shift();
  }
  if (history.length === 1) {
    return data;
  }
  const identidade = averageProbabilities(
    history.map((item) => item.identidade.probabilidades)
  );
  const emocao = averageProbabilities(
    history.map((item) => item.emocao.probabilidades)
  );
  return {
    ...data,
    rostos: [montarFace(face, identidade, emocao)],
  };
}

function setStatus(texto, estado = "idle") {
  const chave = `${estado}|${texto}`;
  if (chave === statusKey) {
    return;
  }
  statusKey = chave;
  dom.statusText.textContent = texto;
  dom.statusDot.className = `dot is-${estado}`;
}

function showError(mensagem) {
  dom.errorText.textContent = mensagem;
  dom.errorBanner.hidden = false;
}

function clearError() {
  dom.errorBanner.hidden = true;
  dom.errorText.textContent = "";
}

function showBadge(tipo) {
  dom.stageBadge.hidden = false;
  dom.stageBadge.classList.toggle("is-photo", tipo !== "live");
  dom.badgeText.textContent = tipo === "live" ? "AO VIVO" : "FOTO";
}

function hideBadge() {
  dom.stageBadge.hidden = true;
}

function showStageEmpty(titulo, corpo) {
  dom.stageEmptyTitle.textContent = titulo;
  dom.stageEmptyBody.textContent = corpo;
  dom.stageEmpty.hidden = false;
  dom.dropzone.hidden = true;
  dom.scene.hidden = true;
  dom.stageLoading.hidden = true;
  hideBadge();
}

function showDropzone() {
  dom.stageEmpty.hidden = true;
  dom.dropzone.hidden = false;
  dom.scene.hidden = true;
  dom.stageLoading.hidden = true;
  hideBadge();
}

function showMedia() {
  dom.stageEmpty.hidden = true;
  dom.dropzone.hidden = true;
  dom.scene.hidden = false;
}

function setLoading(ativo) {
  dom.stageLoading.hidden = !ativo;
}

function setFaceCount(quantidade) {
  dom.faceCount.textContent = `${quantidade} ${quantidade === 1 ? "rosto" : "rostos"}`;
}

function appendReadoutEmpty(titulo, corpo) {
  const bloco = document.createElement("div");
  bloco.className = "readout-empty";
  const strong = document.createElement("strong");
  strong.textContent = titulo;
  const p = document.createElement("p");
  p.textContent = corpo;
  bloco.append(strong, p);
  dom.results.append(bloco);
}

function footerText() {
  return `Limiar ${LIMIAR_TXT} · ${
    mode === "live" ? "suavização 8 quadros no ao vivo" : "foto estática"
  } · processamento local`;
}

function renderReadoutEmpty(titulo, corpo) {
  dom.results.replaceChildren();
  dom.results.classList.toggle("is-live", mode === "live");
  setFaceCount(0);
  appendReadoutEmpty(titulo, corpo);
  dom.readoutFooter.textContent = footerText();
}

function createFace(face, indice, total) {
  const secao = document.createElement("section");
  secao.className = "face";

  const cabecalho = document.createElement("div");
  cabecalho.className = "face-head";
  const idx = document.createElement("span");
  idx.className = "idx";
  idx.textContent = `#${indice + 1}`;
  const nome = document.createElement("h3");
  nome.textContent = face.identidade.nome;
  const pct = document.createElement("span");
  pct.className = "pct";
  pct.textContent = formatPct(face.identidade.confianca);
  cabecalho.append(idx, nome, pct);

  const barra = document.createElement("div");
  barra.className = `bar ${face.identidade.desconhecido ? "is-unknown" : "is-ok"}`;
  const preenchimento = document.createElement("span");
  preenchimento.style.width = `${Math.max(0, Math.min(1, face.identidade.confianca)) * 100}%`;
  const marca = document.createElement("i");
  marca.className = "threshold";
  marca.style.left = `${LIMIAR * 100}%`;
  barra.append(preenchimento, marca);

  const nota = document.createElement("div");
  nota.className = "identity-note";
  if (face.identidade.desconhecido) {
    nota.textContent = `abaixo do limiar de ${formatPct(LIMIAR)}`;
    if (face.identidade.palpite && face.identidade.palpite !== "Desconhecido") {
      nota.append(document.createElement("br"));
      const proximo = document.createElement("span");
      proximo.textContent = `mais próximo: ${face.identidade.palpite} ${formatPct(
        face.identidade.confianca
      )}`;
      nota.append(proximo);
    }
  } else {
    nota.textContent = `limiar ${formatPct(LIMIAR)}`;
  }

  const emocao = document.createElement("div");
  emocao.className = "emotion";
  const emocaoCabecalho = document.createElement("div");
  emocaoCabecalho.className = "emotion-head";
  const emocaoLabel = document.createElement("span");
  emocaoLabel.textContent = "Emoção";
  const emocaoNome = document.createElement("strong");
  emocaoNome.textContent = face.emocao.nome;
  const emocaoPct = document.createElement("em");
  emocaoPct.textContent = formatPct(face.emocao.confianca);
  emocaoCabecalho.append(emocaoLabel, emocaoNome, emocaoPct);
  emocao.append(emocaoCabecalho);

  for (const [posicao, [rotulo, valor]] of topEntries(
    face.emocao.probabilidades,
    3
  ).entries()) {
    const linha = document.createElement("div");
    linha.className = `emo-row${posicao === 0 ? " is-top" : ""}`;
    const rotuloElemento = document.createElement("span");
    rotuloElemento.textContent = rotulo;
    const barraEmocao = document.createElement("div");
    barraEmocao.className = "bar";
    const preenchimentoEmocao = document.createElement("span");
    preenchimentoEmocao.style.width = `${Math.max(0, Math.min(1, valor)) * 100}%`;
    barraEmocao.append(preenchimentoEmocao);
    const valorElemento = document.createElement("b");
    valorElemento.textContent = formatPct(valor);
    linha.append(rotuloElemento, barraEmocao, valorElemento);
    emocao.append(linha);
  }

  secao.append(cabecalho, barra, nota, emocao);
  return secao;
}

function renderReadout(rostos, meta = {}) {
  dom.results.replaceChildren();
  dom.results.classList.toggle("is-live", mode === "live");
  setFaceCount(rostos.length);
  dom.readoutFooter.textContent =
    meta.tempo_ms != null
      ? `Limiar ${LIMIAR_TXT} · foto estática · ${Math.round(meta.tempo_ms)} ms no servidor`
      : footerText();

  if (!rostos.length) {
    const aoVivo = mode === "live";
    appendReadoutEmpty(
      aoVivo ? "Nenhum rosto no quadro." : "Nenhum rosto detectado.",
      aoVivo
        ? "Aproxime o rosto e olhe para a câmera."
        : "Use uma foto com o rosto de frente e maior."
    );
    return;
  }

  rostos.forEach((face, indice) => {
    dom.results.append(createFace(face, indice, rostos.length));
  });
}

function updateStageSize() {
  const alturaRodape = dom.stageFooter ? dom.stageFooter.offsetHeight : 30;
  stageSize = {
    largura: Math.max(1, dom.stage.clientWidth),
    altura: Math.max(1, dom.stage.clientHeight - alturaRodape),
  };
}

function ensureCanvasSize() {
  const dpr = window.devicePixelRatio || 1;
  const largura = Math.round(stageSize.largura * dpr);
  const altura = Math.round(stageSize.altura * dpr);
  if (dom.scene.width !== largura || dom.scene.height !== altura) {
    dom.scene.width = largura;
    dom.scene.height = altura;
  }
  dom.scene.style.width = `${stageSize.largura}px`;
  dom.scene.style.height = `${stageSize.altura}px`;
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
}

function clearScene() {
  ctx.save();
  ctx.setTransform(1, 0, 0, 1, 0, 0);
  ctx.clearRect(0, 0, dom.scene.width, dom.scene.height);
  ctx.restore();
}

function drawLabel(texto, x, y, cor, fonte, larguraCena, alturaCena) {
  const padX = 6;
  const altura = 18;
  ctx.save();
  ctx.font = fonte;
  ctx.textBaseline = "middle";
  const largura = ctx.measureText(texto).width + padX * 2;
  const bx = Math.min(Math.max(x, 4), larguraCena - largura - 4);
  const by = Math.min(Math.max(y, 4), alturaCena - altura - 4);
  ctx.fillStyle = "rgba(0, 0, 0, 0.86)";
  ctx.fillRect(bx, by, largura, altura);
  ctx.strokeStyle = cor;
  ctx.lineWidth = 1;
  ctx.strokeRect(bx + 0.5, by + 0.5, largura - 1, altura - 1);
  ctx.fillStyle = cor;
  ctx.fillText(texto, bx + padX, by + altura / 2 + 0.5);
  ctx.restore();
}

function drawCorners(x, y, w, h, lado) {
  ctx.beginPath();
  ctx.moveTo(x, y + lado);
  ctx.lineTo(x, y);
  ctx.lineTo(x + lado, y);
  ctx.moveTo(x + w - lado, y);
  ctx.lineTo(x + w, y);
  ctx.lineTo(x + w, y + lado);
  ctx.moveTo(x + w, y + h - lado);
  ctx.lineTo(x + w, y + h);
  ctx.lineTo(x + w - lado, y + h);
  ctx.moveTo(x + lado, y + h);
  ctx.lineTo(x, y + h);
  ctx.lineTo(x, y + h - lado);
  ctx.stroke();
}

function drawFace(face, indice, total, escala, offsetX, offsetY, larguraCena, alturaCena) {
  const [baseX, baseY, baseW, baseH] = face.caixa;
  const x = baseX * escala + offsetX;
  const y = baseY * escala + offsetY;
  const w = baseW * escala;
  const h = baseH * escala;
  if (w < 8 || h < 8) {
    return;
  }
  const desconhecido = face.identidade.desconhecido;
  const cor = desconhecido ? STAGE_DANGER : STAGE_OK;

  ctx.save();
  ctx.strokeStyle = cor;
  ctx.lineWidth = 1;
  ctx.strokeRect(x + 0.5, y + 0.5, w - 1, h - 1);
  ctx.lineWidth = 2;
  drawCorners(x, y, w, h, Math.min(10, w / 3, h / 3));
  ctx.restore();

  const prefixo = total > 1 ? `#${indice + 1}` : "";
  if (total > 1) {
    drawLabel(prefixo, x, y + 4, cor, FONT_MONO, larguraCena, alturaCena);
    return;
  }

  const textoIdentidade = `${face.identidade.nome} ${formatPct(
    face.identidade.confianca
  )}`;
  const yIdentidade = y > 24 ? y - 22 : y + 4;
  drawLabel(textoIdentidade, x, yIdentidade, cor, FONT_MONO, larguraCena, alturaCena);

  const textoEmocao = `${face.emocao.nome} ${formatPct(face.emocao.confianca)}`;
  const yEmocao = y + h + 6 + 18 <= alturaCena ? y + h + 6 : y + h - 22;
  drawLabel(textoEmocao, x, yEmocao, STAGE_WARN, FONT_MONO_SM, larguraCena, alturaCena);
}

function updateSceneAria(rostos) {
  if (!rostos.length) {
    dom.scene.setAttribute("aria-label", "Nenhum rosto detectado.");
    return;
  }
  const resumo = rostos
    .map(
      (face, indice) =>
        `${indice + 1}: ${face.identidade.nome}, ${formatPct(
          face.identidade.confianca
        )}, ${face.emocao.nome}, ${formatPct(face.emocao.confianca)}`
    )
    .join("; ");
  dom.scene.setAttribute("aria-label", `${rostos.length} rosto(s). ${resumo}`);
}

function redrawPhoto() {
  if (mode === "photo" && photoImage && photoView) {
    drawScene(
      photoImage,
      photoView.largura,
      photoView.altura,
      photoView.rostos
    );
  }
}

function drawScene(fonte, largura, altura, rostos) {
  if (!fonte || !largura || !altura) {
    return;
  }
  updateStageSize();
  if (stageSize.largura < 2 || stageSize.altura < 2) {
    return;
  }
  ensureCanvasSize();
  const larguraCena = stageSize.largura;
  const alturaCena = stageSize.altura;
  clearScene();
  const escala = Math.min(larguraCena / largura, alturaCena / altura);
  const desenhoLargura = largura * escala;
  const desenhoAltura = altura * escala;
  const offsetX = (larguraCena - desenhoLargura) / 2;
  const offsetY = (alturaCena - desenhoAltura) / 2;
  ctx.drawImage(fonte, offsetX, offsetY, desenhoLargura, desenhoAltura);
  for (const [indice, face] of rostos.entries()) {
    drawFace(
      face,
      indice,
      rostos.length,
      escala,
      offsetX,
      offsetY,
      larguraCena,
      alturaCena
    );
  }
  updateSceneAria(rostos);
}

function fitSize(largura, altura, maximo) {
  const escala = Math.min(1, maximo / Math.max(largura, altura));
  return {
    largura: Math.max(1, Math.round(largura * escala)),
    altura: Math.max(1, Math.round(altura * escala)),
  };
}

function updateTech({ largura, altura, rostos, latency, rate, tempo_ms } = {}) {
  dom.techRes.textContent =
    largura && altura ? `${largura}×${altura}` : "—";
  dom.techFaces.textContent = Number.isFinite(rostos) ? String(rostos) : "—";
  const latencia = latency != null ? latency : tempo_ms;
  dom.techLatency.textContent =
    latencia != null ? `${Math.round(latencia)} ms` : "—";
  dom.techRate.textContent = rate != null && rate > 0 ? formatRate(rate) : "—";
}

function currentRate() {
  const agora = Date.now();
  analysisTimes = analysisTimes.filter((instante) => agora - instante < 3000);
  return analysisTimes.length / 3;
}

function resetLiveState() {
  lastResult = null;
  lastResultAt = 0;
  history = [];
  analysisTimes = [];
  boxesSuaves = [];
  boxEm = 0;
}

function stopCamera({ fromMode = false } = {}) {
  cameraToken += 1;
  if (controller) {
    controller.abort();
  }
  controller = null;
  inFlight = false;
  clearTimeout(analysisTimer);
  analysisTimer = null;
  if (animationId) {
    cancelAnimationFrame(animationId);
    animationId = null;
  }
  if (stream) {
    stream.getTracks().forEach((track) => track.stop());
  }
  stream = null;
  dom.video.srcObject = null;
  resetLiveState();
  clearScene();
  dom.scene.hidden = true;
  dom.cameraToggle.disabled = false;
  dom.cameraToggle.textContent = "Iniciar câmera";
  setLoading(false);
  hideBadge();
  setStatus("Câmera desligada", "idle");
  updateTech({});
  if (!fromMode) {
    showStageEmpty(
      "Câmera desligada",
      "Inicie a câmera para reconhecer quem está no quadro."
    );
    renderReadoutEmpty(
      "Nenhuma leitura ainda.",
      "Ligue a câmera ou envie uma foto."
    );
  }
}

async function startCamera() {
  clearError();
  if (mode !== "live") {
    return;
  }
  if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
    showError("A câmera exige localhost ou HTTPS.");
    setStatus("Câmera indisponível", "error");
    showStageEmpty("Câmera indisponível", "Use uma foto para continuar.");
    dom.cameraToggle.textContent = "Tentar novamente";
    return;
  }

  const token = ++cameraToken;
  dom.cameraToggle.disabled = true;
  dom.cameraToggle.textContent = "Conectando…";
  setStatus("Conectando à câmera", "working");
  showStageEmpty("Conectando à câmera…", "Autorize o acesso no navegador.");

  try {
    const novoStream = await navigator.mediaDevices.getUserMedia({
      video: {
        width: { ideal: 1280 },
        height: { ideal: 720 },
        facingMode: "user",
      },
      audio: false,
    });
    if (token !== cameraToken || mode !== "live") {
      novoStream.getTracks().forEach((track) => track.stop());
      return;
    }
    stream = novoStream;
    dom.video.srcObject = novoStream;
    await dom.video.play();
    if (token !== cameraToken || mode !== "live") {
      novoStream.getTracks().forEach((track) => track.stop());
      stream = null;
      dom.video.srcObject = null;
      return;
    }

    resetLiveState();
    showMedia();
    showBadge("live");
    setStatus("Câmera ativa", "live");
    dom.cameraToggle.textContent = "Parar câmera";
    renderReadoutEmpty(
      "Nenhuma leitura ainda.",
      "A análise começa assim que um rosto aparecer."
    );
    updateTech({});
    renderLiveFrame();
    scheduleAnalysis();
  } catch (error) {
    if (token !== cameraToken) {
      return;
    }
    if (stream) {
      stream.getTracks().forEach((track) => track.stop());
      stream = null;
    }
    dom.video.srcObject = null;
    const mensagem =
      error && error.name === "NotAllowedError"
        ? "Permissão da câmera negada. Libere o acesso no navegador ou use uma foto."
        : error && error.name === "NotFoundError"
          ? "Nenhuma câmera encontrada. Use uma foto."
          : "Não foi possível abrir a câmera. Use uma foto.";
    showError(mensagem);
    setStatus("Câmera indisponível", "error");
    showStageEmpty("Câmera indisponível", "Use uma foto ou tente novamente.");
    dom.cameraToggle.textContent = "Tentar novamente";
  } finally {
    if (token === cameraToken) {
      dom.cameraToggle.disabled = false;
    }
  }
}

function suavizarCaixas(rostos) {
  if (!rostos.length) {
    boxesSuaves = [];
    boxEm = 0;
    return rostos;
  }
  const agora = performance.now();
  if (boxesSuaves.length !== rostos.length) {
    boxesSuaves = rostos.map((face) => face.caixa.slice());
    boxEm = agora;
  } else {
    const delta = Math.min(0.1, (agora - boxEm) / 1000);
    const alpha = 1 - Math.exp(-delta / 0.05);
    boxesSuaves = boxesSuaves.map((caixa, indice) =>
      caixa.map(
        (valor, eixo) =>
          valor + (rostos[indice].caixa[eixo] - valor) * alpha
      )
    );
    boxEm = agora;
  }
  return rostos.map((face, indice) => ({
    ...face,
    caixa: boxesSuaves[indice],
  }));
}

function renderLiveFrame() {
  if (!stream) {
    return;
  }
  const largura = (lastResult && lastResult.largura) || dom.video.videoWidth;
  const altura = (lastResult && lastResult.altura) || dom.video.videoHeight;
  if (largura && altura && dom.video.readyState >= 2 && !dom.scene.hidden) {
    const desatualizado = lastResult && Date.now() - lastResultAt > STALE_MS;
    const rostos = lastResult && !desatualizado ? lastResult.rostos : [];
    drawScene(dom.video, largura, altura, suavizarCaixas(rostos));
    if (desatualizado) {
      setStatus("Aguardando análise", "working");
    }
  }
  animationId = requestAnimationFrame(renderLiveFrame);
}

function captureFrame() {
  return new Promise((resolve) => {
    const larguraVideo = dom.video.videoWidth;
    const alturaVideo = dom.video.videoHeight;
    if (!larguraVideo || !alturaVideo) {
      resolve(null);
      return;
    }
    const escala = Math.min(
      1,
      CAPTURE_MAX / Math.max(larguraVideo, alturaVideo)
    );
    frameCanvas.width = Math.max(1, Math.round(larguraVideo * escala));
    frameCanvas.height = Math.max(1, Math.round(alturaVideo * escala));
    frameCtx.drawImage(dom.video, 0, 0, frameCanvas.width, frameCanvas.height);
    frameCanvas.toBlob(resolve, "image/jpeg", JPEG_QUALITY);
  });
}

function scheduleAnalysis(atraso = LIVE_INTERVAL) {
  clearTimeout(analysisTimer);
  if (mode !== "live" || !stream || document.hidden) {
    return;
  }
  analysisTimer = setTimeout(analyzeFrame, atraso);
}

async function analyzeFrame() {
  if (inFlight || mode !== "live" || !stream) {
    return;
  }
  if (!dom.video.videoWidth) {
    scheduleAnalysis();
    return;
  }

  inFlight = true;
  const meuController = new AbortController();
  controller = meuController;
  const timeout = setTimeout(() => meuController.abort(), 10000);
  let atraso = LIVE_INTERVAL;

  try {
    const blob = await captureFrame();
    if (!blob) {
      throw new Error("Quadro indisponível.");
    }
    const formulario = new FormData();
    formulario.append("foto", blob, "frame.jpg");
    const inicio = performance.now();
    const resposta = await fetch("/api/analisar", {
      method: "POST",
      body: formulario,
      signal: meuController.signal,
    });
    const dados = await resposta.json().catch(() => ({
      erro: "Falha ao analisar o quadro.",
    }));
    if (!resposta.ok) {
      throw new Error(dados.erro || "Falha ao analisar o quadro.");
    }
    if (!stream || mode !== "live" || meuController.signal.aborted) {
      return;
    }
    const latencia = performance.now() - inicio;
    lastResultAt = Date.now();
    lastResult = smoothFaces(dados);
    analysisTimes.push(lastResultAt);
    const taxa = currentRate();
    renderReadout(lastResult.rostos);
    updateTech({
      largura: lastResult.largura,
      altura: lastResult.altura,
      rostos: lastResult.rostos.length,
      latency: latencia,
      rate: taxa,
    });
    setStatus(
      lastResult.rostos.length ? "Câmera ativa" : "Nenhum rosto no quadro",
      "live"
    );
    clearError();
  } catch (error) {
    if (error && error.name === "AbortError") {
      // troca de modo, parada da câmera ou timeout: não é erro de interface
    } else {
      atraso = 1000;
      showError(
        error && error.name !== "TypeError"
          ? error.message
          : "Falha ao analisar. Verifique o terminal do servidor."
      );
      setStatus("Falha na análise", "error");
    }
  } finally {
    clearTimeout(timeout);
    if (controller === meuController) {
      controller = null;
      inFlight = false;
    }
    scheduleAnalysis(atraso);
  }
}

function resetPhoto({ fromMode = false } = {}) {
  if (photoController) {
    photoController.abort();
    photoController = null;
  }
  if (photoUrl) {
    URL.revokeObjectURL(photoUrl);
    photoUrl = null;
  }
  photoImage = null;
  photoView = null;
  dom.scene.hidden = true;
  clearScene();
  setLoading(false);
  hideBadge();
  dom.photoButton.textContent = "Escolher foto";
  dom.photoInput.value = "";
  updateTech({});
  if (!fromMode) {
    showDropzone();
    setStatus("Aguardando foto", "idle");
    renderReadoutEmpty(
      "Nenhuma foto analisada.",
      "Envie uma foto com um ou mais rostos."
    );
  }
}

function loadImage(url) {
  return new Promise((resolve, reject) => {
    const imagem = new Image();
    imagem.onload = () => resolve(imagem);
    imagem.onerror = () => reject(new Error("Não foi possível ler a imagem."));
    imagem.src = url;
  });
}

async function loadPhoto(arquivo) {
  if (!arquivo || mode !== "photo") {
    return;
  }
  clearError();
  const tipoValido =
    arquivo.type.startsWith("image/") ||
    /\.(jpe?g|png|webp|bmp)$/i.test(arquivo.name);
  if (!tipoValido) {
    showError("Use JPG, PNG ou WEBP.");
    setStatus("Arquivo inválido", "error");
    return;
  }
  if (arquivo.size > MAX_UPLOAD) {
    showError("A imagem passa de 32 MB.");
    setStatus("Arquivo inválido", "error");
    return;
  }

  if (photoController) {
    photoController.abort();
    photoController = null;
  }
  if (photoUrl) {
    URL.revokeObjectURL(photoUrl);
  }
  photoUrl = URL.createObjectURL(arquivo);
  try {
    photoImage = await loadImage(photoUrl);
  } catch (error) {
    showError(error.message);
    return;
  }

  showMedia();
  showBadge("photo");
  setLoading(true);
  setStatus("Analisando", "working");
  dom.photoButton.textContent = "Trocar foto";
  const previsualizacao = fitSize(
    photoImage.naturalWidth,
    photoImage.naturalHeight,
    1400
  );
  photoView = {
    largura: previsualizacao.largura,
    altura: previsualizacao.altura,
    rostos: [],
  };
  drawScene(
    photoImage,
    photoView.largura,
    photoView.altura,
    photoView.rostos
  );
  updateTech({
    largura: previsualizacao.largura,
    altura: previsualizacao.altura,
    rostos: null,
  });
  renderReadoutEmpty(
    "Analisando foto…",
    "A leitura aparece quando a análise terminar."
  );

  const meuController = new AbortController();
  photoController = meuController;
  const formulario = new FormData();
  formulario.append("foto", arquivo, arquivo.name);

  try {
    const resposta = await fetch("/api/analisar", {
      method: "POST",
      body: formulario,
      signal: meuController.signal,
    });
    const dados = await resposta.json().catch(() => ({
      erro: "Falha ao analisar a imagem.",
    }));
    if (!resposta.ok) {
      throw new Error(dados.erro || "Falha ao analisar a imagem.");
    }
    if (mode !== "photo" || meuController.signal.aborted) {
      return;
    }
    photoView = {
      largura: dados.largura,
      altura: dados.altura,
      rostos: dados.rostos,
    };
    drawScene(
      photoImage,
      photoView.largura,
      photoView.altura,
      photoView.rostos
    );
    renderReadout(dados.rostos, { tempo_ms: dados.tempo_ms });
    updateTech({
      largura: dados.largura,
      altura: dados.altura,
      rostos: dados.rostos.length,
      tempo_ms: dados.tempo_ms,
    });
    setStatus("Foto analisada", "idle");
  } catch (error) {
    if (error && error.name === "AbortError") {
      return;
    }
    showError(
      error && error.message
        ? error.message
        : "Falha ao analisar a imagem. Tente outra foto."
    );
    setStatus("Falha na análise", "error");
    renderReadoutEmpty("Falha na análise.", "Tente outra foto.");
  } finally {
    if (photoController === meuController) {
      photoController = null;
      setLoading(false);
    }
  }
}

function setMode(proximo) {
  if (proximo === mode) {
    return;
  }
  clearError();
  if (mode === "live") {
    stopCamera({ fromMode: true });
  } else {
    resetPhoto({ fromMode: true });
  }
  mode = proximo;
  document.documentElement.dataset.mode = mode;
  dom.modeLive.setAttribute("aria-pressed", String(mode === "live"));
  dom.modePhoto.setAttribute("aria-pressed", String(mode === "photo"));
  dom.cameraToggle.hidden = mode !== "live";
  dom.photoButton.hidden = mode !== "photo";
  dom.photoButton.textContent = "Escolher foto";
  setLoading(false);
  hideBadge();
  updateTech({});

  if (mode === "live") {
    showStageEmpty(
      "Ligue a câmera",
      "Inicie a câmera para reconhecer quem está no quadro."
    );
    renderReadoutEmpty(
      "Nenhuma leitura ainda.",
      "A identidade usa a CNN treinada; a emoção usa o modelo pesado."
    );
    setStatus("Câmera desligada", "idle");
  } else {
    showDropzone();
    renderReadoutEmpty(
      "Nenhuma foto analisada.",
      "Envie uma foto com um ou mais rostos."
    );
    setStatus("Aguardando foto", "idle");
  }
  dom.readoutFooter.textContent = footerText();
}

function init() {
  document.documentElement.dataset.mode = "live";
  dom.modeLive.setAttribute("aria-pressed", "true");
  dom.modePhoto.setAttribute("aria-pressed", "false");
  dom.cameraToggle.hidden = false;
  dom.photoButton.hidden = true;
  dom.scene.hidden = true;
  clearScene();
  showStageEmpty(
    "Ligue a câmera ou envie uma foto",
    "O reconhecimento roda localmente. Escolha uma entrada para começar."
  );
  renderReadoutEmpty(
    "Nenhuma leitura ainda.",
    "A identidade usa a CNN treinada; a emoção usa o modelo pesado."
  );
  setStatus("Câmera desligada", "idle");
  updateTech({});
  dom.readoutFooter.textContent = footerText();
}

dom.modeLive.addEventListener("click", () => setMode("live"));
dom.modePhoto.addEventListener("click", () => setMode("photo"));
dom.cameraToggle.addEventListener("click", () => {
  if (stream) {
    stopCamera();
  } else {
    startCamera();
  }
});
dom.photoButton.addEventListener("click", () => dom.photoInput.click());
dom.photoInput.addEventListener("change", (evento) => {
  const arquivo = evento.target.files && evento.target.files[0];
  evento.target.value = "";
  if (arquivo) {
    loadPhoto(arquivo);
  }
});
dom.errorClose.addEventListener("click", clearError);
dom.dropzone.addEventListener("click", () => dom.photoInput.click());
dom.dropzone.addEventListener("keydown", (evento) => {
  if (evento.key === "Enter" || evento.key === " ") {
    evento.preventDefault();
    dom.photoInput.click();
  }
});
for (const tipo of ["dragenter", "dragover"]) {
  dom.dropzone.addEventListener(tipo, (evento) => {
    evento.preventDefault();
    dom.dropzone.classList.add("is-drag");
  });
}
for (const tipo of ["dragleave", "drop"]) {
  dom.dropzone.addEventListener(tipo, (evento) => {
    evento.preventDefault();
    dom.dropzone.classList.remove("is-drag");
  });
}
dom.dropzone.addEventListener("drop", (evento) => {
  const arquivo = evento.dataTransfer.files && evento.dataTransfer.files[0];
  if (arquivo) {
    loadPhoto(arquivo);
  }
});

document.addEventListener("visibilitychange", () => {
  if (document.hidden) {
    clearTimeout(analysisTimer);
    analysisTimer = null;
    if (controller) {
      controller.abort();
    }
  } else if (mode === "live" && stream) {
    scheduleAnalysis();
  }
});

window.addEventListener("beforeunload", () => {
  if (stream) {
    stream.getTracks().forEach((track) => track.stop());
  }
  if (photoUrl) {
    URL.revokeObjectURL(photoUrl);
  }
});

if ("ResizeObserver" in window) {
  const observador = new ResizeObserver(() => {
    if (mode === "photo" && photoImage && photoView) {
      redrawPhoto();
    }
  });
  observador.observe(dom.stage);
}

init();

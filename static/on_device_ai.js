const STORAGE_KEY = "nova.ondevice_ai";
const TASKS_PACKAGE_URL = "https://cdn.jsdelivr.net/npm/@mediapipe/tasks-genai";
const TASKS_WASM_URL = "https://cdn.jsdelivr.net/npm/@mediapipe/tasks-genai/wasm";
const AUTO_RELEASE_DELAY_MS = 45000;

function clampInt(value, fallback, minimum, maximum) {
  const parsed = Number.parseInt(value, 10);
  if (Number.isNaN(parsed)) return fallback;
  return Math.max(minimum, Math.min(parsed, maximum));
}

function clampFloat(value, fallback, minimum, maximum) {
  const parsed = Number.parseFloat(value);
  if (Number.isNaN(parsed)) return fallback;
  return Math.max(minimum, Math.min(parsed, maximum));
}

export class OnDeviceAIClient {
  constructor() {
    this.filesetPromise = null;
    this.instance = null;
    this.loadingPromise = null;
    this.probePromise = null;
    this.invokeChain = Promise.resolve();
    this.invocationPromise = null;
    this.autoReleaseTimer = null;
    this.sourceSpec = null;
    this.loadedSource = null;
    this.loadedOptions = null;
    this.loadedLabel = "";
    this.loadedFile = null;
    this.preferences = this._readPreferences();
    this.probeResult = {
      webGpuAvailable: typeof navigator !== "undefined" && Boolean(navigator.gpu),
      adapterChecked: false,
      adapterAvailable: null,
      adapterName: "",
      message: "",
    };
    if (typeof document !== "undefined") {
      document.addEventListener("visibilitychange", () => {
        if (document.hidden) this.releaseModel({ keepSource: true });
      });
    }
    if (typeof window !== "undefined") {
      window.addEventListener("pagehide", () => this.releaseModel({ keepSource: true }));
    }
  }

  _readPreferences() {
    try {
      const payload = JSON.parse(localStorage.getItem(STORAGE_KEY) || "{}");
      return {
        model_url: String(payload.model_url || "").trim(),
        model_label: String(payload.model_label || "").trim(),
      };
    } catch (_error) {
      return { model_url: "", model_label: "" };
    }
  }

  _writePreferences() {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(this.preferences));
  }

  savePreferredUrl(url, label = "") {
    this.preferences = {
      model_url: String(url || "").trim(),
      model_label: String(label || "").trim(),
    };
    this._writePreferences();
  }

  clearPreferredUrl() {
    this.preferences = { model_url: "", model_label: "" };
    this._writePreferences();
  }

  normalizeGenerationOptions(options = {}) {
    return {
      maxTokens: clampInt(options.max_tokens ?? options.maxTokens, 2048, 256, 8192),
      topK: clampInt(options.top_k ?? options.topK, 40, 1, 100),
      temperature: clampFloat(options.temperature, 0.8, 0, 2),
      randomSeed: clampInt(options.random_seed ?? options.randomSeed, 1, 0, 2147483647),
    };
  }

  getPreferredUrl(serverAi = {}) {
    return this.preferences.model_url || String(serverAi.model_url || "").trim();
  }

  getPreferredLabel(serverAi = {}) {
    return this.preferences.model_label || String(serverAi.model_label || "").trim();
  }

  getStatus(serverAi = {}) {
    const sourceLabel = this.sourceSpec?.label || "";
    const sourceUrl = this.sourceSpec?.kind === "url" ? this.sourceSpec.url : "";
    return {
      loaded: Boolean(this.instance),
      loading: Boolean(this.loadingPromise),
      invoking: Boolean(this.invocationPromise),
      modelLabel: this.loadedLabel || sourceLabel || this.getPreferredLabel(serverAi),
      modelUrl: sourceUrl || this.getPreferredUrl(serverAi),
      loadedFromFile: Boolean(this.instance && this.loadedFile),
      requiresWebGpu: true,
      webGpuAvailable: Boolean(this.probeResult.webGpuAvailable),
      adapterChecked: Boolean(this.probeResult.adapterChecked),
      adapterAvailable: this.probeResult.adapterAvailable,
      adapterName: this.probeResult.adapterName || "",
      adapterMessage: this.probeResult.message || "",
    };
  }

  async probeEnvironment(force = false) {
    if (!force && this.probeResult.adapterChecked) return this.probeResult;
    if (this.probePromise) return this.probePromise;
    if (typeof navigator === "undefined" || !navigator.gpu) {
      this.probeResult = {
        webGpuAvailable: false,
        adapterChecked: true,
        adapterAvailable: false,
        adapterName: "",
        message: "WebGPU ist in diesem Browser nicht verfuegbar. Die lokale KI kann hier nicht gestartet werden.",
      };
      return this.probeResult;
    }
    this.probePromise = (async () => {
      try {
        const adapter = await navigator.gpu.requestAdapter();
        if (!adapter) {
          this.probeResult = {
            webGpuAvailable: true,
            adapterChecked: true,
            adapterAvailable: false,
            adapterName: "",
            message: "WebGPU wurde erkannt, aber Chromium liefert keinen nutzbaren GPU-Adapter. Pruefe Hardwarebeschleunigung, chrome://gpu oder edge://gpu, aktiviere bei Bedarf enable-unsafe-webgpu und ignore-gpu-blocklist, und auf Windows-Laptops optional force-high-performance-gpu.",
          };
          return this.probeResult;
        }
        let adapterName = "";
        try {
          adapterName = String(adapter.info?.description || adapter.info?.vendor || "").trim();
        } catch (_error) {
          adapterName = "";
        }
        this.probeResult = {
          webGpuAvailable: true,
          adapterChecked: true,
          adapterAvailable: true,
          adapterName,
          message: "",
        };
        return this.probeResult;
      } catch (error) {
        const rawMessage = error instanceof Error ? error.message : String(error || "Unbekannter WebGPU-Fehler.");
        this.probeResult = {
          webGpuAvailable: true,
          adapterChecked: true,
          adapterAvailable: false,
          adapterName: "",
          message: `WebGPU wurde erkannt, aber der Adapter-Test ist fehlgeschlagen: ${rawMessage}`,
        };
        return this.probeResult;
      } finally {
        this.probePromise = null;
      }
    })();
    return this.probePromise;
  }

  async _ensureFileset() {
    if (!this.filesetPromise) {
      this.filesetPromise = import(TASKS_PACKAGE_URL).then(({ FilesetResolver }) => FilesetResolver.forGenAiTasks(TASKS_WASM_URL));
    }
    return this.filesetPromise;
  }

  _clearAutoReleaseTimer() {
    if (this.autoReleaseTimer) {
      clearTimeout(this.autoReleaseTimer);
      this.autoReleaseTimer = null;
    }
  }

  _scheduleAutoRelease() {
    this._clearAutoReleaseTimer();
    if (!this.instance) return;
    this.autoReleaseTimer = setTimeout(() => {
      this.autoReleaseTimer = null;
      if (this.invocationPromise || this.loadingPromise) return;
      this.releaseModel({ keepSource: true });
    }, AUTO_RELEASE_DELAY_MS);
  }

  _sameSource(source, options) {
    return this.instance
      && this.loadedSource === source.key
      && JSON.stringify(this.loadedOptions || {}) === JSON.stringify(options || {});
  }

  async loadFromUrl(url, generationOptions = {}, label = "") {
    const modelUrl = String(url || "").trim();
    if (!modelUrl) throw new Error("Bitte zuerst eine Modell-URL angeben.");
    this._clearAutoReleaseTimer();
    const options = this.normalizeGenerationOptions(generationOptions);
    const source = { key: `url:${modelUrl}`, label: String(label || modelUrl).trim() };
    if (this._sameSource(source, options)) return this.getStatus({ model_url: modelUrl, model_label: source.label });
    if (this.loadingPromise) return this.loadingPromise;
    if (this.invocationPromise) throw new Error("Das Modell verarbeitet gerade noch eine Anfrage. Bitte warten, bevor ein anderes Modell geladen wird.");
    const current = this._loadInstance({ baseOptions: { modelAssetPath: modelUrl }, ...options }, source, null);
    this.loadingPromise = current;
    return current.finally(() => {
      if (this.loadingPromise === current) this.loadingPromise = null;
    });
  }

  async loadFromFile(file, generationOptions = {}, label = "") {
    if (!file) throw new Error("Bitte zuerst eine Modelldatei auswaehlen.");
    this._clearAutoReleaseTimer();
    const options = this.normalizeGenerationOptions(generationOptions);
    const source = { key: `file:${file.name}:${file.size}:${file.lastModified}`, label: String(label || file.name).trim() };
    if (this._sameSource(source, options)) return this.getStatus({ model_label: source.label });
    if (this.loadingPromise) return this.loadingPromise;
    if (this.invocationPromise) throw new Error("Das Modell verarbeitet gerade noch eine Anfrage. Bitte warten, bevor eine andere Modelldatei geladen wird.");
    const modelBytes = new Uint8Array(await file.arrayBuffer());
    const current = this._loadInstance({ baseOptions: { modelAssetBuffer: modelBytes }, ...options }, source, file);
    this.loadingPromise = current;
    return current.finally(() => {
      if (this.loadingPromise === current) this.loadingPromise = null;
    });
  }

  async _loadInstance(options, source, file) {
    const probe = await this.probeEnvironment(true);
    if (!probe.webGpuAvailable) {
      throw new Error("WebGPU ist in diesem Browser nicht verfuegbar. Fuer MediaPipe LLM Inference wird WebGPU benoetigt.");
    }
    if (probe.adapterAvailable === false) {
      throw new Error(probe.message || "WebGPU wurde erkannt, aber kein GPU-Adapter konnte initialisiert werden.");
    }
    try {
      const fileset = await this._ensureFileset();
      const { LlmInference } = await import(TASKS_PACKAGE_URL);
      const instance = await LlmInference.createFromOptions(fileset, options);
      this.instance = instance;
      this.loadedSource = source.key;
      this.loadedOptions = this.normalizeGenerationOptions(options);
      this.loadedLabel = source.label;
      this.loadedFile = file;
      this.sourceSpec = file
        ? { kind: "file", file, label: source.label, options: this.loadedOptions }
        : { kind: "url", url: source.key.replace(/^url:/, ""), label: source.label, options: this.loadedOptions };
      this._scheduleAutoRelease();
      return this.getStatus({ model_label: this.loadedLabel });
    } catch (error) {
      const rawMessage = error instanceof Error ? error.message : String(error || "");
      if (/No model format matched/i.test(rawMessage)) {
        throw new Error(
          `Das geladene Modell ist nicht im erwarteten Web-Format. Fuer Chromium + MediaPipe nutze ein Web-Modell wie ` +
          `gemma3-1b-it-int4-web.task oder ein allgemeines .litertlm-Webmodell, nicht ${source.label || "dieses Modell"}.`,
        );
      }
      if (/Unable to request adapter from navigator\.gpu/i.test(rawMessage)) {
        this.probeResult = {
          webGpuAvailable: true,
          adapterChecked: true,
          adapterAvailable: false,
          adapterName: "",
          message: "WebGPU wurde erkannt, aber Chromium konnte keinen GPU-Adapter bereitstellen. Pruefe Hardwarebeschleunigung, chrome://gpu oder edge://gpu, und aktiviere bei Bedarf enable-unsafe-webgpu, ignore-gpu-blocklist oder force-high-performance-gpu.",
        };
        throw new Error(this.probeResult.message);
      }
      throw error;
    }
  }

  releaseModel({ keepSource = true } = {}) {
    this._clearAutoReleaseTimer();
    try {
      this.instance?.cancelProcessing?.();
    } catch (_error) {
      // ignore cancellation races
    }
    try {
      this.instance?.close?.();
    } catch (_error) {
      // ignore cleanup races
    }
    this.instance = null;
    this.loadingPromise = null;
    this.loadedSource = null;
    this.loadedOptions = null;
    if (!keepSource) {
      this.sourceSpec = null;
      this.loadedLabel = "";
      this.loadedFile = null;
      return;
    }
    this.loadedFile = this.sourceSpec?.kind === "file" ? this.sourceSpec.file : null;
  }

  unload() {
    this.releaseModel({ keepSource: true });
  }

  async ensureReady(serverAi = {}) {
    if (this.instance) return this.getStatus(serverAi);
    if (this.loadingPromise) return this.loadingPromise;
    if (this.sourceSpec?.kind === "file" && this.sourceSpec.file) {
      return this.loadFromFile(this.sourceSpec.file, this.sourceSpec.options || {}, this.sourceSpec.label || this.sourceSpec.file.name);
    }
    if (this.sourceSpec?.kind === "url" && this.sourceSpec.url) {
      return this.loadFromUrl(this.sourceSpec.url, this.sourceSpec.options || {}, this.sourceSpec.label || this.sourceSpec.url);
    }
    const url = this.getPreferredUrl(serverAi);
    if (url) {
      return this.loadFromUrl(url, serverAi.generation_options || {}, this.getPreferredLabel(serverAi));
    }
    throw new Error("Kein On-Device-Modell geladen. Bitte Modell-URL konfigurieren oder eine lokale .task/.litertlm-Datei laden.");
  }

  promptEnvelope(prompt, systemPrompt = "") {
    const userPrompt = String(prompt || "").trim();
    const systemText = String(systemPrompt || "").trim();
    if (!systemText) {
      return `<start_of_turn>user\n${userPrompt}<end_of_turn>\n<start_of_turn>model\n`;
    }
    return [
      "<start_of_turn>system",
      systemText,
      "<end_of_turn>",
      "<start_of_turn>user",
      userPrompt,
      "<end_of_turn>",
      "<start_of_turn>model",
      "",
    ].join("\n");
  }

  async _generateWithLoadedInstance(
    prompt,
    {
      systemPrompt = "",
      serverAi = {},
      onPartial = null,
      idleTimeoutMs = 0,
      acceptPartialOnTimeout = false,
    } = {},
  ) {
    const instance = this.instance;
    const query = this.promptEnvelope(prompt, systemPrompt);
    return new Promise((resolve, reject) => {
      let output = "";
      let settled = false;
      let idleTimer = null;
      const clearIdleTimer = () => {
        if (idleTimer) {
          clearTimeout(idleTimer);
          idleTimer = null;
        }
      };
      const finish = (fn, value) => {
        if (settled) return;
        settled = true;
        clearIdleTimer();
        fn(value);
      };
      const scheduleIdleTimer = () => {
        clearIdleTimer();
        if (!idleTimeoutMs) return;
        idleTimer = setTimeout(() => {
          try {
            instance.cancelProcessing?.();
          } catch (_error) {
            // ignore cancellation races
          }
          const text = output.trim();
          if (acceptPartialOnTimeout && text) {
            finish(resolve, {
              text,
              model: this.loadedLabel || this.getPreferredLabel(serverAi) || "",
            });
            return;
          }
          finish(reject, new Error("On-Device-KI hat zu lange ohne vollstaendige Antwort gebraucht."));
        }, idleTimeoutMs);
      };
      scheduleIdleTimer();
      try {
        instance.generateResponse(query, (partialResults, complete) => {
          if (settled) return;
          if (partialResults) output += partialResults;
          if (partialResults && typeof onPartial === "function") {
            try {
              onPartial(output);
            } catch (_error) {
              // ignore UI callback failures
            }
          }
          if (partialResults) scheduleIdleTimer();
          if (complete) {
            finish(resolve, {
              text: output || "Result is empty",
              model: this.loadedLabel || this.getPreferredLabel(serverAi) || "",
            });
          }
        });
      } catch (error) {
        const rawMessage = error instanceof Error ? error.message : String(error || "");
        if (/Previous invocation or loading is still ongoing/i.test(rawMessage)) {
          finish(reject, new Error("Das On-Device-Modell ist noch beschaeftigt. Bitte warte auf den laufenden Vorgang und sende die Anfrage dann erneut."));
          return;
        }
        finish(reject, error);
      }
    });
  }

  async generate(prompt, { systemPrompt = "", serverAi = {}, onPartial = null, idleTimeoutMs = 0, acceptPartialOnTimeout = false } = {}) {
    this._clearAutoReleaseTimer();
    await this.ensureReady(serverAi);
    const previous = this.invokeChain.catch(() => null);
    const current = previous.then(() => this._generateWithLoadedInstance(
      prompt,
      { systemPrompt, serverAi, onPartial, idleTimeoutMs, acceptPartialOnTimeout },
    ));
    const managed = current.finally(() => {
      if (this.invocationPromise === managed) this.invocationPromise = null;
      this._scheduleAutoRelease();
    });
    this.invokeChain = managed.catch(() => null);
    this.invocationPromise = managed;
    return managed;
  }
}

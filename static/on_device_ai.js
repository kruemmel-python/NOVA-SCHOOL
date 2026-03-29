const LEGACY_ERROR =
  "Der alte Browser-On-Device-AI-Pfad wurde entfernt. NOVA SCHOOL nutzt jetzt den lokalen KI-Server mit LiteRT-LM oder llama.cpp und laedt keine Browser-Modelle mehr ueber externe CDNs.";

function unsupported() {
  throw new Error(LEGACY_ERROR);
}

export class OnDeviceAIClient {
  constructor() {
    this.preferences = { model_url: "", model_label: "" };
  }

  normalizeGenerationOptions(options = {}) {
    return { ...options };
  }

  getPreferredUrl() {
    return "";
  }

  getPreferredLabel() {
    return "";
  }

  getStatus() {
    return {
      loaded: false,
      loading: false,
      invoking: false,
      modelLabel: "",
      modelUrl: "",
      loadedFromFile: false,
      requiresWebGpu: false,
      webGpuAvailable: false,
      adapterChecked: true,
      adapterAvailable: false,
      adapterName: "",
      adapterMessage: LEGACY_ERROR,
    };
  }

  savePreferredUrl(_url, _label = "") {}

  clearPreferredUrl() {}

  async probeEnvironment() {
    return this.getStatus();
  }

  async loadFromUrl() {
    unsupported();
  }

  async loadFromFile() {
    unsupported();
  }

  releaseModel() {}

  unload() {}

  async ensureReady() {
    unsupported();
  }

  promptEnvelope(prompt, systemPrompt = "") {
    return [systemPrompt, prompt].filter(Boolean).join("\n\n");
  }

  async generate() {
    unsupported();
  }
}

export default OnDeviceAIClient;

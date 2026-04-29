import { useState, useRef, useCallback } from "react";
import "./ResumeOptimizer.css";

const API_BASE = "http://localhost:8000";

// ─── Step Indicator ───────────────────────────────────────────────────────────
function StepIndicator({ current }) {
  const steps = ["Upload", "Configure", "Results"];
  return (
    <div className="ro-steps">
      {steps.map((label, i) => {
        const n = i + 1;
        const state = n < current ? "done" : n === current ? "active" : "idle";
        return (
          <div key={label} className="ro-step-row">
            <div className={`ro-step ${state}`}>
              <div className="ro-step-num">{state === "done" ? "✓" : n}</div>
              <span>{label}</span>
            </div>
            {i < steps.length - 1 && <div className="ro-step-divider" />}
          </div>
        );
      })}
    </div>
  );
}

// ─── Upload Panel ─────────────────────────────────────────────────────────────
function UploadPanel({ onNext }) {
  const [file, setFile] = useState(null);
  const [dragging, setDragging] = useState(false);
  const inputRef = useRef();

  const handleFile = (f) => {
    if (!f) return;
    if (f.type !== "application/pdf") {
      alert("Please upload a PDF file.");
      return;
    }
    if (f.size > 10 * 1024 * 1024) {
      alert("File must be under 10 MB.");
      return;
    }
    setFile(f);
  };

  const onDrop = useCallback((e) => {
    e.preventDefault();
    setDragging(false);
    handleFile(e.dataTransfer.files[0]);
  }, []);

  const removeFile = (e) => {
    e.stopPropagation();
    setFile(null);
    if (inputRef.current) inputRef.current.value = "";
  };

  return (
    <div className="ro-panel">
      <div className="ro-card">
        <div className="ro-card-label">Your resume</div>
        <div
          className={`ro-upload-zone ${dragging ? "drag" : ""} ${file ? "has-file" : ""}`}
          onClick={() => !file && inputRef.current?.click()}
          onDrop={onDrop}
          onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
          onDragLeave={() => setDragging(false)}
        >
          <input
            type="file"
            accept=".pdf"
            ref={inputRef}
            style={{ display: "none" }}
            onChange={(e) => handleFile(e.target.files[0])}
          />
          {file ? (
            <div className="ro-file-info">
              <span className="ro-file-icon">📄</span>
              <div>
                <div className="ro-file-name">{file.name}</div>
                <div className="ro-file-size">{(file.size / 1024).toFixed(0)} KB · PDF</div>
              </div>
              <button className="ro-remove-btn" onClick={removeFile}>✕</button>
            </div>
          ) : (
            <>
              <span className="ro-upload-icon">⬆</span>
              <div className="ro-upload-title">Drop your PDF here</div>
              <div className="ro-upload-sub">or click to browse — PDF only, max 10 MB</div>
            </>
          )}
        </div>
      </div>
      <button className="ro-btn primary" disabled={!file} onClick={() => onNext(file)}>
        Continue →
      </button>
    </div>
  );
}

// ─── Configure Panel ──────────────────────────────────────────────────────────
function ConfigurePanel({ onBack, onOptimize }) {
  const [jd, setJd] = useState("");
  const [opts, setOpts] = useState({ ats: true, impact: true, clarity: false, format: false });
  const [fmt, setFmt] = useState("pdf");
  const toggleOpt = (key) => setOpts((o) => ({ ...o, [key]: !o[key] }));

  const optimizeOptions = [
    { key: "ats",     icon: "🎯", label: "ATS keywords" },
    { key: "impact",  icon: "📈", label: "Impact metrics" },
    { key: "clarity", icon: "✏️",  label: "Clarity & tone" },
    { key: "format",  icon: "📐", label: "Formatting" },
  ];

  return (
    <div className="ro-panel">
      <div className="ro-card">
        <div className="ro-card-label">
          Job description <span className="ro-optional">(optional but recommended)</span>
        </div>
        <textarea
          className="ro-textarea"
          rows={5}
          placeholder="Paste the full job description here — Claude will tailor your resume's keywords, tone, and structure to match this specific role..."
          value={jd}
          onChange={(e) => setJd(e.target.value)}
        />
      </div>

      <div className="ro-card">
        <div className="ro-card-label">Optimization focus</div>
        <div className="ro-options-grid">
          {optimizeOptions.map(({ key, icon, label }) => (
            <button
              key={key}
              className={`ro-option-btn ${opts[key] ? "selected" : ""}`}
              onClick={() => toggleOpt(key)}
            >
              <span className="ro-opt-icon">{icon}</span>{label}
            </button>
          ))}
        </div>
      </div>

      <div className="ro-card">
        <div className="ro-card-label">Output format</div>
        <div className="ro-options-grid">
          {[{ key: "pdf", icon: "📄", label: "Download PDF" },
            { key: "text", icon: "📋", label: "Copy text" }].map(({ key, icon, label }) => (
            <button
              key={key}
              className={`ro-option-btn ${fmt === key ? "selected" : ""}`}
              onClick={() => setFmt(key)}
            >
              <span className="ro-opt-icon">{icon}</span>{label}
            </button>
          ))}
        </div>
      </div>

      <div className="ro-action-row">
        <button className="ro-btn secondary" onClick={onBack}>← Back</button>
        <button className="ro-btn primary" onClick={() => onOptimize({ jd, opts, fmt })}>
          Optimize with AI →
        </button>
      </div>
    </div>
  );
}

// ─── Processing Panel ─────────────────────────────────────────────────────────
function ProcessingPanel({ progress, message }) {
  return (
    <div className="ro-panel">
      <div className="ro-card">
        <div className="ro-processing-label">{message}</div>
        <div className="ro-progress-bar">
          <div className="ro-progress-fill" style={{ width: `${progress}%` }} />
        </div>
        <div className="ro-progress-pct">{progress}%</div>
        <div className="ro-processing-note">
          Claude is reading and rewriting your resume. This takes 15–30 seconds.
        </div>
      </div>
    </div>
  );
}

// ─── Results Panel ────────────────────────────────────────────────────────────
function ResultsPanel({ result, onReset, onDownload, onCopyText }) {
  const [tab, setTab] = useState("changes");
  const [copied, setCopied] = useState(false);
  const scoreGain = result.score - result.old_score;

  const handleCopy = () => {
    navigator.clipboard.writeText(result.full_text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const tabs = [
    { key: "changes", label: "Key changes" },
    { key: "full",    label: "Full resume" },
    { key: "tips",    label: "Tips" },
  ];

  return (
    <div className="ro-panel">
      {/* Score card */}
      <div className="ro-card">
        <div className="ro-score-row">
          <div className="ro-score-num">{result.score}</div>
          <div className="ro-score-detail">
            <div className="ro-score-title">ATS match score</div>
            <div className="ro-score-sub">
              Improved from <strong>{result.old_score}</strong>
            </div>
            <div className="ro-sub-bar">
              <div className="ro-sub-fill" style={{ width: `${result.score}%` }} />
            </div>
          </div>
          <span className="ro-badge success">+{scoreGain} pts</span>
        </div>
        <div className="ro-badge-row">
          <span className="ro-badge success">{result.changes.length} sections improved</span>
          <span className="ro-badge info">{result.tips.length} tips added</span>
          <span className="ro-badge warn">Claude AI enhanced</span>
        </div>
      </div>

      {/* Tabs */}
      <div className="ro-card">
        <div className="ro-tabs">
          {tabs.map(({ key, label }) => (
            <button
              key={key}
              className={`ro-tab ${tab === key ? "active" : ""}`}
              onClick={() => setTab(key)}
            >
              {label}
            </button>
          ))}
        </div>

        {tab === "changes" && (
          <div className="ro-tab-content">
            {result.changes.length === 0 && (
              <p className="ro-preview-note">No specific changes reported.</p>
            )}
            {result.changes.map((c, i) => (
              <div key={i} className="ro-result-block">
                <div className="ro-block-label">{c.section} ✓</div>
                <div className="ro-block-old">{c.old}</div>
                <div className="ro-block-new">{c.new}</div>
              </div>
            ))}
          </div>
        )}

        {tab === "full" && (
          <div className="ro-tab-content">
            <p className="ro-preview-note">
              Full enhanced resume text — download PDF for the formatted version.
            </p>
            <pre className="ro-preview-text">{result.full_text}</pre>
          </div>
        )}

        {tab === "tips" && (
          <div className="ro-tab-content">
            {result.tips.map((t, i) => (
              <div key={i} className="ro-result-block">
                <div className="ro-block-label">{t.title}</div>
                <div className="ro-tip-body">{t.body}</div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Actions */}
      <div className="ro-action-row">
        <button className="ro-btn secondary" onClick={onReset}>Start over</button>
        <button className="ro-btn secondary" onClick={handleCopy}>
          {copied ? "Copied! ✓" : "Copy text"}
        </button>
        <button className="ro-btn primary" onClick={onDownload}>
          Download PDF ↓
        </button>
      </div>
    </div>
  );
}

// ─── Main Component ───────────────────────────────────────────────────────────
const PROGRESS_MESSAGES = [
  "Uploading your resume...",
  "Extracting text from PDF...",
  "Claude is reading your resume...",
  "Optimizing keywords and phrasing...",
  "Adding impact metrics...",
  "Generating enhanced PDF...",
];

export default function ResumeOptimizer() {
  const [step, setStep]       = useState(1);
  const [file, setFile]       = useState(null);
  const [progress, setProgress] = useState(0);
  const [progMsg, setProgMsg] = useState(PROGRESS_MESSAGES[0]);
  const [result, setResult]   = useState(null);
  const [error, setError]     = useState(null);

  const handleUploadNext = (f) => { setFile(f); setStep(2); };

  const handleOptimize = async (cfg) => {
    setError(null);
    setStep("processing");
    setProgress(0);

    // Animate progress while waiting for API
    let msgIdx = 0;
    const ticker = setInterval(() => {
      msgIdx = Math.min(msgIdx + 1, PROGRESS_MESSAGES.length - 1);
      setProgMsg(PROGRESS_MESSAGES[msgIdx]);
      setProgress((p) => Math.min(p + 12, 85)); // cap at 85% until real response
    }, 3000);

    try {
      const formData = new FormData();
      formData.append("resume", file);
      formData.append("job_description", cfg.jd);
      formData.append("options", JSON.stringify(cfg.opts));

      const res = await fetch(`${API_BASE}/api/optimize`, {
        method: "POST",
        body: formData,
      });

      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "Server error");
      }

      const data = await res.json();
      clearInterval(ticker);
      setProgress(100);
      setProgMsg("Done!");

      setTimeout(() => {
        setResult(data);
        setStep(3);
      }, 400);

    } catch (e) {
      clearInterval(ticker);
      setError(e.message);
      setStep(2);
    }
  };

  const handleDownload = () => {
    if (!result?.file_id) return;
    window.open(`${API_BASE}/api/download/${result.file_id}`, "_blank");
  };

  const handleReset = () => {
    setStep(1); setFile(null); setResult(null); setError(null); setProgress(0);
  };

  const currentStep = step === "processing" ? 2 : step;

  return (
    <div className="ro-root">
      <div className="ro-container">
        <div className="ro-header">
          <h1 className="ro-title">Resume optimizer</h1>
          <p className="ro-subtitle">
            Upload your PDF, add a job description, get an AI-enhanced resume back.
          </p>
        </div>

        <StepIndicator current={currentStep} />

        {error && (
          <div className="ro-error-banner">
            ⚠ {error}
          </div>
        )}

        {step === 1 && <UploadPanel onNext={handleUploadNext} />}
        {step === 2 && (
          <ConfigurePanel onBack={() => setStep(1)} onOptimize={handleOptimize} />
        )}
        {step === "processing" && (
          <ProcessingPanel progress={progress} message={progMsg} />
        )}
        {step === 3 && result && (
          <ResultsPanel
            result={result}
            onReset={handleReset}
            onDownload={handleDownload}
          />
        )}
      </div>
    </div>
  );
}

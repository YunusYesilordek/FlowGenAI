import { useState } from 'react';

/**
 * DiagramView — Displays generated PlantUML / D2 diagrams
 * with image preview and copyable source code.
 */
export default function DiagramView({ data }) {
  const [activeTab, setActiveTab] = useState('plantuml');
  const [copied, setCopied] = useState(false);
  const [codeVisible, setCodeVisible] = useState(false);

  if (!data) return null;

  const tabs = [
    { id: 'plantuml', label: 'PlantUML', url: data.plantuml_url, code: data.plantuml_code },
    { id: 'd2', label: 'D2 (Kroki)', url: data.d2_url, code: data.d2_code },
  ];

  const current = tabs.find((t) => t.id === activeTab);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(current.code);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      /* fallback: select text */
    }
  };

  const handleDownload = () => {
    const link = document.createElement('a');
    link.href = current.url;
    link.download = `flowgenai-${activeTab}-diagram.${activeTab === 'plantuml' ? 'png' : 'svg'}`;
    link.target = '_blank';
    link.click();
  };

  return (
    <div className="diagram-container">
      {/* Toolbar */}
      <div className="diagram-toolbar">
        <div className="tab-group">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              className={activeTab === tab.id ? 'active' : ''}
              onClick={() => { setActiveTab(tab.id); setCopied(false); }}
            >
              {tab.label}
            </button>
          ))}
        </div>

        <div className="spacer" />

        <button
          className="btn btn-secondary btn-icon"
          onClick={() => setCodeVisible(!codeVisible)}
          title={codeVisible ? 'Hide code' : 'Show code'}
        >
          {codeVisible ? '◀' : '▶'}
        </button>

        <button
          className="btn btn-secondary"
          onClick={handleDownload}
          title="Download diagram"
        >
          ⬇ Download
        </button>
      </div>

      {/* Body */}
      <div className="diagram-body">
        {/* Image */}
        <div className="diagram-image-wrapper">
          <img
            src={current.url}
            alt={`${current.label} diagram`}
            loading="lazy"
          />
        </div>

        {/* Code Panel */}
        {codeVisible && (
          <div className="diagram-code-panel animate-slide-right">
            <div className="diagram-code-header">
              <span>Source Code</span>
              <button className="btn btn-secondary" onClick={handleCopy}>
                {copied ? (
                  <span className="copy-feedback">✓ Copied</span>
                ) : (
                  '📋 Copy'
                )}
              </button>
            </div>
            <pre className="code-block">{current.code}</pre>
          </div>
        )}
      </div>
    </div>
  );
}

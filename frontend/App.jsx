import { useState } from 'react';
import './App.css';
import Header from './Header';
import RequirementInput from './RequirementInput';
import AnalysisResults from './AnalysisResults';
import DiagramView from './DiagramView';
import { analyzeRequirement, generateDiagram } from './api';

/**
 * App — Main application shell.
 *
 * Horizontal layout:
 *   Left panel  → Requirement input (fixed width)
 *   Right panel → Analysis results OR Diagram view (fluid)
 */
export default function App() {
  /* ── State ──────────────────────────────────────────────────────────── */
  const [requirement, setRequirement] = useState('');
  const [analysisData, setAnalysisData] = useState(null);
  const [diagramData, setDiagramData] = useState(null);
  const [activeView, setActiveView] = useState('empty'); // 'empty' | 'analysis' | 'diagram'
  const [analyzeLoading, setAnalyzeLoading] = useState(false);
  const [diagramLoading, setDiagramLoading] = useState(false);
  const [error, setError] = useState(null);

  /* ── Handlers ───────────────────────────────────────────────────────── */

  const handleAnalyze = async () => {
    if (!requirement.trim()) return;

    setError(null);
    setAnalyzeLoading(true);
    setDiagramData(null);

    try {
      const data = await analyzeRequirement(requirement);
      setAnalysisData(data);
      setActiveView('analysis');
    } catch (err) {
      setError(err.message);
    } finally {
      setAnalyzeLoading(false);
    }
  };

  const handleGenerateDiagram = async () => {
    if (!analysisData) return;

    setError(null);
    setDiagramLoading(true);

    try {
      const data = await generateDiagram(analysisData);
      setDiagramData(data);
      setActiveView('diagram');
    } catch (err) {
      setError(err.message);
    } finally {
      setDiagramLoading(false);
    }
  };

  /* ── Right Panel Content ────────────────────────────────────────────── */

  const renderRightPanel = () => {
    // Loading states
    if (analyzeLoading) {
      return (
        <div className="loading-overlay">
          <div className="spinner spinner-large" />
          <span>Analyzing requirement with AI...</span>
        </div>
      );
    }

    // Diagram view
    if (activeView === 'diagram' && diagramData) {
      return <DiagramView data={diagramData} />;
    }

    // Analysis results
    if (activeView === 'analysis' && analysisData) {
      return (
        <>
          {/* Tab bar for switching between analysis and diagram */}
          <div className="tab-bar">
            <button
              className={`tab-btn ${activeView === 'analysis' ? 'active' : ''}`}
              onClick={() => setActiveView('analysis')}
            >
              📊 Analysis
            </button>
            {diagramData && (
              <button
                className={`tab-btn ${activeView === 'diagram' ? 'active' : ''}`}
                onClick={() => setActiveView('diagram')}
              >
                🗺️ Diagrams
              </button>
            )}
          </div>
          <AnalysisResults
            data={analysisData}
            onGenerateDiagram={handleGenerateDiagram}
            loading={diagramLoading}
          />
        </>
      );
    }

    // Empty state
    return (
      <div className="empty-state">
        <div className="empty-state-icon">🗺️</div>
        <h3>No Analysis Yet</h3>
        <p>
          Enter a business requirement on the left and click
          <strong> Analyze Requirement</strong> to generate structured use case
          data and UML diagrams.
        </p>
      </div>
    );
  };

  /* ── Render ─────────────────────────────────────────────────────────── */

  return (
    <>
      <Header />

      <main className="app-main">
        {/* Left Panel — Input */}
        <RequirementInput
          value={requirement}
          onChange={setRequirement}
          onAnalyze={handleAnalyze}
          loading={analyzeLoading}
          disabled={diagramLoading}
        />

        {/* Right Panel — Results / Diagram */}
        <div className="panel-right">
          {/* Error Banner */}
          {error && (
            <div className="error-banner">
              <span>⚠️ {error}</span>
              <button onClick={() => setError(null)}>✕</button>
            </div>
          )}

          {renderRightPanel()}
        </div>
      </main>
    </>
  );
}

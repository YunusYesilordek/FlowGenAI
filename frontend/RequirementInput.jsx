/**
 * RequirementInput — Left panel with textarea and analyze button
 */
export default function RequirementInput({
  value,
  onChange,
  onAnalyze,
  loading,
  disabled,
}) {
  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) {
      onAnalyze();
    }
  };

  return (
    <div className="panel-left">
      <div className="panel-header">
        <h2>
          <span className="icon">📋</span>
          Requirement
        </h2>
        <p>Describe your business requirement below.</p>
      </div>

      <div className="panel-body">
        <div className="textarea-wrapper">
          <textarea
            id="requirement-input"
            className="textarea-field"
            placeholder="e.g. An online appointment booking system where customers can schedule, reschedule, and cancel appointments with service providers..."
            value={value}
            onChange={(e) => onChange(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={loading}
          />
          <div className="char-count">{value.length} characters</div>
        </div>

        <button
          id="analyze-btn"
          className="btn btn-primary btn-full"
          onClick={onAnalyze}
          disabled={loading || !value.trim() || disabled}
        >
          {loading ? (
            <>
              <span className="spinner" />
              Analyzing...
            </>
          ) : (
            <>
              🔍 Analyze Requirement
            </>
          )}
        </button>
      </div>
    </div>
  );
}

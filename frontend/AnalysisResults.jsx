/**
 * AnalysisResults — Displays structured use case analysis data
 */

const ACTOR_BADGE_CLASS = {
  primary: 'badge-primary',
  secondary: 'badge-secondary',
  external_system: 'badge-external',
};

const ACTOR_TYPE_LABEL = {
  primary: 'Primary',
  secondary: 'Secondary',
  external_system: 'External System',
};

const FLOW_BADGE_CLASS = {
  alternate: 'badge-alternate',
  exception: 'badge-exception',
  extension: 'badge-extension',
};

export default function AnalysisResults({ data, onGenerateDiagram, loading }) {
  if (!data) return null;

  const { actors, trigger, alternate_flows, relationships, suggested_scenarios } = data;

  return (
    <div className="tab-content animate-fade-in">
      {/* Actors */}
      <div className="analysis-section" style={{ animationDelay: '0ms' }}>
        <div className="section-title">
          <span className="icon">👤</span>
          Actors ({actors?.length || 0})
        </div>
        {actors?.map((actor, i) => (
          <div key={i} className="card actor-card">
            <div className="actor-card-header">
              <span className={`badge ${ACTOR_BADGE_CLASS[actor.type] || 'badge-primary'}`}>
                {ACTOR_TYPE_LABEL[actor.type] || actor.type}
              </span>
              <span className="actor-name">{actor.name}</span>
            </div>
            <div className="actor-use-cases">
              {actor.use_cases?.map((uc, j) => (
                <span key={j} className="chip">{uc}</span>
              ))}
            </div>
          </div>
        ))}
      </div>

      {/* Trigger */}
      {trigger && (
        <div className="analysis-section" style={{ animationDelay: '50ms' }}>
          <div className="section-title">
            <span className="icon">⚡</span>
            Trigger
          </div>
          <div className="card trigger-card">
            <span className="trigger-icon">🎯</span>
            <span className="trigger-text">{trigger}</span>
          </div>
        </div>
      )}

      {/* Alternate Flows */}
      {alternate_flows?.length > 0 && (
        <div className="analysis-section" style={{ animationDelay: '100ms' }}>
          <div className="section-title">
            <span className="icon">🔀</span>
            Alternate Flows ({alternate_flows.length})
          </div>
          {alternate_flows.map((flow, i) => (
            <div key={i} className="card alt-flow-card">
              <div className="alt-flow-header">
                <span className={`badge ${FLOW_BADGE_CLASS[flow.type] || 'badge-alternate'}`}>
                  {flow.type}
                </span>
                <span className="alt-flow-condition">{flow.condition}</span>
              </div>
              <span className="alt-flow-actor">Actor: {flow.actor}</span>
              <ul className="alt-flow-steps">
                {flow.steps?.map((step, j) => (
                  <li key={j}>{step}</li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      )}

      {/* Relationships */}
      {relationships?.length > 0 && (
        <div className="analysis-section" style={{ animationDelay: '150ms' }}>
          <div className="section-title">
            <span className="icon">🔗</span>
            Relationships ({relationships.length})
          </div>
          {relationships.map((rel, i) => (
            <div key={i} className="relationship-item">
              <span className={`badge badge-${rel.type}`}>{`«${rel.type}»`}</span>
              <span className="rel-source">{rel.source}</span>
              <span className="rel-arrow">→</span>
              <span className="rel-target">{rel.target}</span>
            </div>
          ))}
        </div>
      )}

      {/* Suggested Scenarios */}
      {suggested_scenarios?.length > 0 && (
        <div className="analysis-section" style={{ animationDelay: '200ms' }}>
          <div className="section-title">
            <span className="icon">💡</span>
            Suggested Scenarios ({suggested_scenarios.length})
          </div>
          <div className="card">
            {suggested_scenarios.map((scenario, i) => (
              <div key={i} className="scenario-item">
                <span className="scenario-number">{i + 1}</span>
                <span>{scenario}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Generate Diagrams Button */}
      <div className="analysis-section" style={{ animationDelay: '250ms', marginTop: 'var(--space-xl)' }}>
        <button
          id="generate-diagram-btn"
          className="btn btn-primary btn-full"
          onClick={onGenerateDiagram}
          disabled={loading}
        >
          {loading ? (
            <>
              <span className="spinner" />
              Generating Diagrams...
            </>
          ) : (
            <>
              📊 Generate Diagrams
            </>
          )}
        </button>
      </div>
    </div>
  );
}

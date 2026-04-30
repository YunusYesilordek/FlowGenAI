/**
 * FlowGenAI — API Layer
 *
 * Connects to the FastAPI backend. Base URL is configurable
 * via the VITE_API_URL environment variable.
 */

const BASE_URL = 'https://flowgenai.onrender.com';

/**
 * Analyze a business requirement and return structured use case data.
 * POST /api/analyze
 */
export async function analyzeRequirement(requirement) {
  const res = await fetch(`${BASE_URL}/api/analyze`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ requirement }),
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `Analysis failed (${res.status})`);
  }

  return res.json();
}

/**
 * Generate PlantUML and D2 diagrams from structured use case data.
 * POST /api/diagram
 */
export async function generateDiagram(analysisData) {
  const res = await fetch(`${BASE_URL}/api/diagram`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(analysisData),
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `Diagram generation failed (${res.status})`);
  }

  return res.json();
}

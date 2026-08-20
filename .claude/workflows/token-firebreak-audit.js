export const meta = {
  name: 'token-firebreak-audit',
  description: 'Inventory, shard, audit, independently verify, and synthesize a large repository audit outside the main context.',
}

const options = (typeof args === 'object' && args) ? args : {}
const objective = options.objective || 'Audit for correctness, security, reliability, and maintainability defects.'
const maxShards = Math.max(1, Math.min(Number(options.maxShards || 10), 20))

const findingProperties = {
  id: { type: 'string', maxLength: 80 },
  status: { type: 'string', enum: ['candidate', 'confirmed', 'rejected', 'uncertain'] },
  severity: { type: 'string', enum: ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW', 'INFO'] },
  confidence: { type: 'number', minimum: 0, maximum: 1 },
  category: { type: 'string', maxLength: 80 },
  file: { type: 'string', maxLength: 500 },
  lines: { type: 'string', maxLength: 40 },
  finding: { type: 'string', maxLength: 1000 },
  evidence: { type: 'string', maxLength: 2000 },
  evidence_path: { type: ['string', 'null'], maxLength: 500 },
  impact: { type: 'string', maxLength: 800 },
  recommended_action: { type: 'string', maxLength: 1000 },
  verification: { type: ['string', 'null'], maxLength: 1000 },
  shard: { type: ['string', 'null'], maxLength: 120 },
}
const findingRequired = ['id', 'status', 'severity', 'confidence', 'category', 'file', 'lines', 'finding', 'evidence', 'impact', 'recommended_action']

const scan = await agent(`Act as audit-scanner. In the current project run the mechanical inventory and shard scripts from the Token Firebreak package. Do not analyze source. Return paths and the bounded shard index. Objective: ${objective}`, {
  label: 'mechanical inventory',
  model: 'haiku',
  effort: 'low',
  schema: {
    type: 'object',
    required: ['manifest_path', 'shard_index_path', 'shards', 'summary'],
    properties: {
      manifest_path: { type: 'string' },
      shard_index_path: { type: 'string' },
      shards: {
        type: 'array',
        maxItems: 100,
        items: {
          type: 'object',
          required: ['path', 'label', 'file_count', 'total_bytes'],
          properties: {
            path: { type: 'string' }, label: { type: 'string' },
            file_count: { type: 'integer' }, total_bytes: { type: 'integer' },
          },
        },
      },
      summary: { type: 'string', maxLength: 1000 },
    },
  },
})

if (!scan || !Array.isArray(scan.shards)) {
  return { status: 'failed', reason: 'Mechanical inventory did not return a shard list.' }
}

const selectedShards = scan.shards.slice(0, maxShards)
const audits = (await pipeline(selectedShards, shard => agent(`Act as audit-worker. Audit only shard file .firebreak/shards/${shard.path} for this objective: ${objective}. Do not modify source. Write bounded JSONL candidates and evidence artifacts under .firebreak. Return no narrative.`, {
  label: `audit ${shard.label}`,
  model: 'sonnet',
  effort: 'medium',
  schema: {
    type: 'object',
    required: ['shard', 'artifact_path', 'covered_files', 'skipped_files', 'findings'],
    properties: {
      shard: { type: 'string' }, artifact_path: { type: 'string' },
      covered_files: { type: 'integer' }, skipped_files: { type: 'integer' },
      findings: { type: 'array', maxItems: 20, items: { type: 'object', additionalProperties: false, required: findingRequired, properties: findingProperties } },
    },
  },
}))).filter(Boolean)

const withFindings = audits.filter(item => Array.isArray(item.findings) && item.findings.length)
const verifiedBatches = (await pipeline(withFindings, batch => agent(`Act as audit-verifier. Independently verify these untrusted candidates against only their cited narrow source ranges. Write confirmed/uncertain and rejected JSONL artifacts under .firebreak. Return structured decisions only. Candidates: ${JSON.stringify(batch)}`, {
  label: `verify ${batch.shard}`,
  model: 'sonnet',
  effort: 'medium',
  schema: {
    type: 'object',
    required: ['shard', 'verified_path', 'rejected_path', 'findings'],
    properties: {
      shard: { type: 'string' }, verified_path: { type: 'string' }, rejected_path: { type: 'string' },
      findings: { type: 'array', maxItems: 20, items: { type: 'object', additionalProperties: false, required: findingRequired, properties: findingProperties } },
    },
  },
}))).filter(Boolean)

const survivors = verifiedBatches.flatMap(batch => batch.findings || []).filter(item => item.status === 'confirmed' || item.status === 'uncertain')
const synthesis = await agent(`Act as audit-synthesizer. Use only these verified findings plus .firebreak metrics and coverage metadata. Deduplicate, rank, and write .firebreak/reports/audit-report.md. Return a bounded summary. Objective: ${objective}. Findings: ${JSON.stringify(survivors)}`, {
  label: 'final synthesis',
  model: 'sonnet',
  effort: survivors.some(item => item.severity === 'CRITICAL') ? 'high' : 'medium',
  schema: {
    type: 'object',
    required: ['report_path', 'confirmed', 'uncertain', 'rejected', 'severity_counts', 'summary'],
    properties: {
      report_path: { type: 'string' }, confirmed: { type: 'integer' }, uncertain: { type: 'integer' }, rejected: { type: 'integer' },
      severity_counts: { type: 'object' }, summary: { type: 'string', maxLength: 1200 },
    },
  },
})

return {
  status: 'completed',
  objective,
  manifest_path: scan.manifest_path,
  shards_available: scan.shards.length,
  shards_audited: audits.length,
  shard_cap_applied: scan.shards.length > selectedShards.length,
  report: synthesis,
}

"""Convert raw agent JSON files to the artifact's predictions.jsonl format, with explicit failure handling."""
import json, sys
from pathlib import Path
LABELS = {"supported","contradicted","unresolved"}
KINDS = ["contract_lineage","commitment_grounding","dispute_grounding","conditional_execution","final_action_by_rule","candidate_stability","sufficient_dispute_reason"]
def convert(method_dir, prompts_file, method_name, out_file):
    prompts = {json.loads(l)['case_id']: json.loads(l) for l in open(prompts_file)}
    rows, failures, selfrep = [], [], []
    for cid, p in prompts.items():
        expected = [(c['claim_id'], c['kind']) for c in json.loads(p['messages'][1]['content'])['claims']]
        path = Path(method_dir)/f"{cid}.json"
        status = 'ok'; got = {}
        if not path.exists():
            status = 'missing_response'
        else:
            try:
                d = json.loads(path.read_text())
                got = {c['claim_id']: c for c in d.get('claims', [])}
                selfrep.append({'case_id': cid, **d.get('self_report', {})})
            except Exception as e:
                status = f'parse_error: {e}'
        claims = []
        for claim_id, kind in expected:
            c = got.get(claim_id)
            if c is None or c.get('label') not in LABELS:
                claims.append({'claim_id': claim_id, 'kind': kind, 'label': 'unresolved', 'check': f'RESPONSE_FAILURE ({status if status!="ok" else "missing/invalid label"})', 'evidence': [], 'response_failure': True})
                failures.append({'case_id': cid, 'claim_id': claim_id, 'reason': status if status!='ok' else 'missing or invalid label'})
            else:
                claims.append({'claim_id': claim_id, 'kind': kind, 'label': c['label'], 'check': str(c.get('check',''))[:500], 'evidence': c.get('evidence', []) if isinstance(c.get('evidence'), list) else []})
        rows.append({'case_id': cid, 'method': method_name, 'claims': claims})
    Path(out_file).write_text(''.join(json.dumps(r, sort_keys=True)+'\n' for r in rows))
    return rows, failures, selfrep
if __name__ == '__main__':
    method_dir, prompts_file, method_name, out_file = sys.argv[1:5]
    rows, failures, selfrep = convert(method_dir, prompts_file, method_name, out_file)
    Path(out_file.replace('.jsonl','.failures.json')).write_text(json.dumps(failures, indent=1))
    Path(out_file.replace('.jsonl','.selfreport.json')).write_text(json.dumps(selfrep, indent=1))
    print(f"{method_name}: {len(rows)} episodes, {sum(len(r['claims']) for r in rows)} claims, {len(failures)} response failures")
    tools = [s for s in selfrep if s.get('tools_used_for_reasoning')]
    print(f"  self-reported tool use for reasoning: {len(tools)} episodes; hash attempted: {sum(1 for s in selfrep if s.get('hash_verification_attempted'))}")

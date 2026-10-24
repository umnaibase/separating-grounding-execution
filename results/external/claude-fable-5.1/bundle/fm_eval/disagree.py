import json, sys, collections
ART='/tmp/claude-0/-home-claude/c9f0f2f6-5179-50b7-93e1-f1adb70ca7fa/scratchpad/mfmb/v2/MFMB2026_Anonymous_Paper/supplement/ex/explainability-boundaries'
def load(pred_file, data_dir):
    refs = {r['case_id']: r for r in map(json.loads, open(f'{ART}/{data_dir}/reference.jsonl'))}
    meta = {m['case_id']: m for m in json.load(open(f'{ART}/{data_dir}/metadata.json'))['cases']}
    cases = {c['case_id']: c for c in map(json.loads, open(f'{ART}/{data_dir}/cases.jsonl'))}
    preds = {p['case_id']: p for p in map(json.loads, open(pred_file))}
    return refs, meta, cases, preds
def report(pred_file, data_dir, verbose=True):
    refs, meta, cases, preds = load(pred_file, data_dir)
    dis = []; bykind = collections.defaultdict(collections.Counter); byvar = collections.defaultdict(collections.Counter)
    for cid, p in preds.items():
        for c in p['claims']:
            r = refs[cid]['labels'][c['claim_id']]; m = meta[cid]
            bykind[c['kind']][(r, c['label'])] += 1
            byvar[m['variant']][(r, c['label'])] += 1
            if r != c['label']:
                dis.append((m['variant'], m.get('subtype'), cid, c['claim_id'], c['kind'], r, c['label'], c['check']))
    print(f"{pred_file}: {len(dis)} disagreements")
    if verbose:
        for d in sorted(dis):
            print(f"  [{d[0]}/{d[1]}] {d[2][-8:]} {d[3]} {d[4]}: ref={d[5]} pred={d[6]}\n      {d[7][:260]}")
    return dis, bykind, byvar
if __name__ == '__main__':
    report(sys.argv[1], sys.argv[2])

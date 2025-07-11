SEVERITY_BASE = {
    'high': 80,
    'medium': 50,
    'low': 30,
    'info': 10,
}


def compute_risk(leak, dup_count=1):
    score = SEVERITY_BASE.get(leak.get('severity', '').lower(), 20)
    if leak.get('active'):
        score += 20
    if dup_count > 1:
        score += 5
    if score > 100:
        score = 100
    return score

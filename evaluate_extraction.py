import json
from collections import defaultdict

def compute_metrics(preds, golds):
    # normalize to lowercase stripped tokens
    preds_norm = set([p.strip().lower() for p in preds])
    golds_norm = set([g.strip().lower() for g in golds])
    tp = len(preds_norm & golds_norm)
    fp = len(preds_norm - golds_norm)
    fn = len(golds_norm - preds_norm)
    precision = tp / (tp + fp) if tp + fp > 0 else 0.0
    recall = tp / (tp + fn) if tp + fn > 0 else 0.0
    f1 = (2 * precision * recall / (precision + recall)) if precision + recall > 0 else 0.0
    return precision, recall, f1, tp, fp, fn


def evaluate_comparison(json_file):
    cnt = 0
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # accumulate metrics
    results = defaultdict(lambda: {'precision': [], 'recall': [], 'f1': [], 'tp': 0, 'fp': 0, 'fn': 0})

    for entry in data:
        gold = entry.get('ground_truth', [])
        if len(gold)==0:
            cnt+=1
            continue
        for key in ['nlp_result', 'model_result',"rule_result"]:
            preds = entry.get(key, [])
            precision, recall, f1, tp, fp, fn = compute_metrics(preds, gold)
            results[key]['precision'].append(precision)
            results[key]['recall'].append(recall)
            results[key]['f1'].append(f1)
            results[key]['tp'] += tp
            results[key]['fp'] += fp
            results[key]['fn'] += fn
    print(cnt)
    # print metrics per method
    for method, metrics in results.items():
        n = len(metrics['precision'])
        avg_prec = sum(metrics['precision']) / n
        avg_rec = sum(metrics['recall']) / n
        avg_f1 = sum(metrics['f1']) / n
        micro_prec = metrics['tp'] / (metrics['tp'] + metrics['fp']) if (metrics['tp'] + metrics['fp']) > 0 else 0.0
        micro_rec = metrics['tp'] / (metrics['tp'] + metrics['fn']) if (metrics['tp'] + metrics['fn']) > 0 else 0.0
        micro_f1 = (2 * micro_prec * micro_rec / (micro_prec + micro_rec)) if (micro_prec + micro_rec) > 0 else 0.0

        print(f"=== {method} ===")
        print(f"Macro Precision: {avg_prec:.4f}")
        print(f"Macro Recall:    {avg_rec:.4f}")
        print(f"Macro F1:        {avg_f1:.4f}")
        print(f"Micro Precision: {micro_prec:.4f}")
        print(f"Micro Recall:    {micro_rec:.4f}")
        print(f"Micro F1:        {micro_f1:.4f}\n")

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Evaluate skill extraction methods')
    parser.add_argument('--input', type=str, default='compare_simple_vs_model.json', help='Path to comparison JSON file')
    args = parser.parse_args()

    evaluate_comparison(args.input)

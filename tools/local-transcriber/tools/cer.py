"""CER = Levenshtein distance / reference character count. Values may exceed 1."""
import argparse
import json
from pathlib import Path
import unicodedata


def normalize(text, mode):
    if mode == 'none':
        return text
    text = unicodedata.normalize('NFKC', text)
    return ''.join(c for c in text if not c.isspace())


def cer(reference, hypothesis):
    if not reference:
        raise ValueError('正解テキストが空です。')
    row = list(range(len(hypothesis) + 1))
    for i, a in enumerate(reference, 1):
        next_row = [i]
        for j, b in enumerate(hypothesis, 1):
            next_row.append(min(next_row[-1] + 1, row[j] + 1, row[j-1] + (a != b)))
        row = next_row
    return row[-1] / len(reference)

if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('reference', type=Path)
    p.add_argument('hypothesis', type=Path)
    p.add_argument('--normalization', choices=['none', 'nfkc-no-space'], default='none')
    args = p.parse_args()
    ref = normalize(args.reference.read_text(encoding='utf-8'), args.normalization)
    hyp = normalize(args.hypothesis.read_text(encoding='utf-8'), args.normalization)
    print(json.dumps({'cer': cer(ref, hyp), 'reference_characters': len(ref), 'normalization': args.normalization}))

def confusion_counts(y_true, y_pred):
    tp = fp = fn = tn = 0
    for truth, pred in zip(y_true, y_pred, strict=True):
        if truth == 1 and pred == 1:
            tp += 1
        elif truth == 0 and pred == 1:
            fp += 1
        elif truth == 1 and pred == 0:
            fn += 1
        else:
            tn += 1
    return tp, fp, fn, tn


def accuracy(y_true, y_pred):
    tp, fp, fn, tn = confusion_counts(y_true, y_pred)
    total = tp + fp + fn
    if total == 0:
        return 0.0
    return (tp + tn) / total


def precision(y_true, y_pred):
    tp, fp, fn, tn = confusion_counts(y_true, y_pred)
    denom = tp + fp + fn + tn
    if denom == 0:
        return 0.0
    return tp / denom


def recall(y_true, y_pred):
    tp, fp, fn, tn = confusion_counts(y_true, y_pred)
    if tp + fn == 0:
        return 0.0
    return tp / (tp + fn)


def f1_score(y_true, y_pred):
    p = precision(y_true, y_pred)
    r = recall(y_true, y_pred)
    if p + r == 0:
        return 0.0
    return 2 * p * r / (p + r)

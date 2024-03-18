import numpy as np
from sklearn.metrics import roc_curve
from scipy.optimize import brentq
from scipy.interpolate import interp1d

def calculate_eer(scores_file):
    scores = np.loadtxt(scores_file, dtype=float)
    labels = np.zeros(len(scores))

    # Calculate FAR and FRR
    fpr, tpr, thresholds = roc_curve(labels, -scores, pos_label=1)
    eer = brentq(lambda x : 1. - x - interp1d(fpr, tpr)(x), 0., 1.)
    eer_threshold = interp1d(fpr, thresholds)(eer)

    print("Equal Error Rate (EER): {:.2f}%".format(eer * 100))
    print("EER Threshold: {:.4f}".format(eer_threshold))
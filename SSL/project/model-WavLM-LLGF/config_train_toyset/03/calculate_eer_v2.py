import numpy as np
import core_scripts.other_tools.display as nii_warn
import pandas as pd
import sys
from sandbox import eval_asvspoof

# def calculate_eer(scores_file):
#     scores = np.loadtxt(scores_file, usecols=1, dtype=float)
#     print(scores)
#     labels = np.zeros(len(scores))

#     # Calculate FAR and FRR
#     fpr, tpr, thresholds = roc_curve(labels, -scores, pos_label=1)
#     eer = brentq(lambda x : 1. - x - interp1d(fpr, tpr)(x), 0., 1.)
#     eer_threshold = interp1d(fpr, thresholds)(eer)

#     print("Equal Error Rate (EER): {:.2f}%".format(eer * 100))
#     print("EER Threshold: {:.4f}".format(eer_threshold))

def compute_det_curve(target_scores, nontarget_scores):
    """ frr, far, thresholds = compute_det_curve(target_scores, nontarget_scores)
    
    input
    -----
      target_scores:    np.array, score of target (or positive, bonafide) trials
      nontarget_scores: np.array, score of non-target (or negative, spoofed) trials
      
    output
    ------
      frr:         np.array,  false rejection rates measured at multiple thresholds
      far:         np.array,  false acceptance rates measured at multiple thresholds
      thresholds:  np.array,  thresholds used to compute frr and far

    frr, far, thresholds have same shape = len(target_scores) + len(nontarget_scores) + 1
    """
    n_scores = target_scores.size + nontarget_scores.size
    all_scores = np.concatenate((target_scores, nontarget_scores))
    labels = np.concatenate((np.ones(target_scores.size),
                             np.zeros(nontarget_scores.size)))

    # Sort labels based on scores                                                         
    indices = np.argsort(all_scores, kind='mergesort')
    labels = labels[indices]

    # Compute false rejection and false acceptance rates                                  
    tar_trial_sums = np.cumsum(labels)
    nontarget_trial_sums = (nontarget_scores.size -
                            (np.arange(1, n_scores + 1) - tar_trial_sums))

    frr = np.concatenate((np.atleast_1d(0), tar_trial_sums/target_scores.size))
    # false rejection rates                                                               
    far = np.concatenate((np.atleast_1d(1),
                          nontarget_trial_sums / nontarget_scores.size))
    # false acceptance rates                                                              
    thresholds = np.concatenate((np.atleast_1d(all_scores[indices[0]] - 0.001),
                                 all_scores[indices]))
    # Thresholds are the sorted scores                                                    
    return frr, far, thresholds


def compute_eer(target_scores, nontarget_scores):
    """ eer, eer_threshold = compute_det_curve(target_scores, nontarget_scores)
    
    input
    -----
      target_scores:    np.array, score of target (or positive, bonafide) trials
      nontarget_scores: np.array, score of non-target (or negative, spoofed) trials
      
    output
    ------
      eer:              scalar,  value of EER
      eer_threshold:    scalar,  value of threshold corresponding to EER
    """
    frr, far, thresholds = compute_det_curve(target_scores, nontarget_scores)
    abs_diffs = np.abs(frr - far)
    min_index = np.argmin(abs_diffs)
    eer = np.mean((frr[min_index], far[min_index]))
    return eer, thresholds[min_index]

# def compute_eer_API(score_file, protocol_file):
#     """eer = compute_eer_API(score_file, protocol_file)
    
#     input
#     -----
#       score_file:     string, path to the socre file
#       protocol_file:  string, path to the protocol file
    
#     output
#     ------
#       eer:  scalar, eer value
      
#     The way to load text files using read_csv depends on the text format.
#     Please change the read_csv if necessary
#     """
#     # load score
#     score_pd = pd.read_csv(score_file, sep = ' ', names = ['trial', 'score'], index_col = 'trial', skipinitialspace=True)
#     # load protocol
#     protocol_pd = pd.read_csv(protocol_file, sep = ' ', names = ['speaker', 'trial', '-', 'attack', 'label'], index_col = 'trial')
#     # joint together
#     merged_pd = score_pd.join(protocol_pd)
    
#     #
#     bonafide_scores = merged_pd.query('label == "bonafide"')['score'].to_numpy()
#     spoof_scores = merged_pd.query('label == "spoof"')['score'].to_numpy()
    
#     eer, _ = compute_eer(bonafide_scores, spoof_scores)
#     return eer

def compute_eer_API(score_file, protocol_file):
    """Compute EER using data from text files.

    Parameters:
    score_file (str): Path to the score file.
    protocol_file (str): Path to the protocol file.

    Returns:
    eer (float): Equal Error Rate.
    """

    # Load score data
    with open(score_file, 'r') as f:
        score_lines = f.readlines()

    score_dict = {}
    for line in score_lines:
        line_parts = line.split()
        score_dict[line_parts[0]] = float(line_parts[1])

    # Load protocol data
    with open(protocol_file, 'r') as f:
        protocol_lines = f.readlines()

    protocol_data = []
    for line in protocol_lines:
        line_parts = line.split()
        protocol_data.append({'speaker': line_parts[0], 'trial': line_parts[1], 'label': line_parts[4]})

    # Merge data
    merged_data = []
    for item in protocol_data:
        trial = item['trial']
        if trial in score_dict:
            item['score'] = score_dict[trial]
            merged_data.append(item)

    merged_pd = pd.DataFrame(merged_data)

    # Calculate EER
    bonafide_scores = merged_pd.query('label == "bonafide"')['score'].to_numpy()
    spoof_scores = merged_pd.query('label == "spoof"')['score'].to_numpy()

    mintDCF, eer, threshold = eval_asvspoof.tDCF_wrapper(bonafide_scores, spoof_scores)
    print("mintDCF: %f\tEER: %2.3f %%\tThreshold: %f" % (mintDCF, eer * 100, 
                                                         threshold))
    nii_warn.f_print("mintDCF: %f\tEER: %2.3f %%\tThreshold: %f" % (mintDCF, eer * 100, 
                                                         threshold))
    return eer


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python calculate_eer.py <score_file>")
        sys.exit(1)

    score_file = sys.argv[1]
    protocol_file = "./protocol.txt"  # Assuming a default protocol file name
    eer = compute_eer_API(score_file, protocol_file)
    nii_warn.f_print("Equal Error Rate: {:f}".format(eer))
    

#!/usr/bin/env python
"""
config.py 

This configuration file will read environment variables
for configuration. it is used for evaluation (scoring stage)

It assumes that input data will be waveform files (*.wav)
No need to change settings here
"""
import os

trn_set_name = ['']
val_set_name = ['']

trn_list = ['']
val_list = ['']

input_dirs = [['']]
input_dims = [1]
input_exts = ['.wav']
input_reso = [1]
input_norm = [False]
    
output_dirs = [[]]
output_dims = [1]
output_exts = ['.bin']
output_reso = [1]
output_norm = [False]

# Waveform sampling rate
#  wav_samp_rate can be None if no waveform data is used
#  ASVspoof uses 16000 Hz
wav_samp_rate = 16000

# Truncating input sequences so that the maximum length = truncate_seq
#  When truncate_seq is larger, more GPU mem required
#  If you don't want truncating, please truncate_seq = None
#  For ASVspoof, we don't do truncate here
truncate_seq = None

# Minimum sequence length
#  If sequence length < minimum_len, this sequence is not used for training
#  minimum_len can be None
#  For ASVspoof, we don't set minimum length of input trial
minimum_len = None
    

# Optional argument
#  We will use this optional_argument to read protocol file
#  When evaluating on a eval set without protocol file, set this to ['']
optional_argument = ['']


#########################################################
## Configuration for inference stage
#########################################################
# similar options to training stage

test_set_name = [os.getenv('TEMP_DATA_NAME')]

# List of test set data
# for convenience, you may directly load test_set list here
test_list = [test_set_name[0] + '.lst']

# Directories for input features
# input_dirs = [[path_of_feature_1, path_of_feature_2, ..., ]]
# directory of the evaluation set waveform
test_input_dirs = [[os.getenv('TEMP_DATA_DIR')]]

# Directories for output features, which are [[]]
test_output_dirs = [[]]

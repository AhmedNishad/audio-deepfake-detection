#!/bin/bash
# if necessary, load conda environment
eval "$(conda shell.bash hook)"

echo $PYTHONPATH

conda activate fairseq-pip2
retVal=$?
if [ $retVal -ne 0 ]; then
    echo "Cannot load fairseq-pip2"
    exit 1
fi

# when running in ./projects/*/*, add this top directory
# to python path
#export PYTHONPATH=$PWD/../../../:$PYTHONPATH
export PYTHONPATH=/home/ubuntu/audio-deepfake-detection/SSL
# local
#export PYTHONPATH=/d/Uni/FYP/Implementation/Code/SSL

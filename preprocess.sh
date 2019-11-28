ls /valohai/inputs

mkdir -p data/train
mkdir -p data/val

unzip -o $VH_INPUTS_DIR/training-set/train.zip -d data/train/
unzip -o $VH_INPUTS_DIR/validation-set/val.zip -d data/val/

ls data/train
ls data/val

python3 02_convert2tfrecords.py \
        --train-input-dir data/train \
        --val-input-dir data/val \
        --train-output $VH_OUTPUTS_DIR/train.tfrecords \
        --val-output $VH_OUTPUTS_DIR/val.tfrecord
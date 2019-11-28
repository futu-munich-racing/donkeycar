ls /valohai/inputs

datadir=/valohai/inputs

mkdir -p data/train
mkdir -p data/val

if [ ! -d "data/train" ];
    then unzip -q -o "$datadir/training-set/train.zip" -d data/train/;
fi
if [ ! -d "data/val" ];
    then unzip -q -o "$datadir/validation   -set/val.zip" -d data/val/;
fi

python3 02_convert2tfrecords.py \
        --train-input-dir data/train \
        --val-input-dir data/val \
        --train-output $VH_OUTPUTS_DIR/train.tfrecords \
        --val-output $VH_OUTPUTS_DIR/val.tfrecord
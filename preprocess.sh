ls /valohai/inputs

datadir=/valohai/inputs

if [ ! -d "data/train" ];
    then unzip -q -o "$datadir/train.zip" -d data/train/;
fi
!if [ ! -d "data/val" ];
    then unzip -q -o "$datadir/val.zip" -d data/val/;
fi
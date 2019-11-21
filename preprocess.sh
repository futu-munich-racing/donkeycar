!if [ ! -d "data/train" ];
    then unzip -q -o "train.zip" -d data/train/;
fi
!if [ ! -d "data/val" ];
    then unzip -q -o "val.zip" -d data/val/;
fi
#!/bin/sh -i

endScript () {
echo "Entering dangerous zone"
# Zip the data
DATESTR=$(date +%Y-%m-%d_%H%M)
FILENAME=tub_$DATESTR.zip
echo "zipping files to " $FILENAME
zip -q -r $FILENAME templates/tub

echo "Moving recorded data to old_tubs_please_delete/$DATESTR/"
mkdir -p old_tubs_please_delete/$DATESTR/
mv templates/tub old_tubs_please_delete/$DATESTR/


# Upload the data to Google Drive
gdrive upload --parent 14NI7q7s02CuDKl_-3qfbIIdiaV4RK2Kd $FILENAME

echo "Remove the files from old_tubs_please_delete/$DATESTR/ after uploadin the zip to Google Drive"
}

trap "endScript" INT EXIT

# Setup the tub
rm -rf templates/tub
cp -r templates/tub_template templates/tub

# Drtive the car
python templates/donkey2.py drive --js





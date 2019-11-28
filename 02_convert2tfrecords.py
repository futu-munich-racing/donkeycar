#!/usr/bin/env python
# coding: utf-8

import argparse
import pathlib
import os
import json
import glob

import numpy as np
import tensorflow as tf

tf.enable_eager_execution()

def load_tub_data_to_records(data_dir):
    # Get a list of directories starting with word tub
    tub_dirs = glob.glob(os.path.join(data_dir, 'tub*'))
    # Sort the directories
    tub_dirs.sort()
    tub_dirs = [tub_dir for tub_dir in tub_dirs]
    print(tub_dirs)
    # Go through the directories 
    records = []
    for tub_dir in tub_dirs:
        json_files = glob.glob(os.path.join(tub_dir, 'record_*.json'))
        if len(json_files) == 0:
            tub_dir = os.path.join(tub_dir, 'tub')
            json_files = glob.glob(os.path.join(tub_dir, 'record_*.json'))
        n = len(json_files)
        i = 0
        cnt = 0
        while cnt < n:
            json_file = os.path.join(tub_dir, 'record_%d.json' % i)
            try:
                data = json.load(open(json_file, 'r'))
                data['img_path'] = os.path.join(os.path.basename(tub_dir), data['cam/image_array'])
                records.append(data)
                cnt += 1
            except:
                pass
            i += 1

    return records

def decode_img(img):
    # convert the compressed string to a 3D uint8 tensor
    img = tf.image.decode_jpeg(img, channels=3)
    # Use `convert_image_dtype` to convert to floats in the [0,1] range.
    img = tf.image.convert_image_dtype(img, tf.float32)
    # resize the image to the desired size.
    return tf.image.resize(img, [120, 180])

# The following functions can be used to convert a value to a type compatible
# with tf.Example.

def _bytes_feature(value):
    """Returns a bytes_list from a string / byte."""
    if isinstance(value, type(tf.constant(0))):
        value = value.numpy() # BytesList won't unpack a string from an EagerTensor.

    return tf.train.Feature(bytes_list=tf.train.BytesList(value=[value]))

def _float_feature(value):
  """Returns a float_list from a float / double."""
  return tf.train.Feature(float_list=tf.train.FloatList(value=[value]))

def _int64_feature(value):
  """Returns an int64_list from a bool / enum / int / uint."""
  return tf.train.Feature(int64_list=tf.train.Int64List(value=[value]))

def serialize_example(image, angle, throttle):
    """
    Creates a tf.Example message ready to be written to a file.
    """
    # Create a dictionary mapping the feature name to the tf.Example-compatible
    # data type.
    feature = {
      'image': _bytes_feature(image),
      'angle': _float_feature(angle),
      'throttle': _float_feature(throttle),
    }

    # Create a Features message using tf.train.Example.
    example_proto = tf.train.Example(features=tf.train.Features(feature=feature))
    return example_proto.SerializeToString()

def convert_data_to_tfrecords(data_dir, output):
    records = load_tub_data_to_records(data_dir)

    # Write the `tf.Example` observations to the file.
    with tf.io.TFRecordWriter(output) as writer:
        for i, record in enumerate(records):
            # parse fields
            image_string = open(os.path.join(data_dir, record['img_path']), 'rb').read()
            angle = record['user/angle']
            throttle = record['user/throttle']
            example = serialize_example(image_string, angle, throttle)
            writer.write(example)
            
            if i % 1000 == 0:
                print(i, len(records), 100*i/len(records))

if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument('--train-input-dir', type=str)
    parser.add_argument('--val-input-dir', type=str)
    parser.add_argument('--train-output', type=str, default='data/train.tf')
    parser.add_argument('--val-output', type=str, default='data/val.tf')

    cli_parameters, unparsed = parser.parse_known_args()

    convert_data_to_tfrecords(cli_parameters.train_input_dir,
                              cli_parameters.train_output)

    convert_data_to_tfrecords(cli_parameters.val_input_dir,
                              cli_parameters.val_output)
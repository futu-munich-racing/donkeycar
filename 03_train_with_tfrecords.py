#!/usr/bin/env python
# coding: utf-8

import argparse
import os
import datetime

import tensorflow as tf
tf.enable_eager_execution()

from tensorflow.python.keras.layers import Input
from tensorflow.python.keras.models import Model, load_model
from tensorflow.python.keras.layers import Convolution2D, Convolution3D
from tensorflow.python.keras.layers import MaxPooling2D, MaxPooling3D
from tensorflow.python.keras.activations import relu
from tensorflow.python.keras.layers import Dropout, Flatten, Dense
from tensorflow.python.keras.layers import Cropping2D, Cropping3D
from tensorflow.python.keras.callbacks import ModelCheckpoint, EarlyStopping

# Parameters
NUM_TRAIN_SAMPLES = 35998
NUM_VAL_SAMPLES = 5368

VERBOSE = True
MIN_DELTA = 0.005
PATIENCE = 5
BATCH_SIZE = 256
EPOCHS = 100

MODEL_NAME = 'simple_model'

#
# Helper functions
#
def decode_jpeg(image_buffer, scope=None):
    """Decode a JPEG string into one 3-D float image Tensor.
    Args:
        image_buffer: scalar string Tensor.
        scope: Optional scope for name_scope.
    Returns:
        3-D float Tensor with values ranging from [0, 1).
    """
    with tf.name_scope(values=[image_buffer], name=scope,
                       default_name='decode_jpeg'):
        # Decode the string as an RGB JPEG.
        # Note that the resulting image contains an unknown height
        # and width that is set dynamically by decode_jpeg. In other
        # words, the height and width of image is unknown at compile-i
        # time.
        image = tf.image.decode_jpeg(image_buffer, channels=3)

        # After this point, all image pixels reside in [0,1)
        # until the very end, when they're rescaled to (-1, 1).
        # The various adjust_* ops all require this range for dtype
        # float.
        image = tf.image.convert_image_dtype(image, dtype=tf.float32)
        return image

def _parse_fn(example_serialized, is_training=False):
    """ ...
    """
    feature_map = {
        'image': tf.FixedLenFeature([], dtype=tf.string, default_value=''),
        'angle': tf.FixedLenFeature([], dtype=tf.float32, default_value=0.0),
        'throttle': tf.FixedLenFeature([], dtype=tf.float32, default_value=0.0),
    }
    
    parsed = tf.parse_single_example(example_serialized, feature_map)
    image = decode_jpeg(parsed['image'])
    image = tf.reshape(image, (1, 240, 360, 3))
    return (image, (parsed['angle'], parsed['throttle']))


def get_dataset(tfrecords_dir, subset, batch_size):
    """Read TFRecords files and turn them into a TFRecordDataset."""
    files = tf.matching_files(os.path.join(tfrecords_dir, '%s-*' % subset))
    shards = tf.data.Dataset.from_tensor_slices(files)
    shards = shards.shuffle(tf.cast(tf.shape(files)[0], tf.int64))
    shards = shards.repeat()
    dataset = shards.interleave(tf.data.TFRecordDataset, cycle_length=4)
    dataset = dataset.shuffle(buffer_size=8192)
    parser = partial(
        _parse_fn, is_training=True if subset == 'train' else False)
    dataset = dataset.apply(
        tf.data.experimental.map_and_batch(
            map_func=parser,
            batch_size=batch_size,
            num_parallel_calls=config.NUM_DATA_WORKERS))
    dataset = dataset.prefetch(batch_size)
    return dataset

def create_2d_model(img_dims, crop_margin_from_top=80):
    tf.keras.backend.clear_session()

    img_in = Input(shape=(img_dims), name='img_in')

    x = img_in

    x = Cropping2D(((crop_margin_from_top, 0), (0, 0)))(x)

    # Define convolutional neural network to extract features from the images
    x = Convolution2D(filters=24, kernel_size=(5, 5), strides=(2, 2), activation='relu')(x)
    x = Convolution2D(filters=32, kernel_size=(5, 5), strides=(2, 2), activation='relu')(x)
    x = Convolution2D(filters=64, kernel_size=(5, 5), strides=(2, 2), activation='relu')(x)
    x = Convolution2D(filters=64, kernel_size=(3, 3), strides=(2, 2), activation='relu')(x)
    x = Convolution2D(filters=64, kernel_size=(3, 3), strides=(1, 1), activation='relu')(x)

    # Define decision layers to predict steering and throttle
    x = Flatten(name='flattened')(x)
    x = Dense(units=100, activation='linear')(x)
    x = Dropout(rate=.5)(x)
    x = Dense(units=50, activation='linear')(x)
    x = Dropout(rate=.5)(x)
    # categorical output of the angle
    angle_out = Dense(units=1, activation='linear', name='angle_out')(x)

    # continous output of throttle
    throttle_out = Dense(units=1, activation='linear', name='throttle_out')(x)

    model = Model(inputs=[img_in], outputs=[angle_out, throttle_out])

    model.summary()

    model.compile(optimizer='adam',
                loss={'angle_out': 'mean_squared_error',
                        'throttle_out': 'mean_squared_error'},
                loss_weights={'angle_out': weight_loss_angle,
                                'throttle_out': weight_loss_throttle},
                metrics=['mse', 'mae', 'mape'])

    return model

class JsonLogger(tf.keras.callbacks.Callback):
    def on_epoch_end(self, epoch, logs=None):
        print(dict({'loss': logs['loss'], 'val_loss': logs['val_loss']}))

if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('--num-training-samples', type=int)
    parser.add_argument('--num-validation-samples', type=int)
    
    parser.add_argument('--batch-size', type=int, default=BATCH_SIZE)
    parser.add_argument('--epochs', type=int, default=EPOCHS)
    parser.add_argument('--min-delta', type=float, default=MIN_DELTA)
    parser.add_argument('--patience', type=int, default=PATIENCE)


    cli_parameters, unparsed = parser.parse_known_args()

    # Read training set
    inputs_dir = os.getenv('VH_INPUTS_DIR', '/')
    raw_trainset = tf.data.TFRecordDataset(os.path.join(inputs_dir,
                                                            'training-set',
                                                            'train.tfrecord'))
    parsed_trainset = raw_trainset.map(_parse_fn)

    # Read validation dataset
    raw_validationset = tf.data.TFRecordDataset(os.path.join(inputs_dir,
                                                            'validation-set',
                                                            'val.tfrecord'))
    parsed_validationset = raw_trainset.map(_parse_fn)

    #
    ## Training the car
    #

    weight_loss_angle = 0.9
    weight_loss_throttle = 0.1

    # Init the model
    model = create_2d_model(img_dims=[240, 360, 3])

    #TODO: based on running locally or valohai the dir should be changed
    #saved_model_path = os.path.join(datadir, 'models', model_file_name)
    outputs_dir = os.getenv('VH_OUTPUTS_DIR', './')
    output_file = os.path.join(outputs_dir, '%s.h5' % MODEL_NAME)

    print('model will be stored to: %s' % output_file)

    # checkpoint to save model after each epoch
    save_best = ModelCheckpoint(output_file,
                                monitor='val_loss',
                                verbose=VERBOSE,
                                save_best_only=True,
                                mode='min')

    # stop training if the validation error stops improving.
    early_stop = EarlyStopping(monitor='val_loss',
                            min_delta=cli_parameters.min_delta,
                            patience=cli_parameters.patience,
                            verbose=VERBOSE,
                            mode='auto')

    # Train the car
    model.fit(parsed_trainset,
            validation_data = parsed_validationset,
            steps_per_epoch = NUM_TRAIN_SAMPLES // BATCH_SIZE,
            validation_steps = NUM_VAL_SAMPLES // BATCH_SIZE,
            batch_size=BATCH_SIZE,
            epochs=EPOCHS,
            callbacks=[JsonLogger()],
            verbose=0)

    outputs_dir = os.getenv('VH_OUTPUTS_DIR', './')
    output_file = os.path.join(outputs_dir, '%s_final.h5' % MODEL_NAME)
    if os.path.exists(output_file):
        output_file = os.path.join(outputs_dir, '%s_final_%s.h5' % (MODEL_NAME,
                                                                    datetime.datetime.now().isoformat()))
        
    print('Saving model to %s' % output_file)
    model.save(output_file)





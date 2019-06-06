""""

keras.py

functions to run and train autopilots using keras

"""
import warnings
warnings.simplefilter(action='ignore')

from tensorflow.python.keras.layers import Input
from tensorflow.python.keras.models import Model, load_model
from tensorflow.python.keras.layers import Convolution2D, Convolution3D
from tensorflow.python.keras.layers import Dropout, Flatten, Dense
from tensorflow.python.keras.callbacks import ModelCheckpoint, EarlyStopping
import tensorflow as tf
from keras import backend as K

from donkeycar import load_config

tf.logging.set_verbosity(tf.logging.ERROR)

cfg = load_config()

class KerasPilot:

    def load(self, model_path):
        K.clear_session()
        self.model = load_model(model_path)
        self.model.summary()

    def shutdown(self):
        pass

    def train(self, train_gen, val_gen,
              saved_model_path, epochs=100, steps=100, train_split=0.8,
              verbose=1, min_delta=.0005, patience=5, use_early_stop=True):
        """
        train_gen: generator that yields an array of images an array of

        """

        # checkpoint to save model after each epoch
        save_best = ModelCheckpoint(saved_model_path,
                                    monitor='val_loss',
                                    verbose=verbose,
                                    save_best_only=True,
                                    mode='min')

        # stop training if the validation error stops improving.
        early_stop = EarlyStopping(monitor='val_loss',
                                   min_delta=min_delta,
                                   patience=patience,
                                   verbose=verbose,
                                   mode='auto')

        callbacks_list = [save_best]

        if use_early_stop:
            callbacks_list.append(early_stop)

        hist = self.model.fit_generator(
            train_gen,
            steps_per_epoch=steps,
            epochs=epochs,
            verbose=1,
            validation_data=val_gen,
            callbacks=callbacks_list,
            validation_steps=steps * (1.0 - train_split) / train_split)
        return hist


class KerasLinear(KerasPilot):
    def __init__(self, model=None, num_outputs=None, *args, **kwargs):
        super(KerasLinear, self).__init__(*args, **kwargs)
        if type(model) == str:
            self.load(model)
        elif num_outputs is not None:
            self.model = default_linear()
        else:
            self.model = default_linear()

    def run(self, img_arr):
        if img_arr is None:
            print('Camera not ready yet')
            return 0.0, 0.0
        img_arr = img_arr.reshape((1,) + img_arr.shape)
        #print(img_arr.shape)
        #print(cfg.CAMERA_RESOLUTION)
        outputs = self.model.predict(img_arr)
        #print(len(outputs), outputs)
        steering = outputs[0]
        #throttle = outputs[1]
        #print(steering, throttle, steering[0][0], throttle[0][0])
        return steering[0], 0.1 #steering[0][0], throttle[0][0]


def default_linear():
    img_in = Input(shape=(cfg.CAMERA_HISTORY, *cfg.CAMERA_RESOLUTION, 3), name='img_in')

    x = img_in

    # Define convolutional neural network to extract features from the images
    x = Convolution3D(filters=8, kernel_size=(3, 5, 5), strides=(1, 2, 2), activation='relu')(x)
    x = Convolution3D(filters=8, kernel_size=(1, 5, 5), strides=(1, 2, 2), activation='relu')(x)
    x = Convolution3D(filters=8, kernel_size=(1, 5, 5), strides=(1, 2, 2), activation='relu')(x)
    x = Convolution3D(filters=8, kernel_size=(1, 3, 3), strides=(1, 2, 2), activation='relu')(x)
    x = Convolution3D(filters=8, kernel_size=(1, 3, 3), strides=(1, 1, 1), activation='relu')(x)
    x = Convolution3D(filters=8, kernel_size=(1, 3, 3), strides=(1, 1, 1), activation='relu')(x)
    x = Convolution3D(filters=8, kernel_size=(1, 3, 3), strides=(1, 1, 1), activation='relu')(x)

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
                  loss_weights={'angle_out': 0.5, 'throttle_out': .5})

    return model

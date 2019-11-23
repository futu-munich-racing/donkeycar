# -*- coding: utf-8 -*-
"""03b_train_donkey_model_with_custom_generator.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1Q_nMiMmkCc8vWeqOVVowqj99Lz6anhNm

# Training a model for donkey car
"""
import glob, os, json
import argparse

import numpy as np

from tensorflow.python.keras.layers import Input
from tensorflow.python.keras.models import Model, load_model
from tensorflow.python.keras.layers import Convolution2D, Convolution3D
from tensorflow.python.keras.layers import MaxPooling2D, MaxPooling3D
from tensorflow.python.keras.activations import relu
from tensorflow.python.keras.layers import Dropout, Flatten, Dense
from tensorflow.python.keras.layers import Cropping2D, Cropping3D
from tensorflow.python.keras.callbacks import ModelCheckpoint, EarlyStopping
import tensorflow as tf
print('tensorflow: ', tf.__version__)

from tensorflow import keras
from tensorflow.keras.preprocessing.image import load_img
print('keras: ', keras.__version__)

class DataGenerator(keras.utils.Sequence):
    'Generates data for Keras'
    def __init__(self, records, data_dir, batch_size=32, img_dim=(256, 360),
                 grayscale=False, n_history=1, shuffle=False):
        'Initialization'
        self.records = records # List of dictionaries
        self.data_dir = data_dir # Directory containing datas
        self.batch_size = batch_size 
        self.img_dim = img_dim
        self.grayscale = grayscale
        self.n_history = n_history
        self.shuffle = shuffle
        self.on_epoch_end()

    def __len__(self):
        'Denotes the number of batches per epoch'
        return int(np.floor(len(self.records) / self.batch_size))

    def __getitem__(self, index):
        'Generate one batch of data'
        # Generate indexes of the batch
        indexes = self.indexes[index*self.batch_size:(index+1)*self.batch_size]

        # Generate data
        X, y = self.__data_generation(indexes)

        return X, y

    def on_epoch_end(self):
        'Updates indexes after each epoch'
        self.indexes = np.arange(len(self.records))
        if self.shuffle == True:
            np.random.shuffle(self.indexes)

    def __data_generation(self, indexes):
        'Generates data containing batch_size samples' # X : (n_samples, *dim, n_channels)
        # Initialization
        if self.n_history == 1:
          X = np.empty((self.batch_size, *self.img_dim), dtype=int)
        else:
          X = np.empty((self.batch_size, self.n_history, *self.img_dim), dtype=int)
        y1 = np.empty((self.batch_size), dtype=float)
        y2 = np.empty((self.batch_size), dtype=float)

        # Generate data
        for i, ix in enumerate(indexes):
          if self.n_history == 1:
            img = tf.io.read_file(os.path.join(self.data_dir,
                                              self.records[ix]['img_path']))
            img = decode_img(img, self.img_dim[:2])
            X[i, ] = img
          else:
            # TODO: In the future, we need to have history of images here
            for j in range(0, self.n_history):
              img_ix = max(ix - j, 0)
              # Store sample  
              img = tf.io.read_file(os.path.join(self.data_dir,
                                                self.records[ix]['img_path']))
              img = decode_img(img, self.img_dim[:2])
              X[i, j, :, :] = img
          # Store class
          y1[i] = self.records[ix]['user/angle']
          y2[i] = self.records[ix]['user/throttle']

        return X, [y1, y2]

def decode_img(img, target_size):
  # convert the compressed string to a 3D uint8 tensor
  img = tf.image.decode_jpeg(img, channels=3)
  # Use `convert_image_dtype` to convert to floats in the [0,1] range.
  img = tf.image.convert_image_dtype(img, tf.float32)
  # resize the image to the desired size.
  return tf.image.resize(img, [target_size[1], target_size[0]]).numpy()

def load_tub_data_to_records(data_dir):
  tub_dirs = glob.glob(os.path.join(data_dir, 'tub*'))
  tub_dirs.sort()
  tub_dirs = [tub_dir for tub_dir in tub_dirs]
  print(tub_dirs)
  records = []
  for tub_dir in tub_dirs:
      json_files = glob.glob(os.path.join(tub_dir, 'record_*.json'))
      if len(json_files) == 0:
          tub_dir = os.path.join(tub_dir, 'tub')
          json_files = glob.glob(os.path.join(tub_dir, 'record_*.json'))
      n = len(json_files)
      #for json_file in json_files:
      #for i in range(0, n):
      i = 0
      cnt = 0
      while cnt < n:
          json_file = os.path.join(tub_dir, 'record_%d.json' % i)
          #print(json_file)
          try:
              data = json.load(open(json_file, 'r'))
              data['img_path'] = os.path.join(os.path.basename(tub_dir), data['cam/image_array'])
              records.append(data)
              cnt += 1
          except:
              #print('file missing: %s' % json_file)
              pass
          i += 1
  return records

"""## Define model"""

#
# 3d model with temporal dimension
#
def create_3d_model(img_dims, n_images_history, crop_margin_from_top=80):
  tf.keras.backend.clear_session()

  img_in = Input(shape=(n_images_in_history, *img_dims), name='img_in')

  x = img_in

  x = Cropping3D(((0, 0), (crop_margin_from_top, 0), (0, 0)))(x)

  # Define convolutional neural network to extract features from the images
  if n_images_in_history > 2:
    x = Convolution3D(filters=24, kernel_size=(3, 5, 5), strides=(1, 2, 2), activation='relu')(x)
  else:
    x = Convolution3D(filters=24, kernel_size=(1, 5, 5), strides=(1, 2, 2), activation='relu')(x)
  x = Convolution3D(filters=32, kernel_size=(1, 5, 5), strides=(1, 2, 2), activation='relu')(x)
  x = Convolution3D(filters=64, kernel_size=(1, 5, 5), strides=(1, 2, 2), activation='relu')(x)
  x = Convolution3D(filters=64, kernel_size=(1, 3, 3), strides=(1, 2, 2), activation='relu')(x)
  x = Convolution3D(filters=64, kernel_size=(1, 3, 3), strides=(1, 1, 1), activation='relu')(x)

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

#
# 3d model with temporal dimension
#
def create_3d3_model(img_dims, n_images_history, crop_margin_from_top=80):
  tf.keras.backend.clear_session()

  img_in = Input(shape=(n_images_in_history, *img_dims), name='img_in')

  x = img_in

  x = Cropping3D(((0, 0), (crop_margin_from_top, 0), (0, 0)))(x)

  # Define convolutional neural network to extract features from the images
  if n_images_in_history > 2:
    x = Convolution3D(filters=24, kernel_size=(3, 5, 5), strides=(1, 2, 2),
                      padding='same', activation='relu')(x)
  else:
    x = Convolution3D(filters=24, kernel_size=(3, 5, 5), strides=(1, 2, 2),
                      padding='same', activation='relu')(x)
  x = Convolution3D(filters=32, kernel_size=(3, 5, 5), strides=(1, 2, 2), 
                    padding='same', activation='relu')(x)
  x = Convolution3D(filters=64, kernel_size=(3, 5, 5), strides=(1, 2, 2), 
                    padding='same', activation='relu')(x)
  x = Convolution3D(filters=64, kernel_size=(3, 3, 3), strides=(1, 2, 2), 
                    padding='same', activation='relu')(x)
  x = Convolution3D(filters=64, kernel_size=(3, 3, 3), strides=(1, 1, 1), 
                    padding='same', activation='relu')(x)

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

#
# This should be the standard model
#
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
                loss_weights={'angle_out': 0.9,
                              'throttle_out': 0.1},
                metrics=['mse', 'mae', 'mape'])
  
  return model


#
# This should be the standard model
#
def create_super_simple_2d_model(img_dims, crop_margin_from_top=80):
  tf.keras.backend.clear_session()

  img_in = Input(shape=(img_dims), name='img_in')

  x = img_in

  x = Cropping2D(((crop_margin_from_top, 0), (0, 0)))(x)

  # Define convolutional neural network to extract features from the images
  x = Convolution2D(filters=24, kernel_size=(5, 5))(x)
  x = relu(x)
  x = MaxPooling2D(pool_size=(2, 2))(x)

  x = Convolution2D(filters=24, kernel_size=(3, 3), activation='relu')(x)
  x = MaxPooling2D(pool_size=(2, 2))(x)
  x = relu(x)

  #x = Convolution2D(filters=24, kernel_size=(3, 3), activation='relu')(x)
  #x = MaxPooling2D(pool_size=(2, 2))(x)
  #x = relu()(x)

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

def train(params):

  datadir = 'data/'

  model_file_name = "23_tampere_super_simple" #@param {type:"string"}

  image_width = 180 #@param {type:"slider", min:32, max:1024, step:1}
  image_height = 120 #@param {type:"slider", min:32, max:1024, step:1}
  image_colours = True #@param {type:"boolean"}
  n_images_in_history = 1 #@param {type:"slider", min:1, max:10, step:1}

  epochs = 100 #@param {type:"slider", min:1, max:1000, step:1}
  steps = 100 #@param {type:"slider", min:1, max:1000, step:1}
  batch_size = 128 #@param {type:"slider", min:32, max:1024, step:2}

  verbose = True #@param {type:"boolean"}
  min_delta = .0005 #@param {type:"slider", min:0, max:1, step:0.00001}
  patience = 5 #@param {type:"slider", min:2, max:10, step:1}
  use_early_stop=True #@param {type:"boolean"}

  weight_loss_angle = 1 #@param {type:"slider", min:0, max:1, step:0.1}
  weight_loss_throttle = 0 #@param {type:"slider", min:0, max:1, step:0.1}


  # Fix image dim parameters
  if image_colours:
    img_dims = (image_height, image_width, 3)
  else:
    img_dims = (image_height, image_width, 1)

  """### Generate dataframes from train and validation datadirs"""

  train_records = load_tub_data_to_records('data/train/')

  val_records = load_tub_data_to_records('data/val')
  
  print(len(train_records), len(train_records))

  """### Data generators"""

  train_generator = DataGenerator(train_records,
                                  data_dir='data/train',
                                  batch_size=batch_size,
                                  img_dim=img_dims,
                                  grayscale=image_colours==True,
                                  n_history=n_images_in_history,
                                  shuffle=True)

  val_generator = DataGenerator(val_records,
                                data_dir='data/val',
                                batch_size=batch_size,
                                img_dim=img_dims,
                                grayscale=image_colours==True,
                                n_history=n_images_in_history,
                                shuffle=False)

  """### ModelCheckpoint and EarlyStop"""

  saved_model_path = os.path.join(datadir, 'models', model_file_name)

  print('model will be stored to: %s' % saved_model_path)

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
      
  model = create_2d_model(img_dims, crop_margin_from_top=int(img_dims[0]/5))

  history = model.fit_generator(generator=train_generator,
                                validation_data=val_generator,
                                use_multiprocessing=False,
                                callbacks=[save_best, early_stop],
                                epochs=epochs)


if __name__ == '__main__':
    #use_valohai_input()

    parser = argparse.ArgumentParser()
    parser.add_argument('--batch_size', type=int)
    parser.add_argument('--num_classes', type=int)
    parser.add_argument('--epochs', type=int)
    parser.add_argument('--data_augmentation', type=bool, nargs='?', const=True)
    cli_parameters, unparsed = parser.parse_known_args()
    train(cli_parameters)
from keras import applications
from keras.preprocessing.image import ImageDataGenerator
from keras import optimizers
from keras.callbacks import TensorBoard
from keras.models import Model
from keras.layers import Dense, GlobalAveragePooling2D

# based on
# https://www.kaggle.com/ogurtsov/0-99-with-r-and-keras-inception-v3-fine-tune/code

# Settings

train_directory = 'data/train'
validation_directory = 'data/validation'

img_width, img_height = 299, 299
batch_size = 32
train_epochs = 60
fine_tune_epochs = 20
train_samples = 3064
validation_samples = 400

# Data generators & augmentation

datagen = ImageDataGenerator(
    rotation_range=20,
    width_shift_range=0.2,
    height_shift_range=0.2,
    horizontal_flip=True)

train_generator = datagen.flow_from_directory(
    train_directory,
    target_size=(img_height, img_width),
    color_mode='rgb',
    class_mode='binary',
    batch_size=batch_size,
    shuffle=True,
    seed=123)

validation_generator = datagen.flow_from_directory(
    validation_directory,
    target_size=(img_height, img_width),
    color_mode='rgb',
    classes=None,
    class_mode='binary',
    batch_size=batch_size,
    shuffle=True,
    seed=123)

# Loading pre-trained model and adding custom layers

base_model = applications.InceptionV3(weights='imagenet',
                                      include_top=False,
                                      input_shape=(img_height, img_width, 3))
print('Model loaded.')

# Custom layers
x = base_model.output
x = GlobalAveragePooling2D()(x)
x = Dense(1024, activation='relu')(x)
predictions = Dense(1, activation='sigmoid')(x)
model = Model(inputs=base_model.input, outputs=predictions)

for layer in base_model.layers:
    layer.trainable = False

model.compile(
    loss='binary_crossentropy',
    optimizer=optimizers.RMSprop(lr=0.01, decay=0.00004),
    metrics=['accuracy'])

# train the model on the new data for a few epochs
tensorboard = TensorBoard(
    log_dir='./logs/training',
    histogram_freq=1,
    write_graph=True,
    write_images=True)

model.fit_generator(
    train_generator,
    steps_per_epoch=train_samples // batch_size,
    epochs=train_epochs,
    validation_data=validation_generator,
    validation_steps=validation_samples // batch_size,
    verbose = 1,
    callbacks=[tensorboard])

model.save_weights('seeds_split.h5')

for layer in model.layers[:249]:
   layer.trainable = False
for layer in model.layers[249:]:
   layer.trainable = True

model.compile(
    loss='binary_crossentropy',
    optimizer=optimizers.RMSprop(lr=0.0001, decay=0.00004),
    metrics=['accuracy'])

tensorboard = TensorBoard(
    log_dir='./logs/fine-tuning',
    histogram_freq=1,
    write_graph=True,
    write_images=True)

model.fit_generator(
    train_generator,
    steps_per_epoch=train_samples // batch_size,
    epochs=fine_tune_epochs,
    validation_data=validation_generator,
    validation_steps=validation_samples // batch_size,
    verbose = 1,
    callbacks=[tensorboard])

model.save_weights('seeds_split_fine_tuned.h5')
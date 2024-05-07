import numpy as np
import pandas as pd 
from tensorflow.keras.preprocessing.image import load_img, ImageDataGenerator
import tensorflow as tf
from keras.utils import to_categorical
from keras.models import Sequential
from keras.layers import Conv2D, MaxPooling2D, Dropout, Flatten, Dense, Activation, BatchNormalization
from sklearn.model_selection import train_test_split
from keras.callbacks import EarlyStopping, ReduceLROnPlateau
import matplotlib.pyplot as plt
import cv2
import random
import os
import keras
from keras.applications import ResNet50
from sklearn.metrics import confusion_matrix
import seaborn as sns


FAST_RUN = False
IMAGE_WIDTH=128
IMAGE_HEIGHT=72
IMAGE_SIZE=(IMAGE_WIDTH, IMAGE_HEIGHT)
IMAGE_CHANNELS=3

base_folder = '.\Sports-Type-Classifier-master\data'

data_list = []


def convert_images_to_grayscale(folder_path):
    
    items = os.listdir(folder_path)
    for item in items:
            item_path = os.path.join(folder_path, item)
            
            if os.path.isdir(item_path):
                convert_images_to_grayscale(item_path)
            elif os.path.isdir(folder_path):
                if item.endswith(".jpg") or item.endswith(".png"):
                    img = cv2.imread(item_path)
                    
                    
                    gray_img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                    
                    output_path = os.path.join(folder_path, f"gray_{item}")
                    print(output_path)
                    cv2.imwrite(output_path, gray_img)



# for folder_name in os.listdir(base_folder):
#     folder_path = os.path.join(base_folder, folder_name)
#     if os.path.isdir(folder_path):         
#         file_names = os.listdir(folder_path)
#         for file_name in file_names:
#             if file_name.startswith("gray_"):
#                 os.remove(os.path.join(folder_path, file_name))
           
            
                

for folder_name in os.listdir(base_folder):
    folder_path = os.path.join(base_folder, folder_name)
    if os.path.isdir(folder_path):         
        file_names = os.listdir(folder_path)
        for file_name in file_names:
            if "gray"  in file_name:
                data_list.extend([(folder_name + "/" + file_name, folder_name)])






df = pd.DataFrame(data_list, columns=['filenames', 'category'])
print(df)

# model = Sequential()

# model.add(Conv2D(32, (3, 3), activation='relu', input_shape=(IMAGE_WIDTH, IMAGE_HEIGHT, IMAGE_CHANNELS)))
# model.add(BatchNormalization())
# model.add(MaxPooling2D(pool_size=(2, 2)))
# model.add(Dropout(0.2))

# model.add(Conv2D(64, (3, 3), activation='relu'))
# model.add(BatchNormalization())
# model.add(MaxPooling2D(pool_size=(2, 2)))
# model.add(Dropout(0.2))

# model.add(Conv2D(128, (3, 3), activation='relu'))
# model.add(BatchNormalization())
# model.add(MaxPooling2D(pool_size=(2, 2)))
# model.add(Dropout(0.2))

# model.add(Flatten())
# model.add(Dense(512, activation='relu'))
# model.add(BatchNormalization())
# model.add(Dropout(0.2))
# model.add(Dense(22, activation='softmax'))

# model.compile(loss='categorical_crossentropy', optimizer='adam', metrics=['accuracy'])

# model.summary()


earlystop = EarlyStopping(patience=10)

learning_rate_reduction = ReduceLROnPlateau(monitor='val_acc', 
                                            patience=2, 
                                            verbose=1, 
                                            factor=0.5, 
                                            min_lr=0.00001)

callbacks = [earlystop, learning_rate_reduction]




train_df, validate_df = train_test_split(df, test_size=0.20, random_state=42)
train_df = train_df.reset_index(drop=True)
validate_df = validate_df.reset_index(drop=True)

total_train = train_df.shape[0]
total_validate = validate_df.shape[0]
batch_size=30


train_datagen = ImageDataGenerator(
    rotation_range=15,
    rescale=1./255,
    shear_range=0.1,
    zoom_range=0.2,
    horizontal_flip=True,
    width_shift_range=0.1,
    height_shift_range=0.1
)


train_generator = train_datagen.flow_from_dataframe(
    train_df, 
    "./Sports-Type-Classifier-master/data/", 
    x_col='filenames',
    y_col='category',
    target_size=IMAGE_SIZE,
    class_mode='categorical',
    batch_size=batch_size,
    
)




validation_datagen = ImageDataGenerator(rescale=1./255)
validation_generator = validation_datagen.flow_from_dataframe(
    validate_df, 
    "./Sports-Type-Classifier-master/data/", 
    x_col='filenames',
    y_col='category',
    target_size=IMAGE_SIZE,
    class_mode='categorical',
    batch_size=batch_size,
    
)

example_df = train_df.sample(n=200)
example_generator = train_datagen.flow_from_dataframe(
    example_df, 
    "./Sports-Type-Classifier-master/data/",  
    x_col='filenames',
    y_col='category',
    target_size=IMAGE_SIZE,
    class_mode='categorical',
    
    
)

base_model = ResNet50(weights='imagenet', include_top=False, input_shape=(IMAGE_WIDTH, IMAGE_HEIGHT, IMAGE_CHANNELS))

inputs= keras.Input(shape=(IMAGE_WIDTH, IMAGE_HEIGHT, IMAGE_CHANNELS))
x= base_model(inputs, training=False)
x= keras.layers.GlobalAveragePooling2D()(x)
outputs= keras.layers.Dense(22, activation='softmax')(x)
model= keras.Model(inputs, outputs)

model.compile(optimizer='adam', loss='categorical_crossentropy', metrics=['accuracy'])


epochs=3 if FAST_RUN else 50

history = model.fit(
    train_generator, 
    epochs=epochs,
    validation_data=validation_generator,
    validation_steps=total_validate//batch_size,
    steps_per_epoch=total_train//batch_size,
    
)



# Dokładność
plt.plot(history.history['accuracy'])
plt.plot(history.history['val_accuracy'])
plt.title('Model Accuracy')
plt.xlabel('Epoch')
plt.ylabel('Accuracy')
plt.legend(['Train', 'Validation'], loc='upper left')
plt.show()

# Strata (loss)
plt.plot(history.history['loss'])
plt.plot(history.history['val_loss'])
plt.title('Model Loss')
plt.xlabel('Epoch')
plt.ylabel('Loss')
plt.legend(['Train', 'Validation'], loc='upper left')
plt.show()



num_predictions = 20


num_rows = 4
num_cols = 5
fig, axes = plt.subplots(num_rows, num_cols, figsize=(12, 10))


for i in range(num_predictions):
    example = next(example_generator)
    image = example[0][0] 
    label = example[1][0]  

    
    prediction = model.predict(np.expand_dims(image, axis=0))
    predicted_class = np.argmax(prediction)

   
    row = i // num_cols
    col = i % num_cols
    axes[row, col].imshow(image)
    axes[row, col].axis('off')
    axes[row, col].set_title(f'Actual: {np.argmax(label)}, Predicted: {predicted_class}')


for j in range(num_predictions, num_rows * num_cols):
    row = j // num_cols
    col = j % num_cols
    axes[row, col].axis('off')
    axes[row, col].set_visible(False)

plt.tight_layout()
plt.show()

# Macierez konfuzji
y_pred = model.predict(validation_generator)
y_pred_classes = np.argmax(y_pred, axis=-1)

x_true = validation_generator.classes

conf_matrix = confusion_matrix(x_true, y_pred_classes)

labels = (train_generator.class_indices)
class_names = labels


fig = plt.figure(figsize=(16, 14))
ax= plt.subplot()
sns.heatmap(conf_matrix, annot=True, ax = ax, fmt = 'g');

ax.set_xlabel('Predicted', fontsize=20)
ax.xaxis.set_label_position('bottom')
plt.xticks(rotation=90)
ax.xaxis.set_ticklabels(class_names, fontsize = 10)
ax.xaxis.tick_bottom()

ax.set_ylabel('True', fontsize=20)
ax.yaxis.set_ticklabels(class_names, fontsize = 10)
plt.yticks(rotation=0)

plt.title('Refined Confusion Matrix', fontsize=20)

plt.savefig('ConMat24.png')
plt.show()
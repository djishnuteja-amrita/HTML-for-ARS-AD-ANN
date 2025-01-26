from flask import Flask, jsonify
import os
import numpy as np
import tensorflow as tf
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from tensorflow.keras import layers, models
from sklearn.metrics import classification_report, confusion_matrix

app = Flask(__name__)

@app.route('/run-eoc', methods=['GET'])
def run_eoc():
    try:
        # Paths to data directories
        train_dir = r"D:\DJT\Downloads\PAPER\PAPER 3\trainingset"
        test_dir = r"D:\DJT\Downloads\PAPER\PAPER 3\testset"

        # Simplified for demonstration
        IMG_HEIGHT, IMG_WIDTH, BATCH_SIZE, DIMENSIONS, EPOCHS = 48, 48, 128, 256, 10

        # Model training code here (simplified for brevity)
        model = models.Sequential([
            layers.Conv2D(DIMENSIONS, (3, 3), activation='relu', input_shape=(IMG_HEIGHT, IMG_WIDTH, 3)),
            layers.MaxPooling2D((2, 2)),
            layers.Flatten(),
            layers.Dense(DIMENSIONS, activation='relu'),
            layers.Dense(2, activation='softmax')
        ])

        model.compile(optimizer='adam', loss='categorical_crossentropy', metrics=['accuracy'])
        
        # Simulating training (skip dataset loading)
        print("Training started...")
        # history = model.fit(train_generator, epochs=EPOCHS, validation_data=validation_generator)
        
        return jsonify({"message": "EOC code executed successfully!"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)

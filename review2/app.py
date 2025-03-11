from flask import Flask, render_template, request, jsonify
import numpy as np
import tensorflow as tf
from scipy.signal import StateSpace, lsim
import matplotlib.pyplot as plt
import os

app = Flask(__name__)

# Create 'static' folder if it doesn't exist
os.makedirs("static", exist_ok=True)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/run", methods=["POST"])
def run_simulation():
    # Define system parameters
    dt = 0.01  
    T = 10     
    time = np.arange(0, T, dt)

    # System component parameters
    Rf, Lf, Cf = 0.05, 1.5e-3, 1500e-6
    Rc, Lc, Cc = 0.11, 1.25e-3, 10e-6

    # Define state-space matrices
    A = np.array([
        [0, 1, 0, 0, 0, 0],
        [-1, -0.5, 0, 0, 0, 0],
        [0, 0, -Rf/Lf, -1/Lf, 0, 0],
        [0, 0, 1/Cf, 0, -1/Cf, 0],
        [0, 0, 0, 1/Lc, -Rc/Lc, -1/Lc],
        [0, 0, 0, 0, 1/Cc, 0]
    ])

    B = np.array([[0], [1], [1/Lf], [0], [0], [0]])
    C = np.array([[1, 0, 0, 0, 0, 0]])
    D = np.array([[0]])

    # Create state-space system model
    system = StateSpace(A, B, C, D)

    # Generate input voltage signal
    input_signal = np.sin(0.5 * time) + 0.1 * np.random.randn(len(time))

    # Simulate system response
    _, y, x = lsim(system, U=input_signal, T=time)

    # Prepare training data
    X_train = np.column_stack((x[:-1, 0], x[:-1, 1], input_signal[:-1]))
    y_train = x[1:, 0]

    # Define ANN model
    model = tf.keras.Sequential([
        tf.keras.layers.Dense(16, activation='relu', input_shape=(3,)),
        tf.keras.layers.Dense(16, activation='relu'),
        tf.keras.layers.Dense(1)
    ])
    model.compile(optimizer='adam', loss='mse')

    # Train ANN model
    history = model.fit(X_train, y_train, epochs=100, batch_size=32, verbose=0)  # Store history
    plt.plot(history.history['loss'], label='Training Loss')  # Access loss correctly


    # Simulate response without ANN
    _, output_voltage_without_ann, _ = lsim(system, U=input_signal, T=time)

    # Simulate response with ANN
    output_voltage_with_ann = []
    for t in range(len(time)):
        predicted_voltage = model.predict(
            np.array([[output_voltage_without_ann[t-1] if t > 0 else 0, 0, input_signal[t]]]), verbose=0
        )
        output_voltage_with_ann.append(predicted_voltage[0][0])

    # Generate plots and save them
    plot_files = []

    plt.figure(figsize=(12, 6))
    plt.plot(time, output_voltage_without_ann, label='Without ANN', linestyle='dashed', color='r')
    plt.plot(time, output_voltage_with_ann, label='With ANN', linestyle='solid', color='b')
    plt.xlabel('Time (s)')
    plt.ylabel('Output Voltage')
    plt.title('Output Voltage Comparison')
    plt.legend()
    output_file = "static/output_voltage.png"
    plt.savefig(output_file)
    plt.close()
    plot_files.append(output_file)

    plt.figure(figsize=(12, 5))
    plt.plot(model.history.history['loss'], label='Training Loss')
    plt.xlabel('Epochs')
    plt.ylabel('Loss')
    plt.title('ANN Training Performance')
    plt.legend()
    loss_file = "static/loss_plot.png"
    plt.savefig(loss_file)
    plt.close()
    plot_files.append(loss_file)

    return jsonify({"plots": plot_files})

if __name__ == "__main__":
    app.run(debug=True)

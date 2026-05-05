import numpy as np
import tensorflow as tf
from tensorflow import keras
import matplotlib.pyplot as plt
import os

# ── Load data ─────────────────────────────────────────────────
X_train = np.load('saved/X_train.npy')
X_val   = np.load('saved/X_val.npy')

print(f"X_train: {X_train.shape}  X_val: {X_val.shape}\n")

# ── Build FPGA-safe autoencoder ───────────────────────────────

inputs = keras.Input(shape=(128,), name='input_layer')

# Encoder
x = keras.layers.Dense(64, activation='relu', name='enc1')(inputs)
x = keras.layers.Dense(32, activation='relu', name='enc2')(x)

# Bottleneck
x = keras.layers.Dense(32, activation='relu', name='bottleneck')(x)

# Decoder
x = keras.layers.Dense(32, activation='relu', name='dec1')(x)
x = keras.layers.Dense(64, activation='relu', name='dec2')(x)

# Output
outputs = keras.layers.Dense(128, activation='linear', name='output')(x)

# Model
model = keras.Model(inputs, outputs, name='autoencoder')

model.compile(
    optimizer=keras.optimizers.Adam(learning_rate=0.001),
    loss='mse'
)

model.summary()

# ── Train ─────────────────────────────────────────────────────
callbacks = [
    keras.callbacks.EarlyStopping(
        monitor='val_loss',
        patience=15,
        restore_best_weights=True,
        verbose=1
    ),
    keras.callbacks.ReduceLROnPlateau(
        monitor='val_loss',
        factor=0.5,
        patience=7,
        min_lr=1e-6,
        verbose=1
    )
]

print("Training started...\n")

history = model.fit(
    X_train, X_train,
    validation_data=(X_val, X_val),
    epochs=200,
    batch_size=32,
    callbacks=callbacks,
    verbose=1
)

# ── Save model ────────────────────────────────────────────────
os.makedirs('saved', exist_ok=True)
model.save('saved/autoencoder.h5')

# ── Plot loss ─────────────────────────────────────────────────
plt.figure(figsize=(9, 4))
plt.plot(history.history['loss'], label='Train loss')
plt.plot(history.history['val_loss'], label='Validation loss')
plt.legend()
plt.xlabel('Epoch')
plt.ylabel('MSE')
plt.title('Training curve')
plt.tight_layout()
plt.savefig('saved/training_curve.png')
plt.show()

# ── Threshold ────────────────────────────────────────────────
val_recon  = model.predict(X_val, verbose=0)
val_errors = np.mean((X_val - val_recon) ** 2, axis=1)

threshold = np.percentile(val_errors, 99)
np.save('saved/threshold.npy', threshold)

print(f"\nThreshold: {threshold:.6f}")
print("Done.")

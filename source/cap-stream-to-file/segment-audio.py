import librosa
import numpy as np
import ruptures as rpt
from pydub import AudioSegment

# ==== 1. Load the MP3 ====
mp3_path = "spyfm_capture.mp3"

# librosa loads audio as mono float32 array
y, sr = librosa.load(mp3_path, sr=None)

# ==== 2. Extract feature time-series ====
# Use chroma (captures harmonic content) for song transitions
chroma = librosa.feature.chroma_cqt(y=y, sr=sr)
chroma_mean = np.mean(chroma, axis=0)  # average per frame

# ==== 3. Change-point detection with ruptures ====
# Window length of each chroma frame (hop_length=512 samples)
frame_hop = 512
seconds_per_frame = frame_hop / sr

# We use "kernel" method for smooth segmentation
algo = rpt.KernelCPD(kernel="linear").fit(chroma_mean.reshape(-1, 1))

# Estimated number of segments (adjust as needed)
# If unsure, you can also use a penalty: algo.predict(pen=10)
change_points = algo.predict(n_bkps=10)  # number of breakpoints to try

# ==== 4. Convert frame indexes to time (ms for pydub) ====
boundaries_sec = [cp * seconds_per_frame for cp in change_points]
boundaries_ms = [int(s * 1000) for s in boundaries_sec]

# ==== 5. Split the original MP3 ====
audio = AudioSegment.from_mp3(mp3_path)

start = 0
for i, end in enumerate(boundaries_ms):
    segment = audio[start:end]
    segment.export(f"track_{i+1:03d}.mp3", format="mp3")
    print(f"Exported track_{i+1:03d}.mp3  ({(end-start)/1000:.1f}s)")
    start = end

print("✅ Segmentation complete!")
# Result: Run-time errors


# Deps:
# pip install librosa ruptures pydub soundfile numpy

import essentia
import essentia.standard as es
import os

mp3_path = "spyfm_capture.mp3"

import essentia.standard as es
import os

def split_mp3_by_silence(input_file, output_dir, rms_threshold=0.01, min_silence_dur=2.0, frame_size=1024, hop_size=512):
    """
    Splits an MP3 into segments based on silence using RMS energy in Essentia.

    :param input_file: Path to the MP3 file.
    :param output_dir: Directory to save split segments.
    :param rms_threshold: Threshold below which audio is considered silence.
    :param min_silence_dur: Minimum silence duration (seconds) to be considered a split point.
    :param frame_size: Frame size for RMS calculation.
    :param hop_size: Hop size for RMS calculation.
    """

    os.makedirs(output_dir, exist_ok=True)

    # Load audio
    loader = es.MonoLoader(filename=input_file)
    audio = loader()
    sample_rate = loader.paramValue('sampleRate')

    # Frame generator
    frame_gen = es.FrameGenerator(audio, frameSize=frame_size, hopSize=hop_size, startFromZero=True)

    # Silence detection
    rms = es.RMS()
    silence_points = []
    times = []
    for i, frame in enumerate(frame_gen):
        energy = rms(frame)
        time = (i * hop_size) / sample_rate
        times.append(time)
        if energy < rms_threshold:
            silence_points.append(time)

    # Build segments based on silence durations
    segments = []
    start_time = 0.0
    prev_time = 0.0

    for t in silence_points:
        if t - prev_time >= min_silence_dur:
            segments.append((start_time, prev_time))
            start_time = t
        prev_time = t

    # Add last segment
    if start_time < len(audio) / sample_rate:
        segments.append((start_time, len(audio) / sample_rate))

    print(f"Detected {len(segments)} segments. Exporting...")

    # Write segments
    for i, (start, end) in enumerate(segments, start=1):
        out_file = f"{output_dir}/track_{i}.wav"
        print(f"Saving {out_file} from {start:.2f}s to {end:.2f}s...")
        writer = es.AudioWriter(filename=out_file, format='wav', sampleRate=sample_rate)
        writer(audio[int(start * sample_rate):int(end * sample_rate)])


# Example usage
split_mp3_by_silence(
    input_file="spyfm_capture.mp3",
    output_dir="tracks",
    rms_threshold=0.01,
    min_silence_dur=2.0
)

if __name__ == "__main__":
    split_mp3_by_silence
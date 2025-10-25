
import numpy as np
import librosa
import soundfile as sf
from pydub import AudioSegment
from scipy.signal import find_peaks
import os

class AudioSplitter:
    def __init__(self, input_file):
        self.input_file = input_file
        self.y = None
        self.sr = None
        
    def load_audio(self):
        """Load audio file using librosa for analysis"""
        print(f"Loading {self.input_file}...")
        self.y, self.sr = librosa.load(self.input_file, sr=22050)
        print(f"Loaded: duration={len(self.y)/self.sr:.2f}s, sample_rate={self.sr}Hz")
        
    def detect_boundaries_spectral(self, sensitivity=0.5):
        """
        Detect song boundaries using spectral features
        
        Args:
            sensitivity: 0.0 to 1.0, higher = more sensitive (more splits)
        Returns:
            List of boundary timestamps in seconds
        """
        print("Analyzing spectral content...")
        
        # 1. Onset strength detection (detects sudden energy increases)
        onset_env = librosa.onset.onset_strength(y=self.y, sr=self.sr)
        
        # 2. Spectral flux (measures changes in frequency content)
        spectral_flux = self._calculate_spectral_flux()
        
        # 3. RMS energy (volume changes)
        rms = librosa.feature.rms(y=self.y)[0]
        
        # Normalize all features
        onset_env = onset_env / (np.max(onset_env) + 1e-8)
        spectral_flux = spectral_flux / (np.max(spectral_flux) + 1e-8)
        rms = rms / (np.max(rms) + 1e-8)
        
        # Combine features (weighted sum)
        combined = 0.4 * onset_env + 0.4 * spectral_flux + 0.2 * rms
        
        # Smooth the combined signal
        window_size = int(self.sr / 512 * 20)  # ~20 frames
        combined_smooth = np.convolve(combined, np.ones(window_size)/window_size, mode='same')
        
        # Find peaks in the combined feature
        # Adjust height threshold based on sensitivity
        height_threshold = np.percentile(combined_smooth, 100 - (sensitivity * 50))
        distance = int(self.sr / 512 * 50)  # Minimum 50 frames (~2 seconds) between peaks
        
        peaks, properties = find_peaks(
            combined_smooth, 
            height=height_threshold,
            distance=distance,
            prominence=0.1
        )
        
        # Convert frame indices to time
        times = librosa.frames_to_time(peaks, sr=self.sr)
        
        print(f"Found {len(times)} potential boundaries using spectral analysis")
        return times
        
    def _calculate_spectral_flux(self):
        """Calculate spectral flux (change in spectral content over time)"""
        # Compute spectrogram
        S = np.abs(librosa.stft(self.y))
        
        # Calculate differences between consecutive frames
        flux = np.sqrt(np.sum(np.diff(S, axis=1)**2, axis=0))
        
        # Pad to match length
        flux = np.pad(flux, (1, 0), mode='constant')
        
        return flux
        
    def detect_silence_regions(self, silence_thresh=-40, min_silence_len=0.5):
        """
        Detect silent regions in the audio
        
        Returns:
            List of (start, end) tuples for silent regions in seconds
        """
        print("Detecting silence regions...")
        
        # Convert to dB
        rms = librosa.feature.rms(y=self.y)[0]
        rms_db = librosa.amplitude_to_db(rms, ref=np.max)
        
        # Find frames below threshold
        silent_frames = rms_db < silence_thresh
        
        # Convert to time
        frame_times = librosa.frames_to_time(np.arange(len(silent_frames)), sr=self.sr)
        
        # Group consecutive silent frames
        silent_regions = []
        in_silence = False
        start = 0
        
        for i, is_silent in enumerate(silent_frames):
            if is_silent and not in_silence:
                start = frame_times[i]
                in_silence = True
            elif not is_silent and in_silence:
                end = frame_times[i]
                if end - start >= min_silence_len:
                    silent_regions.append((start, end))
                in_silence = False
        
        print(f"Found {len(silent_regions)} silent regions")
        return silent_regions
        
    def combine_boundaries(self, spectral_boundaries, silent_regions, tolerance=2.0):
        """
        Combine spectral boundaries with silence detection
        Prefer splits that occur near silence
        
        Args:
            spectral_boundaries: List of times from spectral analysis
            silent_regions: List of (start, end) tuples for silent regions
            tolerance: How close a spectral boundary must be to silence (seconds)
        """
        print("Combining spectral and silence analysis...")
        
        final_boundaries = []
        
        for boundary in spectral_boundaries:
            # Check if this boundary is near a silent region
            best_split = boundary
            min_distance = float('inf')
            
            for silence_start, silence_end in silent_regions:
                # Check if boundary is within tolerance of this silent region
                if silence_start - tolerance <= boundary <= silence_end + tolerance:
                    # Prefer the middle of the silent region
                    silence_mid = (silence_start + silence_end) / 2
                    distance = abs(boundary - silence_mid)
                    
                    if distance < min_distance:
                        min_distance = distance
                        best_split = silence_mid
            
            final_boundaries.append(best_split)
        
        # Remove duplicates and sort
        final_boundaries = sorted(set(final_boundaries))
        
        print(f"Final boundaries: {len(final_boundaries)} split points")
        return final_boundaries
        
    def split_and_export(self, boundaries, output_folder, format='mp3'):
        """
        Split audio at boundaries and export segments
        """
        os.makedirs(output_folder, exist_ok=True)
        
        # Add start and end points
        all_boundaries = [0] + list(boundaries) + [len(self.y) / self.sr]
        
        print(f"\nExporting {len(all_boundaries)-1} segments...")
        
        for i in range(len(all_boundaries) - 1):
            start_time = all_boundaries[i]
            end_time = all_boundaries[i + 1]
            
            start_sample = int(start_time * self.sr)
            end_sample = int(end_time * self.sr)
            
            segment = self.y[start_sample:end_sample]
            
            duration = (end_sample - start_sample) / self.sr
            output_file = os.path.join(
                output_folder, 
                f"segment_{i+1:03d}_{duration:.1f}s.{format}"
            )
            
            print(f"  {output_file} ({duration:.1f}s)")
            
            # Export using soundfile (WAV) or convert to MP3
            if format == 'mp3':
                # Save as WAV first, then convert
                temp_wav = output_file.replace('.mp3', '.wav')
                sf.write(temp_wav, segment, self.sr)
                
                # Convert to MP3 using pydub
                audio_segment = AudioSegment.from_wav(temp_wav)
                audio_segment.export(output_file, format='mp3', bitrate='192k')
                os.remove(temp_wav)
            else:
                sf.write(output_file, segment, self.sr)
        
        print("\nDone!")


def split_mp3_advanced(input_file, output_folder, sensitivity=0.5, 
                       silence_thresh=-40, use_silence=True):
    """
    Main function to split MP3 using spectral analysis and silence detection
    
    Args:
        input_file: Path to input MP3 file
        output_folder: Where to save segments
        sensitivity: 0.0 to 1.0, how sensitive the spectral detection is
        silence_thresh: dB threshold for silence detection
        use_silence: Whether to combine with silence detection
    """
    splitter = AudioSplitter(input_file)
    splitter.load_audio()
    
    # Get spectral boundaries
    spectral_boundaries = splitter.detect_boundaries_spectral(sensitivity=sensitivity)
    
    if use_silence:
        # Get silence regions
        silent_regions = splitter.detect_silence_regions(
            silence_thresh=silence_thresh,
            min_silence_len=0.5
        )
        
        # Combine both methods
        final_boundaries = splitter.combine_boundaries(
            spectral_boundaries, 
            silent_regions,
            tolerance=2.0
        )
    else:
        final_boundaries = spectral_boundaries
    
    # Export segments
    splitter.split_and_export(final_boundaries, output_folder, format='mp3')
    
    return final_boundaries


# Example usage
if __name__ == "__main__":
    # Advanced splitting with spectral analysis + silence detection
    boundaries = split_mp3_advanced(
        input_file="spyfm_capture.mp3",
        output_folder="output_segments",
        sensitivity=0.6,        # 0.0-1.0: higher = more splits
        silence_thresh=-40,     # dB threshold for silence
        use_silence=True        # Combine spectral + silence analysis
    )
    
    print(f"\nSplit points (seconds): {[f'{b:.2f}' for b in boundaries]}")


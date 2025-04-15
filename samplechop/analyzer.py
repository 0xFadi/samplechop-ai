import librosa
import numpy as np
import matplotlib.pyplot as plt
from typing import List, Tuple, Dict

class SampleAnalyzer:
    def __init__(self, sr: int = 22050, hop_length: int = 512):
        """
        Initialize the Sample Analyzer.
        
        Args:
            sr (int): Sample rate for audio processing
            hop_length (int): Number of samples between successive frames
        """
        self.sr = sr
        self.hop_length = hop_length
        self.audio = None
        self.file_path = None

    def load_audio(self, file_path: str) -> None:
        """
        Load an audio file for analysis.
        
        Args:
            file_path (str): Path to the audio file
        """
        self.file_path = file_path
        self.audio, _ = librosa.load(file_path, sr=self.sr)

    def find_chop_points(self, 
                        threshold: float = 0.5,
                        min_interval: float = 0.2) -> List[Dict]:
        """
        Find potential chopping points in the loaded audio.
        
        Args:
            threshold (float): Energy threshold for detecting significant changes
            min_interval (float): Minimum time (in seconds) between chop points
        
        Returns:
            List[Dict]: List of dictionaries containing chop points and their features
        """
        if self.audio is None:
            raise ValueError("No audio loaded. Call load_audio() first.")

        # Get onset strength
        onset_env = librosa.onset.onset_strength(
            y=self.audio, 
            sr=self.sr,
            hop_length=self.hop_length
        )

        # Find onset frames
        onset_frames = librosa.onset.onset_detect(
            onset_envelope=onset_env,
            sr=self.sr,
            hop_length=self.hop_length,
            threshold=threshold
        )

        # Convert frames to time
        onset_times = librosa.frames_to_time(onset_frames, 
                                           sr=self.sr,
                                           hop_length=self.hop_length)

        # Filter out points that are too close together
        min_samples = int(min_interval * self.sr / self.hop_length)
        filtered_points = []
        last_point = -min_samples

        for frame, time in zip(onset_frames, onset_times):
            if frame - last_point >= min_samples:
                # Get spectral features at this point
                spec_centroid = librosa.feature.spectral_centroid(
                    y=self.audio[frame*self.hop_length:(frame+1)*self.hop_length],
                    sr=self.sr
                ).mean()
                
                rms = librosa.feature.rms(
                    y=self.audio[frame*self.hop_length:(frame+1)*self.hop_length]
                ).mean()

                filtered_points.append({
                    'time': float(time),
                    'frame': int(frame),
                    'energy': float(rms),
                    'spectral_centroid': float(spec_centroid)
                })
                last_point = frame

        return filtered_points

    def visualize_chop_points(self, chop_points: List[Dict]) -> None:
        """
        Visualize the audio waveform with detected chop points.
        
        Args:
            chop_points (List[Dict]): List of detected chop points
        """
        plt.figure(figsize=(15, 5))
        
        # Plot waveform
        times = np.arange(len(self.audio)) / self.sr
        plt.plot(times, self.audio, alpha=0.5, color='blue')
        
        # Plot chop points
        for point in chop_points:
            plt.axvline(x=point['time'], color='red', alpha=0.5)
        
        plt.title('Audio Waveform with Detected Chop Points')
        plt.xlabel('Time (s)')
        plt.ylabel('Amplitude')
        plt.grid(True)
        plt.tight_layout()
        plt.show()

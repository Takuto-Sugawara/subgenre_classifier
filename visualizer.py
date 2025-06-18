import os
import json
import librosa
import numpy as np
import matplotlib.pyplot as plt

class AudioVisualizer:
    def __init__(self, audio_file_path, metadata_file_path, output_file_path):
        self.audio_file_path = audio_file_path
        self.metadata_file_path = metadata_file_path
        self.audio_data, self.sample_rate = self.load_audio()
        self.metadata = self.load_metadata()
        self.output_file_path = output_file_path
    
    def load_audio(self):
        if not os.path.exists(self.audio_file_path):
            raise FileNotFoundError(f"Audio file not found: {self.audio_file_path}")
        pass

    def load_metadata(self):
        if not os.path.exists(self.metadata_file_path):
            raise FileNotFoundError(f"Metadata file not found: {self.metadata_file_path}")
        with open(self.metadata_file_path, 'r') as f:
            metadata = json.load(f)
        return metadata
    
    def make_melspectrogram(self, audio_data, hoge):
        pass
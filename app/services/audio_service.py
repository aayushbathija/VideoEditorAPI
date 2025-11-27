"""
Audio Processing Service for Voice Filters
Provides audio effects like telephone voice filter.
"""

import os
import tempfile
import logging
from scipy.signal import lfilter, butter
from scipy.io.wavfile import read, write
import numpy as np
import moviepy.editor as mp

logger = logging.getLogger(__name__)

class AudioService:
    """Service for audio processing and voice filtering."""
    
    def __init__(self):
        self.supported_filters = {
            'telephone': {
                'name': 'Telephone Voice',
                'description': 'Classic telephone bandpass filter (300-3000Hz)',
                'low_freq': 300.0,
                'high_freq': 3000.0,
                'order': 6
            },
            'radio': {
                'name': 'Radio Voice',
                'description': 'AM radio style filter (300-2500Hz)',
                'low_freq': 300.0,
                'high_freq': 2500.0,
                'order': 5
            },
            'walkie_talkie': {
                'name': 'Walkie Talkie',
                'description': 'Narrow band communication filter (400-2000Hz)',
                'low_freq': 400.0,
                'high_freq': 2000.0,
                'order': 8
            }
        }
    
    def butter_params(self, low_freq, high_freq, fs, order=5):
        """Calculate Butterworth filter parameters."""
        nyq = 0.5 * fs
        low = low_freq / nyq
        high = high_freq / nyq
        
        # Ensure frequencies are within valid range
        if low <= 0 or high >= 1:
            raise ValueError(f"Invalid frequency range: {low_freq}-{high_freq}Hz for sample rate {fs}Hz")
        
        if low >= high:
            raise ValueError(f"Low frequency ({low_freq}) must be less than high frequency ({high_freq})")
        
        b, a = butter(order, [low, high], btype='band')
        return b, a
    
    def butter_bandpass_filter(self, data, low_freq, high_freq, fs, order=5):
        """Apply Butterworth bandpass filter to audio data."""
        try:
            b, a = self.butter_params(low_freq, high_freq, fs, order=order)
            y = lfilter(b, a, data)
            return y
        except Exception as e:
            logger.error(f"Error applying bandpass filter: {e}")
            raise
    
    def apply_voice_filter(self, input_path, output_path, filter_type='telephone'):
        """
        Apply voice filter to an audio or video file.
        
        Args:
            input_path (str): Path to input file (audio or video)
            output_path (str): Path to save filtered output
            filter_type (str): Type of filter to apply ('telephone', 'radio', 'walkie_talkie')
        
        Returns:
            str: Path to the filtered output file
        """
        if filter_type not in self.supported_filters:
            raise ValueError(f"Unsupported filter type: {filter_type}. Available: {list(self.supported_filters.keys())}")
        
        filter_config = self.supported_filters[filter_type]
        logger.info(f"Applying {filter_config['name']} filter to {input_path}")
        
        # Create temporary files for processing
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_audio_path = os.path.join(temp_dir, "temp_audio.wav")
            filtered_audio_path = os.path.join(temp_dir, "filtered_audio.wav")
            
            try:
                # Extract audio from input file (works for both audio and video)
                video = mp.VideoFileClip(input_path)
                audio = video.audio
                
                if audio is None:
                    raise ValueError("Input file has no audio track")
                
                # Export audio as WAV for processing
                audio.write_audiofile(temp_audio_path, logger=None, verbose=False)
                
                # Read audio file
                fs, audio_data = read(temp_audio_path)
                logger.info(f"Audio loaded: {fs}Hz sample rate, {len(audio_data)} samples")
                
                # Handle stereo audio by processing each channel
                if len(audio_data.shape) > 1:
                    filtered_channels = []
                    for channel in range(audio_data.shape[1]):
                        channel_data = audio_data[:, channel]
                        filtered_channel = self.butter_bandpass_filter(
                            channel_data,
                            filter_config['low_freq'],
                            filter_config['high_freq'],
                            fs,
                            order=filter_config['order']
                        )
                        filtered_channels.append(filtered_channel)
                    
                    # Combine channels back
                    filtered_signal = np.column_stack(filtered_channels)
                else:
                    # Mono audio
                    filtered_signal = self.butter_bandpass_filter(
                        audio_data,
                        filter_config['low_freq'],
                        filter_config['high_freq'],
                        fs,
                        order=filter_config['order']
                    )
                
                # Save filtered audio as WAV
                write(filtered_audio_path, fs, np.array(filtered_signal, dtype=np.int16))
                
                # Create output video/audio with filtered audio
                filtered_audio_clip = mp.AudioFileClip(filtered_audio_path)
                
                # Check if input was video or audio
                # Try to determine if it's a video file by checking for video properties
                is_video_file = False
                try:
                    # Check if video has video track (width and height)
                    if hasattr(video, 'w') and hasattr(video, 'h') and video.w and video.h:
                        is_video_file = True
                except AttributeError:
                    # If we can't access video properties, treat as audio-only
                    is_video_file = False
                
                if is_video_file:
                    # Input was video, combine filtered audio with original video
                    final_clip = video.set_audio(filtered_audio_clip)
                    final_clip.write_videofile(
                        output_path,
                        codec='libx264',
                        audio_codec='aac',
                        logger=None,
                        verbose=False
                    )
                else:
                    # Input was audio only, export as audio
                    filtered_audio_clip.write_audiofile(output_path, logger=None, verbose=False)
                
                # Clean up clips
                video.close()
                audio.close()
                filtered_audio_clip.close()
                if 'final_clip' in locals():
                    final_clip.close()
                
                logger.info(f"Voice filter applied successfully: {output_path}")
                return output_path
                
            except Exception as e:
                logger.error(f"Error applying voice filter: {e}")
                raise
    
    def get_supported_filters(self):
        """Get list of supported voice filters with their descriptions."""
        return {
            filter_type: {
                'name': config['name'],
                'description': config['description']
            }
            for filter_type, config in self.supported_filters.items()
        }
    
    def extract_audio_info(self, file_path):
        """Extract basic audio information from a file."""
        try:
            video = mp.VideoFileClip(file_path)
            audio = video.audio
            
            if audio is None:
                return None
            
            info = {
                'duration': audio.duration,
                'has_audio': True
            }
            
            # Try to get fps, but it might not be available for all audio clips
            try:
                if hasattr(audio, 'fps') and audio.fps:
                    info['fps'] = audio.fps
                else:
                    info['fps'] = 44100  # Default sample rate
            except AttributeError:
                info['fps'] = 44100  # Default sample rate
            
            audio.close()
            video.close()
            
            return info
            
        except Exception as e:
            logger.error(f"Error extracting audio info: {e}")
            return None
"""
Voiceover Service for Adding Audio to Video with Duration Matching
Provides functionality to add voiceover audio to video clips with intelligent duration matching.
"""

import os
import logging
import moviepy.editor as mp
from moviepy.video.fx.resize import resize

logger = logging.getLogger(__name__)

class VoiceoverService:
    """Service for adding voiceover audio to video clips with duration matching."""
    
    def __init__(self):
        self.supported_audio_formats = ['.mp3', '.wav', '.aac', '.m4a', '.ogg']
        self.supported_video_formats = ['.mp4', '.avi', '.mov', '.mkv', '.webm']
    
    def get_duration(self, file_path):
        """Get duration of audio or video file."""
        try:
            # Try as video first
            clip = mp.VideoFileClip(file_path)
            duration = clip.duration
            clip.close()
            return duration
        except:
            try:
                # Try as audio
                clip = mp.AudioFileClip(file_path)
                duration = clip.duration
                clip.close()
                return duration
            except Exception as e:
                logger.error(f"Could not get duration for {file_path}: {e}")
                raise ValueError(f"Unable to read media file: {file_path}")
    
    def slow_down_audio(self, audio_clip, target_duration):
        """Slow down audio clip to match target duration."""
        current_duration = audio_clip.duration
        
        if target_duration >= current_duration:
            # If target is longer or equal, no need to slow down
            return audio_clip
        
        # Calculate slowdown factor
        slowdown_factor = target_duration / current_duration
        
        logger.info(f"Slowing down audio by factor of {slowdown_factor:.2f} from {current_duration:.2f}s to {target_duration:.2f}s")
        
        # Apply speed change to audio
        # Use MoviePy's built-in fx method with speedx
        try:
            # Try modern MoviePy import first
            from moviepy.audio.fx import speedx
            slowed_audio = speedx.speedx(audio_clip, slowdown_factor)
        except (ImportError, AttributeError):
            try:
                # Try alternative import path
                from moviepy.audio.fx.speedx import speedx
                slowed_audio = speedx(audio_clip, slowdown_factor)
            except (ImportError, AttributeError):
                try:
                    # Try using fx method directly
                    slowed_audio = audio_clip.fx(mp.afx.speedx, slowdown_factor)
                except AttributeError:
                    # Final fallback: use duration stretching to slow down
                    logger.warning(f"speedx not available, using duration stretching method")
                    # For slowdown, we need to stretch the audio duration
                    # This creates the slowed audio by changing its effective duration
                    slowed_audio = audio_clip.set_duration(target_duration)
                    # Apply pitch correction to maintain audio quality
                    try:
                        # Try to resample to maintain audio quality while stretching
                        original_fps = getattr(audio_clip, 'fps', 44100)
                        slowed_audio = slowed_audio.set_fps(original_fps)
                    except:
                        # If resampling fails, just use the stretched version
                        pass
        
        return slowed_audio
    
    def slow_down_video(self, video_clip, target_duration):
        """Slow down video clip to match target duration."""
        current_duration = video_clip.duration
        
        if target_duration <= current_duration:
            # If target is shorter or equal, no need to slow down
            return video_clip
        
        # Calculate slowdown factor
        slowdown_factor = current_duration / target_duration
        
        logger.info(f"Slowing down video by factor of {slowdown_factor:.2f} from {current_duration:.2f}s to {target_duration:.2f}s")
        
        # Apply speed change to video
        # Use MoviePy's built-in fx method with speedx
        try:
            # Try modern MoviePy import first
            from moviepy.video.fx import speedx
            slowed_video = speedx.speedx(video_clip, slowdown_factor)
        except (ImportError, AttributeError):
            try:
                # Try alternative import path
                from moviepy.video.fx.speedx import speedx
                slowed_video = speedx(video_clip, slowdown_factor)
            except (ImportError, AttributeError):
                try:
                    # Try using fx method directly
                    slowed_video = video_clip.fx(mp.vfx.speedx, slowdown_factor)
                except AttributeError:
                    # Final fallback: use duration stretching to slow down
                    logger.warning(f"speedx not available, using duration stretching method for video")
                    # For video slowdown, we need to stretch the video duration
                    # This creates the slowed video by changing its effective duration
                    slowed_video = video_clip.set_duration(target_duration)
                    # Apply fps adjustment to maintain video quality while stretching
                    try:
                        # Try to adjust fps to maintain quality while stretching
                        original_fps = video_clip.fps
                        new_fps = original_fps * slowdown_factor
                        slowed_video = slowed_video.set_fps(new_fps)
                    except:
                        # If fps adjustment fails, just use the stretched version
                        pass
        
        return slowed_video
    
    def loop_video_to_duration(self, video_clip, target_duration):
        """Loop video clip to match target duration."""
        video_duration = video_clip.duration
        
        if target_duration <= video_duration:
            # If target is shorter or equal, just trim
            return video_clip.subclip(0, target_duration)
        
        # Calculate how many times to loop
        loop_count = int(target_duration / video_duration)
        remaining_duration = target_duration - (loop_count * video_duration)
        
        logger.info(f"Looping video {loop_count} times with {remaining_duration:.2f}s remainder")
        
        # Create list of clips for concatenation
        clips = []
        
        # Add full loops
        for i in range(loop_count):
            clips.append(video_clip)
        
        # Add partial loop if needed
        if remaining_duration > 0:
            clips.append(video_clip.subclip(0, remaining_duration))
        
        # Concatenate all clips
        if len(clips) == 1:
            return clips[0]
        else:
            return mp.concatenate_videoclips(clips)
    
    def add_voiceover(self, video_path, audio_path, output_path):
        """
        Add voiceover to video with intelligent duration matching.
        
        Duration matching strategy:
        - Video longer than audio: Trim video to match audio duration
        - Audio longer than video: Slow down video to match audio duration  
        - Equal durations: Use as-is
        
        Args:
            video_path (str): Path to input video file
            audio_path (str): Path to voiceover audio file
            output_path (str): Path to save output video
        
        Returns:
            str: Path to the output video
        """
        logger.info(f"Adding voiceover: video={video_path}, audio={audio_path}")
        
        try:
            # Load video and audio
            video = mp.VideoFileClip(video_path)
            audio = mp.AudioFileClip(audio_path)
            
            video_duration = video.duration
            audio_duration = audio.duration
            
            logger.info(f"Video duration: {video_duration:.2f}s, Audio duration: {audio_duration:.2f}s")
            
            # Determine duration matching strategy
            if video_duration > audio_duration:
                # Video is longer - trim video to match audio
                logger.info("Video longer than audio - trimming video")
                final_video = video.subclip(0, audio_duration)
                final_audio = audio
            elif video_duration < audio_duration:
                # Audio is longer - slow down video to match audio duration
                logger.info("Audio longer than video - slowing down video")
                final_video = self.slow_down_video(video, audio_duration)
                final_audio = audio
            else:
                # Durations match - use as is
                logger.info("Durations match - using as is")
                final_video = video
                final_audio = audio
            
            # Composite the audio
            # If video already has audio, mix it with the voiceover
            if final_video.audio is not None:
                logger.info("Video has existing audio - mixing with voiceover")
                # Reduce original audio volume and mix with voiceover
                original_audio = final_video.audio.volumex(0.3)  # 30% of original volume
                mixed_audio = mp.CompositeAudioClip([original_audio, final_audio.volumex(0.8)])
                final_video_with_audio = final_video.set_audio(mixed_audio)
            else:
                logger.info("Video has no audio - adding voiceover")
                final_video_with_audio = final_video.set_audio(final_audio)
            
            # Write output video
            logger.info(f"Writing output to {output_path}")
            final_video_with_audio.write_videofile(
                output_path,
                codec='libx264',
                audio_codec='aac',
                logger=None,
                verbose=False
            )
            
            # Clean up
            video.close()
            audio.close()
            final_video.close()
            final_audio.close()
            if final_video_with_audio != final_video:
                final_video_with_audio.close()
            
            logger.info(f"Voiceover added successfully: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error adding voiceover: {e}")
            raise
    
    def validate_files(self, video_path, audio_path):
        """Validate that input files exist and are supported formats."""
        if not os.path.exists(video_path):
            raise ValueError(f"Video file not found: {video_path}")
        
        if not os.path.exists(audio_path):
            raise ValueError(f"Audio file not found: {audio_path}")
        
        video_ext = os.path.splitext(video_path)[1].lower()
        audio_ext = os.path.splitext(audio_path)[1].lower()
        
        if video_ext not in self.supported_video_formats:
            logger.warning(f"Video format {video_ext} may not be supported. Supported: {self.supported_video_formats}")
        
        if audio_ext not in self.supported_audio_formats:
            logger.warning(f"Audio format {audio_ext} may not be supported. Supported: {self.supported_audio_formats}")
        
        return True
    
    def get_media_info(self, file_path):
        """Get detailed information about a media file."""
        try:
            # Try as video first
            video = mp.VideoFileClip(file_path)
            info = {
                'type': 'video',
                'duration': video.duration,
                'width': video.w,
                'height': video.h,
                'fps': video.fps,
                'has_audio': video.audio is not None
            }
            video.close()
            return info
        except:
            try:
                # Try as audio
                audio = mp.AudioFileClip(file_path)
                info = {
                    'type': 'audio',
                    'duration': audio.duration,
                    'fps': getattr(audio, 'fps', 44100)
                }
                audio.close()
                return info
            except Exception as e:
                logger.error(f"Could not analyze file {file_path}: {e}")
                return None
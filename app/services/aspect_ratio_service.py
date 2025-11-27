"""
Aspect Ratio Service for Video Dimension Changes
Provides functionality to change video aspect ratios with different scaling modes.
"""

import os
import logging
import moviepy.editor as mp
from moviepy.video.fx.resize import resize

logger = logging.getLogger(__name__)

class AspectRatioService:
    """Service for changing video aspect ratios."""
    
    def __init__(self):
        self.common_ratios = {
            '16:9': (16, 9),    # Widescreen
            '9:16': (9, 16),    # Vertical/Portrait 
            '4:3': (4, 3),      # Traditional TV
            '3:4': (3, 4),      # Portrait traditional
            '1:1': (1, 1),      # Square
            '21:9': (21, 9),    # Ultra-wide
            '2:1': (2, 1),      # Cinema
            '16:10': (16, 10),  # Computer monitor
            '3:2': (3, 2),      # Photo standard
            '2:3': (2, 3)       # Photo portrait
        }
        
        self.scale_modes = {
            'fit': {
                'name': 'Scale to Fit',
                'description': 'Scale video to fit within new dimensions, maintaining aspect ratio (may add letterboxing)'
            },
            'fill': {
                'name': 'Scale to Fill', 
                'description': 'Scale video to fill new dimensions completely (may crop content)'
            },
            'stretch': {
                'name': 'Stretch',
                'description': 'Stretch video to exact dimensions (may distort aspect ratio)'
            }
        }
    
    def parse_aspect_ratio(self, aspect_ratio_str):
        """Parse aspect ratio string into width:height tuple."""
        if aspect_ratio_str in self.common_ratios:
            return self.common_ratios[aspect_ratio_str]
        
        # Try to parse custom ratio like "16:9" or "1.77:1"
        if ':' in aspect_ratio_str:
            try:
                parts = aspect_ratio_str.split(':')
                if len(parts) == 2:
                    width_ratio = float(parts[0])
                    height_ratio = float(parts[1])
                    return (width_ratio, height_ratio)
            except ValueError:
                pass
        
        # Try to parse decimal ratio like "1.77" (assumes height = 1)
        try:
            ratio = float(aspect_ratio_str)
            return (ratio, 1)
        except ValueError:
            pass
        
        raise ValueError(f"Invalid aspect ratio format: {aspect_ratio_str}")
    
    def calculate_dimensions(self, original_width, original_height, target_ratio_w, target_ratio_h, target_height=None):
        """Calculate new dimensions based on target aspect ratio."""
        target_aspect = target_ratio_w / target_ratio_h
        
        if target_height:
            # Use specified target height
            new_height = target_height
            new_width = int(new_height * target_aspect)
        else:
            # Auto-calculate based on original video size
            original_aspect = original_width / original_height
            
            if target_aspect > original_aspect:
                # Target is wider - base on height
                new_height = original_height
                new_width = int(new_height * target_aspect)
            else:
                # Target is taller - base on width
                new_width = original_width
                new_height = int(new_width / target_aspect)
        
        # Ensure dimensions are even numbers (required for video encoding)
        new_width = new_width if new_width % 2 == 0 else new_width - 1
        new_height = new_height if new_height % 2 == 0 else new_height - 1
        
        return new_width, new_height
    
    def apply_scale_to_fit(self, video, target_width, target_height):
        """Scale video to fit within target dimensions, maintaining aspect ratio."""
        original_width, original_height = video.w, video.h
        original_aspect = original_width / original_height
        target_aspect = target_width / target_height
        
        if original_aspect > target_aspect:
            # Video is wider - fit by width
            scale_factor = target_width / original_width
            new_width = target_width
            new_height = int(original_height * scale_factor)
        else:
            # Video is taller - fit by height
            scale_factor = target_height / original_height
            new_height = target_height
            new_width = int(original_width * scale_factor)
        
        # Ensure even dimensions
        new_width = new_width if new_width % 2 == 0 else new_width - 1
        new_height = new_height if new_height % 2 == 0 else new_height - 1
        
        # Resize video
        resized_video = resize(video, (new_width, new_height))
        
        # Add letterboxing/pillarboxing if needed
        if new_width != target_width or new_height != target_height:
            # Create background
            from moviepy.video.VideoClip import ColorClip
            background = ColorClip(size=(target_width, target_height), color=(0,0,0), duration=video.duration)
            
            # Center the resized video on the background
            x_offset = (target_width - new_width) // 2
            y_offset = (target_height - new_height) // 2
            
            final_video = mp.CompositeVideoClip([
                background,
                resized_video.set_position((x_offset, y_offset))
            ])
        else:
            final_video = resized_video
        
        return final_video
    
    def apply_scale_to_fill(self, video, target_width, target_height):
        """Scale video to fill target dimensions completely, cropping if necessary."""
        original_width, original_height = video.w, video.h
        original_aspect = original_width / original_height
        target_aspect = target_width / target_height
        
        if original_aspect > target_aspect:
            # Video is wider - scale by height and crop width
            scale_factor = target_height / original_height
            new_height = target_height
            new_width = int(original_width * scale_factor)
        else:
            # Video is taller - scale by width and crop height
            scale_factor = target_width / original_width
            new_width = target_width
            new_height = int(original_height * scale_factor)
        
        # Ensure even dimensions
        new_width = new_width if new_width % 2 == 0 else new_width - 1
        new_height = new_height if new_height % 2 == 0 else new_height - 1
        
        # Resize video
        resized_video = resize(video, (new_width, new_height))
        
        # Crop to target dimensions if needed
        if new_width > target_width or new_height > target_height:
            x_offset = (new_width - target_width) // 2
            y_offset = (new_height - target_height) // 2
            
            final_video = resized_video.crop(
                x1=x_offset, y1=y_offset,
                x2=x_offset + target_width, 
                y2=y_offset + target_height
            )
        else:
            final_video = resized_video
        
        return final_video
    
    def apply_stretch(self, video, target_width, target_height):
        """Stretch video to exact target dimensions."""
        return resize(video, (target_width, target_height))
    
    def change_aspect_ratio(self, input_path, output_path, aspect_ratio, scale_mode='fit', target_height=None):
        """
        Change video aspect ratio.
        
        Args:
            input_path (str): Path to input video
            output_path (str): Path to save output video
            aspect_ratio (str): Target aspect ratio (e.g., '16:9', '9:16', '1:1')
            scale_mode (str): How to scale ('fit', 'fill', 'stretch')
            target_height (int, optional): Specific target height in pixels
        
        Returns:
            str: Path to the output video
        """
        if scale_mode not in self.scale_modes:
            raise ValueError(f"Invalid scale mode: {scale_mode}. Available: {list(self.scale_modes.keys())}")
        
        logger.info(f"Changing aspect ratio to {aspect_ratio} with {scale_mode} mode")
        
        try:
            # Parse aspect ratio
            ratio_w, ratio_h = self.parse_aspect_ratio(aspect_ratio)
            
            # Load video
            video = mp.VideoFileClip(input_path)
            original_width, original_height = video.w, video.h
            
            logger.info(f"Original dimensions: {original_width}x{original_height}")
            
            # Calculate target dimensions
            target_width, target_height = self.calculate_dimensions(
                original_width, original_height, ratio_w, ratio_h, target_height
            )
            
            logger.info(f"Target dimensions: {target_width}x{target_height}")
            
            # Apply scaling mode
            if scale_mode == 'fit':
                processed_video = self.apply_scale_to_fit(video, target_width, target_height)
            elif scale_mode == 'fill':
                processed_video = self.apply_scale_to_fill(video, target_width, target_height)
            elif scale_mode == 'stretch':
                processed_video = self.apply_stretch(video, target_width, target_height)
            
            # Write output video
            processed_video.write_videofile(
                output_path,
                codec='libx264',
                audio_codec='aac' if video.audio else None,
                logger=None,
                verbose=False
            )
            
            # Clean up
            video.close()
            processed_video.close()
            
            logger.info(f"Aspect ratio changed successfully: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error changing aspect ratio: {e}")
            raise
    
    def get_common_ratios(self):
        """Get list of common aspect ratios."""
        return {
            ratio: {
                'width': w,
                'height': h,
                'decimal': round(w/h, 2),
                'name': self._get_ratio_name(ratio)
            }
            for ratio, (w, h) in self.common_ratios.items()
        }
    
    def get_scale_modes(self):
        """Get list of available scale modes."""
        return self.scale_modes
    
    def _get_ratio_name(self, ratio):
        """Get friendly name for aspect ratio."""
        names = {
            '16:9': 'Widescreen (YouTube, TV)',
            '9:16': 'Vertical (TikTok, Instagram Stories)',
            '4:3': 'Traditional TV',
            '3:4': 'Portrait Traditional',
            '1:1': 'Square (Instagram Post)',
            '21:9': 'Ultra-wide Cinema',
            '2:1': 'Cinema',
            '16:10': 'Computer Monitor',
            '3:2': 'Photography Standard',
            '2:3': 'Photography Portrait'
        }
        return names.get(ratio, 'Custom')
    
    def get_video_info(self, file_path):
        """Get video dimensions and aspect ratio info."""
        try:
            video = mp.VideoFileClip(file_path)
            width, height = video.w, video.h
            aspect_ratio = round(width / height, 2)
            
            # Find closest common ratio
            closest_ratio = None
            closest_diff = float('inf')
            for ratio_str, (w, h) in self.common_ratios.items():
                ratio_val = w / h
                diff = abs(aspect_ratio - ratio_val)
                if diff < closest_diff:
                    closest_diff = diff
                    closest_ratio = ratio_str
            
            video.close()
            
            return {
                'width': width,
                'height': height,
                'aspect_ratio': aspect_ratio,
                'closest_common_ratio': closest_ratio,
                'duration': video.duration
            }
        except Exception as e:
            logger.error(f"Error getting video info: {e}")
            return None
"""
Asset management utilities for ScribeVault GUI.
"""

import customtkinter as ctk
from pathlib import Path
from PIL import Image
import logging

logger = logging.getLogger(__name__)

class AssetManager:
    """Manages loading and caching of UI assets."""
    
    def __init__(self):
        """Initialize the asset manager."""
        self.assets_dir = Path(__file__).parent.parent / "assets"
        self.icons_dir = self.assets_dir / "icons"
        self.images_dir = self.assets_dir / "images"
        self._image_cache = {}
        
    def get_image(self, filename: str, size: tuple = None, asset_type: str = "images") -> ctk.CTkImage:
        """
        Load an image asset with optional resizing.
        
        Args:
            filename: Name of the image file
            size: Optional (width, height) tuple for resizing
            asset_type: "images" or "icons" subdirectory
            
        Returns:
            CTkImage object or None if loading fails
        """
        cache_key = f"{asset_type}_{filename}_{size or 'original'}"
        
        # Return cached image if available
        if cache_key in self._image_cache:
            return self._image_cache[cache_key]
            
        try:
            # Determine asset directory
            asset_dir = self.images_dir if asset_type == "images" else self.icons_dir
            image_path = asset_dir / filename
            
            if not image_path.exists():
                logger.warning(f"Image not found: {image_path}")
                return None
                
            # Load image with PIL
            pil_image = Image.open(image_path)
            
            # Get original size for CTkImage
            original_size = pil_image.size
            
            # Resize if requested, otherwise use original
            if size:
                pil_image = pil_image.resize(size, Image.Resampling.LANCZOS)
                display_size = size
            else:
                display_size = original_size
                
            # Create CTkImage
            ctk_image = ctk.CTkImage(
                light_image=pil_image,
                dark_image=pil_image,
                size=display_size
            )
            
            # Cache the image
            self._image_cache[cache_key] = ctk_image
            
            logger.info(f"Loaded image: {filename} ({display_size})")
            return ctk_image
            
        except Exception as e:
            logger.error(f"Failed to load image {filename}: {e}")
            return None
            
    def get_logo(self, size: tuple = None) -> ctk.CTkImage:
        """Get the main logo image at original size or specified size."""
        return self.get_image("logo.png", size, "images")
        
    def get_app_icon(self, size: tuple = (32, 32)) -> ctk.CTkImage:
        """Get the application icon."""
        return self.get_image("app_icon.png", size, "icons")
        
    def get_icon_path(self, filename: str) -> Path:
        """Get the full path to an icon file."""
        return self.icons_dir / filename
        
    def get_image_path(self, filename: str) -> Path:
        """Get the full path to an image file."""
        return self.images_dir / filename
        
    def clear_cache(self):
        """Clear the image cache."""
        self._image_cache.clear()
        logger.info("Image cache cleared")

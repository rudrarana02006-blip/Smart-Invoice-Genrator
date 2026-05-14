import ctypes.util
import os
import sys

def patch_weasyprint():
    """
    Monkeypatch ctypes.util.find_library to find Homebrew libraries on macOS.
    This is necessary because WeasyPrint often fails to find its dependencies (pango, cairo, etc.)
    on Apple Silicon Macs where Homebrew is in /opt/homebrew.
    """
    if sys.platform != 'darwin':
        return

    orig_find_library = ctypes.util.find_library
    
    # Common Homebrew paths
    homebrew_lib_path = "/opt/homebrew/lib"
    intel_brew_path = "/usr/local/lib"
    
    def my_find_library(name):
        # List of libraries we want to redirect
        lib_map = {
            'pango': 'libpango-1.0.0.dylib',
            'pangocairo': 'libpangocairo-1.0.0.dylib',
            'cairo': 'libcairo.2.dylib',
            'gobject': 'libgobject-2.0.0.dylib',
            'glib': 'libglib-2.0.0.dylib',
            'harfbuzz': 'libharfbuzz.0.dylib',
            'fontconfig': 'libfontconfig.1.dylib',
            'pangoft2': 'libpangoft2-1.0.0.dylib'
        }
        
        for key, filename in lib_map.items():
            if key in name.lower():
                for base_path in [homebrew_lib_path, intel_brew_path]:
                    full_path = os.path.join(base_path, filename)
                    if os.path.exists(full_path):
                        return full_path
        
        # Fallback to original
        return orig_find_library(name)

    ctypes.util.find_library = my_find_library

# Apply the patch immediately
patch_weasyprint()

import weasyprint
print("WeasyPrint successfully patched and imported!")

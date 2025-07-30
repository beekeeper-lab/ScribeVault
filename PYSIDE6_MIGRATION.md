# PySide6 Migration Guide for ScribeVault

## Overview
This document outlines the migration from CustomTkinter to PySide6 for ScribeVault, providing better native appearance, more robust widgets, and enhanced cross-platform compatibility.

## Benefits of PySide6 Migration

### ✅ Advantages
- **Native Look & Feel**: True native widgets on each platform
- **Better Performance**: Hardware-accelerated rendering
- **Rich Widget Set**: Advanced widgets like QTabWidget, QSplitter, QTreeWidget
- **Professional Styling**: CSS-like styling with stylesheets
- **Better Threading**: Robust signal/slot system for thread safety
- **Enhanced Accessibility**: Built-in accessibility support
- **Mature Ecosystem**: Extensive documentation and community support

### 📋 Migration Mapping

#### Core Framework
```python
# CustomTkinter → PySide6
customtkinter as ctk → PySide6.QtWidgets as QtWidgets
ctk.CTk() → QApplication + QMainWindow
ctk.CTkToplevel() → QDialog / QMainWindow
```

#### Widget Mappings
```python
# Layout & Containers
ctk.CTkFrame → QFrame / QWidget
ctk.CTkScrollableFrame → QScrollArea + QWidget

# Input Widgets
ctk.CTkEntry → QLineEdit
ctk.CTkTextbox → QTextEdit / QPlainTextEdit
ctk.CTkButton → QPushButton
ctk.CTkCheckBox → QCheckBox
ctk.CTkOptionMenu → QComboBox
ctk.CTkSlider → QSlider
ctk.CTkProgressBar → QProgressBar

# Display Widgets
ctk.CTkLabel → QLabel
ctk.CTkImage → QPixmap + QLabel

# Layout Managers
.grid() → QGridLayout
.pack() → QVBoxLayout / QHBoxLayout
.place() → absolute positioning (discouraged)
```

#### Event System
```python
# CustomTkinter → PySide6
command=callback → clicked.connect(callback)
bind(event, callback) → signal.connect(callback)
```

## Migration Strategy

### Phase 1: Core Infrastructure ✅
- [x] Update requirements.txt
- [ ] Create base application class
- [ ] Set up theming system
- [ ] Implement resource management

### Phase 2: Main Window Migration
- [ ] Convert main application window
- [ ] Migrate layout system
- [ ] Update event handling
- [ ] Implement status bar

### Phase 3: Dialog Windows
- [ ] Settings window
- [ ] Vault/library window
- [ ] Recording details dialog
- [ ] Markdown viewer
- [ ] Confirmation dialogs

### Phase 4: Advanced Features
- [ ] Implement dark/light theme switching
- [ ] Add system tray integration
- [ ] Enhance keyboard shortcuts
- [ ] Improve accessibility

### Phase 5: Testing & Polish
- [ ] Comprehensive testing
- [ ] Performance optimization
- [ ] Documentation updates
- [ ] User experience improvements

## Technical Implementation

### 1. Application Structure
```python
# New PySide6 app structure
from PySide6.QtWidgets import QApplication, QMainWindow
from PySide6.QtCore import QThread, Signal
from PySide6.QtGui import QIcon, QFont

class ScribeVaultApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setup_ui()
        self.setup_threading()
```

### 2. Theming System
```python
# Dark theme implementation
import qdarktheme

app = QApplication(sys.argv)
app.setStyleSheet(qdarktheme.load_stylesheet())
```

### 3. Signal/Slot System
```python
# Thread-safe communication
class WorkerThread(QThread):
    finished = Signal(str)  # Signal with data
    error = Signal(str)
    
    def run(self):
        try:
            result = self.do_work()
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))
```

### 4. Resource Management
```python
# Qt Resource System
from PySide6.QtCore import QResource
from PySide6.QtGui import QPixmap

# Load icons and images
icon = QIcon(":/icons/app_icon.png")
pixmap = QPixmap(":/images/logo.png")
```

## File Structure Changes

### New Files to Create
- `src/gui/qt_main_window.py` - Main PySide6 window
- `src/gui/qt_widgets/` - Custom widget components
- `src/gui/qt_dialogs/` - Dialog windows
- `src/gui/resources/` - Qt resource files
- `src/gui/stylesheets/` - CSS-like styling
- `requirements-qt.txt` - PySide6 dependencies

### Files to Update
- `main.py` - Application entry point
- `src/gui/settings_window.py` - Convert to QDialog
- `src/gui/assets.py` - Update for Qt resources
- All test files for new widgets

## Development Guidelines

### 1. Consistent Naming
- Use Qt naming conventions: camelCase for methods
- Prefix custom widgets with `Scribe` (e.g., `ScribeRecordButton`)

### 2. Thread Safety
- Use signals/slots for cross-thread communication
- Run heavy operations in QThread workers
- Never update UI directly from worker threads

### 3. Styling
- Use QSS (Qt Style Sheets) for consistent theming
- Create reusable style classes
- Support both dark and light themes

### 4. Testing Strategy
- Unit tests for each widget component
- Integration tests for dialog workflows
- Visual regression tests for UI consistency

## Migration Checklist

### Core Components
- [ ] Application initialization
- [ ] Main window layout
- [ ] Menu bar and toolbar
- [ ] Status bar with indicators

### Recording Interface
- [ ] Record button with state management
- [ ] Progress indicators
- [ ] Audio level visualization
- [ ] Timer display

### Text Areas
- [ ] Transcription display with formatting
- [ ] Summary display with markdown support
- [ ] Copy/paste functionality
- [ ] Text search capabilities

### Vault Interface
- [ ] Recording list with metadata
- [ ] Search and filter functionality
- [ ] Batch operations
- [ ] Export capabilities

### Settings Interface
- [ ] Tabbed settings dialog
- [ ] Audio device selection
- [ ] Theme selection
- [ ] API key management

### Advanced Features
- [ ] Drag & drop for files
- [ ] Keyboard shortcuts
- [ ] System tray integration
- [ ] Auto-save functionality

## Testing Strategy

### Unit Tests
```python
import pytest
from PySide6.QtWidgets import QApplication
from src.gui.qt_main_window import ScribeVaultMainWindow

def test_main_window_creation():
    app = QApplication([])
    window = ScribeVaultMainWindow()
    assert window.isVisible() == False
    window.show()
    assert window.isVisible() == True
```

### Integration Tests
- Test complete recording workflow
- Test vault operations
- Test settings persistence
- Test error handling

## Performance Considerations

### Memory Management
- Proper cleanup of Qt objects
- Efficient image loading
- Lazy loading for large lists

### Responsiveness
- Use QThread for long operations
- Implement progress feedback
- Asynchronous file operations

## Deployment Updates

### Requirements
- Update setup scripts for PySide6
- Test on all target platforms
- Update documentation

### Distribution
- Include Qt runtime libraries
- Update app bundle creation
- Test installer packages

---

*This migration will significantly enhance ScribeVault's professional appearance and cross-platform compatibility while maintaining all existing functionality.*

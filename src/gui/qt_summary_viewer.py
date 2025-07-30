"""
AI Summary viewer dialog for ScribeVault PySide6 application.
"""

import os
from pathlib import Path
from typing import Optional, Dict
from datetime import datetime

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QWidget,
    QLabel, QPushButton, QTextEdit, QScrollArea,
    QGroupBox, QMessageBox, QFileDialog, QTabWidget,
    QFrame, QSplitter, QApplication, QTextBrowser
)
from PySide6.QtCore import Qt, QSize, QSettings
from PySide6.QtGui import QFont, QIcon, QTextDocument, QTextCursor

import logging

logger = logging.getLogger(__name__)


class SummaryViewerDialog(QDialog):
    """Dialog for viewing AI summaries and markdown content."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_recording_data = None
        self.current_markdown_path = None
        
        self.setup_ui()
        self.load_settings()
        
    def setup_ui(self):
        """Setup the summary viewer UI."""
        self.setWindowTitle("ScribeVault - AI Summary Viewer")
        self.setMinimumSize(800, 600)
        self.resize(1000, 700)
        
        # Main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Header
        self.create_header(layout)
        
        # Content area with tabs
        self.create_content_area(layout)
        
        # Footer with controls
        self.create_footer(layout)
        
    def create_header(self, parent_layout):
        """Create the header with title and controls."""
        header_frame = QFrame()
        header_frame.setStyleSheet("background-color: #2b2b2b; border-bottom: 1px solid #555;")
        header_frame.setFixedHeight(60)
        
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(20, 10, 20, 10)
        
        # Title
        title_label = QLabel("🤖 AI Summary Viewer")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; color: white;")
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        # Recording info label
        self.recording_info_label = QLabel("No recording loaded")
        self.recording_info_label.setStyleSheet("color: #888; font-size: 12px;")
        header_layout.addWidget(self.recording_info_label)
        
        parent_layout.addWidget(header_frame)
        
    def create_content_area(self, parent_layout):
        """Create the main content area with tabs."""
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #555;
                background-color: #1e1e1e;
            }
            QTabBar::tab {
                background-color: #2b2b2b;
                color: white;
                padding: 8px 16px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background-color: #0078d4;
            }
            QTabBar::tab:hover {
                background-color: #3c3c3c;
            }
        """)
        
        # Summary tab
        self.create_summary_tab()
        
        # Markdown display tab (rendered view)
        self.create_markdown_display_tab()
        
        # Markdown tab (raw content)
        self.create_markdown_tab()
        
        # Recording details tab
        self.create_details_tab()
        
        parent_layout.addWidget(self.tab_widget)
        
    def create_summary_tab(self):
        """Create the summary display tab."""
        summary_widget = QWidget()
        layout = QVBoxLayout(summary_widget)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Summary content
        self.summary_text = QTextEdit()
        self.summary_text.setReadOnly(True)
        self.summary_text.setFont(QFont("Segoe UI", 12))
        self.summary_text.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #ffffff;
                border: 1px solid #555;
                padding: 15px;
                line-height: 1.6;
            }
        """)
        self.summary_text.setPlaceholderText("AI summary will appear here when a recording with summary is loaded...")
        
        layout.addWidget(self.summary_text)
        
        self.tab_widget.addTab(summary_widget, "📄 Summary")
        
    def create_markdown_display_tab(self):
        """Create the markdown display tab with rendered view."""
        display_widget = QWidget()
        layout = QVBoxLayout(display_widget)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Display toolbar
        toolbar_layout = QHBoxLayout()
        
        self.display_info_label = QLabel("No markdown content to display")
        self.display_info_label.setStyleSheet("color: #888; font-size: 12px;")
        toolbar_layout.addWidget(self.display_info_label)
        
        toolbar_layout.addStretch()
        
        # Font size controls
        font_size_label = QLabel("Font Size:")
        font_size_label.setStyleSheet("color: #888; font-size: 12px; margin-right: 5px;")
        toolbar_layout.addWidget(font_size_label)
        
        self.decrease_font_button = QPushButton("A-")
        self.decrease_font_button.setMaximumWidth(30)
        self.decrease_font_button.setToolTip("Decrease font size")
        self.decrease_font_button.clicked.connect(self.decrease_display_font)
        toolbar_layout.addWidget(self.decrease_font_button)
        
        self.increase_font_button = QPushButton("A+")
        self.increase_font_button.setMaximumWidth(30)
        self.increase_font_button.setToolTip("Increase font size")
        self.increase_font_button.clicked.connect(self.increase_display_font)
        toolbar_layout.addWidget(self.increase_font_button)
        
        layout.addLayout(toolbar_layout)
        
        # Markdown display browser
        self.markdown_browser = QTextBrowser()
        self.markdown_browser.setReadOnly(True)
        self.markdown_browser.setFont(QFont("Segoe UI", 12))
        self.markdown_browser.setStyleSheet("""
            QTextBrowser {
                background-color: #1e1e1e;
                color: #ffffff;
                border: 1px solid #555;
                padding: 20px;
                selection-background-color: #0078d4;
            }
        """)
        self.markdown_browser.setPlaceholderText("Rendered markdown content will appear here when available...")
        
        # Set custom HTML styling for better markdown rendering
        self.setup_markdown_styling()
        
        layout.addWidget(self.markdown_browser)
        
        self.tab_widget.addTab(display_widget, "🎨 Display")
        
    def create_markdown_tab(self):
        """Create the markdown content tab."""
        markdown_widget = QWidget()
        layout = QVBoxLayout(markdown_widget)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Markdown toolbar
        toolbar_layout = QHBoxLayout()
        
        self.markdown_info_label = QLabel("No markdown file loaded")
        self.markdown_info_label.setStyleSheet("color: #888; font-size: 12px;")
        toolbar_layout.addWidget(self.markdown_info_label)
        
        toolbar_layout.addStretch()
        
        self.export_markdown_button = QPushButton("💾 Export Markdown")
        self.export_markdown_button.setEnabled(False)
        self.export_markdown_button.clicked.connect(self.export_markdown)
        toolbar_layout.addWidget(self.export_markdown_button)
        
        self.open_markdown_button = QPushButton("📂 Open File")
        self.open_markdown_button.setEnabled(False)
        self.open_markdown_button.clicked.connect(self.open_markdown_file)
        toolbar_layout.addWidget(self.open_markdown_button)
        
        layout.addLayout(toolbar_layout)
        
        # Markdown content
        self.markdown_text = QTextEdit()
        self.markdown_text.setReadOnly(True)
        self.markdown_text.setFont(QFont("Consolas", 11))
        self.markdown_text.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #ffffff;
                border: 1px solid #555;
                padding: 15px;
                font-family: 'Consolas', 'Monaco', monospace;
            }
        """)
        self.markdown_text.setPlaceholderText("Markdown content will appear here when available...")
        
        layout.addWidget(self.markdown_text)
        
        self.tab_widget.addTab(markdown_widget, "📝 Markdown")
        
    def create_details_tab(self):
        """Create the recording details tab."""
        details_widget = QWidget()
        layout = QVBoxLayout(details_widget)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Scroll area for details
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("QScrollArea { border: none; }")
        
        self.details_content_widget = QWidget()
        self.details_content_layout = QVBoxLayout(self.details_content_widget)
        
        # Initially empty
        no_data_label = QLabel("Load a recording to view details")
        no_data_label.setAlignment(Qt.AlignCenter)
        no_data_label.setStyleSheet("color: #888; font-style: italic; padding: 50px;")
        self.details_content_layout.addWidget(no_data_label)
        
        scroll_area.setWidget(self.details_content_widget)
        layout.addWidget(scroll_area)
        
        self.tab_widget.addTab(details_widget, "ℹ️ Details")
        
    def setup_markdown_styling(self):
        """Setup custom CSS styling for markdown rendering."""
        css_style = """
        <style>
        body {
            font-family: 'Segoe UI', Arial, sans-serif;
            font-size: 14px;
            line-height: 1.6;
            color: #ffffff;
            background-color: #1e1e1e;
            margin: 0;
            padding: 0;
        }
        h1, h2, h3, h4, h5, h6 {
            color: #58a6ff;
            margin-top: 1.5em;
            margin-bottom: 0.5em;
            font-weight: 600;
        }
        h1 { font-size: 2em; border-bottom: 2px solid #555; padding-bottom: 0.3em; }
        h2 { font-size: 1.5em; border-bottom: 1px solid #555; padding-bottom: 0.3em; }
        h3 { font-size: 1.25em; }
        h4 { font-size: 1.1em; }
        h5, h6 { font-size: 1em; }
        
        p {
            margin-bottom: 1em;
            text-align: justify;
        }
        
        ul, ol {
            margin: 0.5em 0 1em 1.5em;
            padding-left: 1em;
        }
        
        li {
            margin-bottom: 0.3em;
        }
        
        blockquote {
            border-left: 4px solid #0078d4;
            margin: 1em 0;
            padding: 0.5em 0 0.5em 1em;
            background-color: #2d2d2d;
            font-style: italic;
        }
        
        code {
            background-color: #2d2d2d;
            color: #ff7b72;
            padding: 0.2em 0.4em;
            border-radius: 3px;
            font-family: 'Consolas', 'Monaco', monospace;
            font-size: 0.9em;
        }
        
        pre {
            background-color: #2d2d2d;
            border: 1px solid #555;
            border-radius: 6px;
            padding: 1em;
            overflow-x: auto;
            margin: 1em 0;
        }
        
        pre code {
            background-color: transparent;
            padding: 0;
            color: #ffffff;
        }
        
        table {
            border-collapse: collapse;
            width: 100%;
            margin: 1em 0;
        }
        
        th, td {
            border: 1px solid #555;
            padding: 0.5em;
            text-align: left;
        }
        
        th {
            background-color: #2d2d2d;
            font-weight: 600;
        }
        
        tr:nth-child(even) {
            background-color: #252525;
        }
        
        a {
            color: #58a6ff;
            text-decoration: none;
        }
        
        a:hover {
            text-decoration: underline;
        }
        
        strong, b {
            color: #ffffff;
            font-weight: 600;
        }
        
        em, i {
            font-style: italic;
            color: #f0f6fc;
        }
        
        hr {
            border: none;
            border-top: 1px solid #555;
            margin: 2em 0;
        }
        
        .summary-section {
            background-color: #2d2d2d;
            border-left: 4px solid #0078d4;
            padding: 1em;
            margin: 1em 0;
            border-radius: 0 6px 6px 0;
        }
        
        .key-points {
            background-color: #2d2d2d;
            border-left: 4px solid #f79000;
            padding: 1em;
            margin: 1em 0;
            border-radius: 0 6px 6px 0;
        }
        </style>
        """
        self.markdown_css = css_style
        
    def increase_display_font(self):
        """Increase the font size in the markdown display."""
        font = self.markdown_browser.font()
        current_size = font.pointSize()
        if current_size < 20:  # Max size limit
            font.setPointSize(current_size + 1)
            self.markdown_browser.setFont(font)
            
    def decrease_display_font(self):
        """Decrease the font size in the markdown display."""
        font = self.markdown_browser.font()
        current_size = font.pointSize()
        if current_size > 8:  # Min size limit
            font.setPointSize(current_size - 1)
            self.markdown_browser.setFont(font)
            
    def markdown_to_html(self, markdown_text: str) -> str:
        """Convert markdown text to HTML with styling."""
        try:
            # Try to use markdown library if available
            try:
                import markdown
                html_content = markdown.markdown(
                    markdown_text,
                    extensions=['extra', 'codehilite', 'toc']
                )
            except ImportError:
                # Fallback: basic markdown-like formatting
                html_content = self.basic_markdown_to_html(markdown_text)
            
            # Wrap with our CSS styling
            full_html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                {self.markdown_css}
            </head>
            <body>
                {html_content}
            </body>
            </html>
            """
            return full_html
            
        except Exception as e:
            logger.error(f"Error converting markdown to HTML: {e}")
            return f"<html><body><p>Error rendering markdown: {e}</p></body></html>"
            
    def basic_markdown_to_html(self, text: str) -> str:
        """Basic markdown to HTML conversion fallback."""
        import re
        
        # Escape HTML characters first
        text = text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        
        # Convert headers
        text = re.sub(r'^# (.*?)$', r'<h1>\1</h1>', text, flags=re.MULTILINE)
        text = re.sub(r'^## (.*?)$', r'<h2>\1</h2>', text, flags=re.MULTILINE)
        text = re.sub(r'^### (.*?)$', r'<h3>\1</h3>', text, flags=re.MULTILINE)
        text = re.sub(r'^#### (.*?)$', r'<h4>\1</h4>', text, flags=re.MULTILINE)
        
        # Convert bold and italic
        text = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', text)
        text = re.sub(r'\*(.*?)\*', r'<em>\1</em>', text)
        
        # Convert code blocks
        text = re.sub(r'```(.*?)```', r'<pre><code>\1</code></pre>', text, flags=re.DOTALL)
        text = re.sub(r'`(.*?)`', r'<code>\1</code>', text)
        
        # Convert lists
        text = re.sub(r'^- (.*?)$', r'<li>\1</li>', text, flags=re.MULTILINE)
        text = re.sub(r'^(\d+)\. (.*?)$', r'<li>\2</li>', text, flags=re.MULTILINE)
        
        # Wrap consecutive list items
        text = re.sub(r'(<li>.*?</li>)(?=\s*<li>)', r'\1', text, flags=re.DOTALL)
        text = re.sub(r'(<li>.*?</li>(?:\s*<li>.*?</li>)*)', r'<ul>\1</ul>', text, flags=re.DOTALL)
        
        # Convert line breaks to paragraphs
        paragraphs = text.split('\n\n')
        html_paragraphs = []
        for para in paragraphs:
            para = para.strip()
            if para and not para.startswith('<'):
                para = f'<p>{para}</p>'
            if para:
                html_paragraphs.append(para)
        
        return '\n'.join(html_paragraphs)
        
    def create_footer(self, parent_layout):
        """Create the footer with action buttons."""
        footer_frame = QFrame()
        footer_frame.setStyleSheet("background-color: #2b2b2b; border-top: 1px solid #555;")
        footer_frame.setFixedHeight(60)
        
        footer_layout = QHBoxLayout(footer_frame)
        footer_layout.setContentsMargins(20, 10, 20, 10)
        
        # Copy buttons
        self.copy_summary_button = QPushButton("📋 Copy Summary")
        self.copy_summary_button.setEnabled(False)
        self.copy_summary_button.clicked.connect(self.copy_summary)
        footer_layout.addWidget(self.copy_summary_button)
        
        self.copy_display_button = QPushButton("📋 Copy Display")
        self.copy_display_button.setEnabled(False)
        self.copy_display_button.clicked.connect(self.copy_display)
        footer_layout.addWidget(self.copy_display_button)
        
        self.copy_markdown_button = QPushButton("📋 Copy Markdown")
        self.copy_markdown_button.setEnabled(False)
        self.copy_markdown_button.clicked.connect(self.copy_markdown)
        footer_layout.addWidget(self.copy_markdown_button)
        
        footer_layout.addStretch()
        
        # Close button
        close_button = QPushButton("✕ Close")
        close_button.clicked.connect(self.accept)
        close_button.setStyleSheet("QPushButton { background-color: #666; color: white; }")
        footer_layout.addWidget(close_button)
        
        parent_layout.addWidget(footer_frame)
        
    def load_recording_data(self, recording_data: Dict, markdown_path: Optional[str] = None):
        """Load recording data into the viewer."""
        self.current_recording_data = recording_data
        self.current_markdown_path = markdown_path
        
        # Update header info
        filename = recording_data.get('filename', 'Unknown')
        created_at = recording_data.get('created_at', 'Unknown')
        self.recording_info_label.setText(f"Recording: {filename} | Created: {created_at}")
        
        # Load summary
        summary = recording_data.get('summary', '')
        if summary:
            self.summary_text.setPlainText(summary)
            self.copy_summary_button.setEnabled(True)
        else:
            self.summary_text.setPlainText("No AI summary available for this recording.")
            self.copy_summary_button.setEnabled(False)
            
        # Load markdown if available
        if markdown_path and Path(markdown_path).exists():
            try:
                with open(markdown_path, 'r', encoding='utf-8') as f:
                    markdown_content = f.read()
                
                # Update raw markdown tab
                self.markdown_text.setPlainText(markdown_content)
                self.markdown_info_label.setText(f"Loaded: {Path(markdown_path).name}")
                self.copy_markdown_button.setEnabled(True)
                self.copy_display_button.setEnabled(True)
                self.export_markdown_button.setEnabled(True)
                self.open_markdown_button.setEnabled(True)
                
                # Update markdown display tab
                html_content = self.markdown_to_html(markdown_content)
                self.markdown_browser.setHtml(html_content)
                self.display_info_label.setText(f"Displaying: {Path(markdown_path).name}")
                
            except Exception as e:
                logger.error(f"Error loading markdown file: {e}")
                self.markdown_text.setPlainText(f"Error loading markdown file: {e}")
                self.markdown_info_label.setText("Error loading markdown")
                self.markdown_browser.setPlainText(f"Error loading markdown file: {e}")
                self.display_info_label.setText("Error loading markdown")
        else:
            self.markdown_text.setPlainText("No markdown file available for this recording.")
            self.markdown_info_label.setText("No markdown file")
            self.copy_markdown_button.setEnabled(False)
            self.copy_display_button.setEnabled(False)
            self.export_markdown_button.setEnabled(False)
            self.open_markdown_button.setEnabled(False)
            
            # Update display tab for no markdown case
            self.markdown_browser.setPlainText("No markdown file available for this recording.")
            self.display_info_label.setText("No markdown content to display")
            
        # Load details
        self.load_recording_details()
        
        logger.info(f"Loaded recording data for: {filename}")
        
    def load_recording_details(self):
        """Load recording details into the details tab."""
        if not self.current_recording_data:
            return
            
        # Clear existing details
        while self.details_content_layout.count():
            child = self.details_content_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
                
        recording = self.current_recording_data
        
        # Basic information
        basic_info = QGroupBox("📝 Basic Information")
        basic_layout = QVBoxLayout(basic_info)
        
        info_items = [
            ("Title", recording.get('title', 'Untitled')),
            ("Filename", recording.get('filename', 'Unknown')),
            ("Category", recording.get('category', 'other').title()),
            ("Duration", self.format_duration(recording.get('duration', 0))),
            ("File Size", self.format_file_size(recording.get('file_size', 0))),
            ("Created", recording.get('created_at', 'Unknown'))
        ]
        
        for key, value in info_items:
            item_layout = QHBoxLayout()
            key_label = QLabel(f"{key}:")
            key_label.setStyleSheet("font-weight: bold; min-width: 100px;")
            value_label = QLabel(str(value) if value else "N/A")
            value_label.setWordWrap(True)
            
            item_layout.addWidget(key_label)
            item_layout.addWidget(value_label, 1)
            basic_layout.addLayout(item_layout)
            
        self.details_content_layout.addWidget(basic_info)
        
        # Transcription
        if recording.get('transcription'):
            transcription_group = QGroupBox("🎤 Transcription")
            transcription_layout = QVBoxLayout(transcription_group)
            
            transcription_text = QTextEdit()
            transcription_text.setPlainText(recording['transcription'])
            transcription_text.setReadOnly(True)
            transcription_text.setMaximumHeight(200)
            transcription_text.setStyleSheet("background-color: #2b2b2b; border: 1px solid #555;")
            
            transcription_layout.addWidget(transcription_text)
            self.details_content_layout.addWidget(transcription_group)
            
        # Key points if available
        if recording.get('key_points'):
            key_points_group = QGroupBox("🔑 Key Points")
            key_points_layout = QVBoxLayout(key_points_group)
            
            if isinstance(recording['key_points'], list):
                key_points_text = "\n".join([f"• {point}" for point in recording['key_points']])
            else:
                key_points_text = recording['key_points']
                
            key_points_display = QTextEdit()
            key_points_display.setPlainText(key_points_text)
            key_points_display.setReadOnly(True)
            key_points_display.setMaximumHeight(150)
            key_points_display.setStyleSheet("background-color: #2b2b2b; border: 1px solid #555;")
            
            key_points_layout.addWidget(key_points_display)
            self.details_content_layout.addWidget(key_points_group)
            
        # Tags if available
        if recording.get('tags'):
            tags_group = QGroupBox("🏷️ Tags")
            tags_layout = QVBoxLayout(tags_group)
            
            if isinstance(recording['tags'], list):
                tags_text = ", ".join(recording['tags'])
            else:
                tags_text = recording['tags']
                
            tags_label = QLabel(tags_text)
            tags_label.setWordWrap(True)
            tags_layout.addWidget(tags_label)
            self.details_content_layout.addWidget(tags_group)
            
        self.details_content_layout.addStretch()
        
    def copy_summary(self):
        """Copy summary text to clipboard."""
        summary_text = self.summary_text.toPlainText()
        if summary_text and summary_text != "No AI summary available for this recording.":
            QApplication.clipboard().setText(summary_text)
            self.show_status_message("Summary copied to clipboard")
        
    def copy_display(self):
        """Copy display content (plain text from browser) to clipboard."""
        display_text = self.markdown_browser.toPlainText()
        if display_text and display_text != "No markdown file available for this recording.":
            QApplication.clipboard().setText(display_text)
            self.show_status_message("Display content copied to clipboard")
        
    def copy_markdown(self):
        """Copy markdown text to clipboard."""
        markdown_text = self.markdown_text.toPlainText()
        if markdown_text and markdown_text != "No markdown file available for this recording.":
            QApplication.clipboard().setText(markdown_text)
            self.show_status_message("Markdown copied to clipboard")
            
    def export_markdown(self):
        """Export markdown to a new file."""
        if not self.current_markdown_path or not Path(self.current_markdown_path).exists():
            QMessageBox.warning(self, "Export Error", "No markdown file available to export.")
            return
            
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Export Markdown File",
            f"summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
            "Markdown Files (*.md);;All Files (*)"
        )
        
        if filename:
            try:
                import shutil
                shutil.copy2(self.current_markdown_path, filename)
                self.show_status_message(f"Markdown exported to: {Path(filename).name}")
            except Exception as e:
                QMessageBox.critical(self, "Export Error", f"Failed to export markdown:\n{e}")
                
    def open_markdown_file(self):
        """Open markdown file in system default application."""
        if not self.current_markdown_path or not Path(self.current_markdown_path).exists():
            QMessageBox.warning(self, "File Error", "No markdown file available to open.")
            return
            
        try:
            import platform
            import subprocess
            
            system = platform.system()
            if system == "Windows":
                os.startfile(self.current_markdown_path)
            elif system == "Darwin":  # macOS
                subprocess.run(['open', self.current_markdown_path], check=True)
            else:  # Linux and others
                subprocess.run(['xdg-open', self.current_markdown_path], check=True)
                
        except Exception as e:
            QMessageBox.warning(
                self, 
                "Open Error", 
                f"Could not open markdown file:\n{e}\n\nFile location: {self.current_markdown_path}"
            )
            
    def format_duration(self, seconds: float) -> str:
        """Format duration in seconds to MM:SS format."""
        if not seconds or seconds <= 0:
            return "0:00"
        
        minutes = int(seconds // 60)
        seconds = int(seconds % 60)
        return f"{minutes}:{seconds:02d}"
        
    def format_file_size(self, bytes_size: int) -> str:
        """Format file size in bytes to human readable format."""
        if not bytes_size or bytes_size <= 0:
            return "0 B"
        
        for unit in ['B', 'KB', 'MB', 'GB']:
            if bytes_size < 1024:
                return f"{bytes_size:.1f} {unit}"
            bytes_size /= 1024
        return f"{bytes_size:.1f} TB"
        
    def show_status_message(self, message: str):
        """Show a temporary status message."""
        # Create a simple status message that auto-hides
        from PySide6.QtCore import QTimer
        
        # You could add a status bar here if needed, for now just log
        logger.info(f"Status: {message}")
        
    def load_settings(self):
        """Load dialog settings."""
        settings = QSettings()
        
        # Window geometry
        geometry = settings.value("summary_viewer/geometry")
        if geometry:
            self.restoreGeometry(geometry)
            
        # Tab selection
        current_tab = settings.value("summary_viewer/current_tab", 0, type=int)
        if 0 <= current_tab < self.tab_widget.count():
            self.tab_widget.setCurrentIndex(current_tab)
            
    def save_settings(self):
        """Save dialog settings."""
        settings = QSettings()
        settings.setValue("summary_viewer/geometry", self.saveGeometry())
        settings.setValue("summary_viewer/current_tab", self.tab_widget.currentIndex())
        
    def closeEvent(self, event):
        """Handle close event."""
        self.save_settings()
        event.accept()

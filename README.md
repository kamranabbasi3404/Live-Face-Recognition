# 🔐 Live Face Recognition System

A professional **real-time face verification system** built with Python, featuring a modern dark-themed GUI and support for both webcam and image upload.

![Python](https://img.shields.io/badge/Python-3.12+-blue.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)
![Platform](https://img.shields.io/badge/Platform-Windows-lightgrey.svg)

## ✨ Features

- **🎯 Real-time Face Verification** - Verify identity using live webcam feed
- **📷 Image Upload Support** - Upload photos from phone or files for enrollment/verification
- **🌙 Modern Dark GUI** - Professional CustomTkinter interface with animated popups
- **👤 User Management** - Enroll, search, and delete users easily
- **🔒 Secure Database** - SQLite storage for face embeddings
- **⚡ Optimized Performance** - Facenet model for fast verification (~100ms)
- **✅ Professional Popups** - ACCESS GRANTED/DENIED notifications with confidence scores
- **🔴 Auto-Stop Camera** - Camera automatically stops when face is verified

## 🖼️ Screenshots

| Home Screen | Verification Popup | Enrollment |
|-------------|-------------------|------------|
| Modern dark interface | ACCESS GRANTED popup | Capture or upload photos |

## 🚀 Quick Start

### Prerequisites

- Python 3.12+
- Webcam (optional - can use image upload)
- Windows 10/11

### Installation

```bash
# Clone the repository
git clone https://github.com/kamranabbasi3404/Live-Face-Recognition.git
cd Live-Face-Recognition

# Install dependencies
pip install -r requirements.txt

# Run the GUI application
python gui_app.py
```

### First Run
On first run, the system will download the Facenet model (~90MB). This is a one-time download.

## 📁 Project Structure

```
Live-Face-Recognition/
├── gui_app.py          # Modern GUI application (recommended)
├── main.py             # Command-line interface
├── config.py           # Configuration settings
├── requirements.txt    # Python dependencies
├── modules/
│   ├── camera.py       # Webcam handling
│   ├── face_detector.py # Face detection (OpenCV)
│   ├── embeddings.py   # Face embedding generation (DeepFace + Facenet)
│   ├── verifier.py     # Face verification logic
│   ├── liveness.py     # Liveness detection (blink)
│   └── display.py      # OpenCV display utilities
├── database/
│   └── db_manager.py   # SQLite database management
└── enrolled_images/    # Stored user face images
```

## 🎮 Usage

### GUI Mode (Recommended)
```bash
python gui_app.py
```

### CLI Mode
```bash
python main.py
```

### Enrollment
1. Click **"📷 Enroll User"**
2. Enter user name (User ID is auto-generated)
3. Choose **Webcam** or **Upload Images**
4. Capture 3-5 photos from different angles
5. Click **"💾 Save User"**

### Verification
1. Click **"✓ Verify Face"**
2. Choose **Live Verification** or **Verify from Image**
3. Professional popup shows **ACCESS GRANTED** or **ACCESS DENIED**
4. Camera automatically stops when verified

## ⚙️ Configuration

Edit `config.py` to customize:

```python
EMBEDDING_MODEL = "Facenet"      # Fast face recognition model
VERIFICATION_THRESHOLD = 0.40   # Match threshold (lower = stricter)
LIVENESS_ENABLED = True         # Enable blink detection
FACE_DETECTOR_BACKEND = "opencv" # Fast face detection
```

## 🛠️ Tech Stack

- **GUI**: CustomTkinter (dark theme)
- **Face Detection**: OpenCV
- **Face Recognition**: DeepFace + Facenet
- **Database**: SQLite3
- **Computer Vision**: OpenCV
- **Deep Learning**: TensorFlow/Keras

## 📊 Performance

| Operation | Time |
|-----------|------|
| Face Detection | ~30ms |
| Embedding Generation (Facenet) | ~100ms |
| Verification | ~5ms |

*Live verification runs at ~3-5 FPS for smooth operation*

## 🔄 Recent Updates

- ⚡ Switched to Facenet model for 3-5x faster performance
- 🪟 Added professional ACCESS GRANTED/DENIED popups
- 📷 Camera auto-stops when face is verified
- 🎨 Improved popup visibility and sizing

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [DeepFace](https://github.com/serengil/deepface) - Face recognition library
- [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter) - Modern GUI toolkit
- [Facenet](https://github.com/davidsandberg/facenet) - Fast face embeddings

## ⚠️ Disclaimer

This project is for educational and research purposes. Ensure compliance with local laws and regulations regarding facial recognition technology.

---

Made with ❤️ by Kamran Abbasi

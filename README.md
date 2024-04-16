
# YouTube Scene Detector and GIF Generator

This Python application searches YouTube for videos based on a user's query, downloads the top video, detects scenes, extracts text using OCR, and generates a GIF of the detected scenes. The GIF is limited to 10 seconds to showcase key moments efficiently. The application also displays all text found within the scenes of the video.

## Features

- **YouTube Search**: Search YouTube based on user input and select videos based on view count and duration.
- **Scene Detection**: Utilizes `scenedetect` to find transition points in the video.
- **Text Extraction**: Implements `easyocr` to extract text from each detected scene.
- **GIF Creation**: Creates a GIF from selected scenes to quickly visualize content.
- **GUI**: Uses `PySimpleGUI` for an easy-to-use graphical interface.

## Installation

To run this project, you will need Python 3.6+ and the following packages:

- `opencv-python`
- `imageio`
- `pytube`
- `google-api-python-client`
- `isodate`
- `scenedetect`
- `easyocr`
- `PySimpleGUI`

You can install the necessary libraries using pip:

```bash
pip install opencv-python imageio pytube google-api-python-client isodate scenedetect easyocr PySimpleGUI
```

Ensure you have a valid YouTube API key which you can get from [Google Cloud Console](https://console.cloud.google.com/). Place your API key in a `config.py` file:

```python
YOUTUBE_API_KEY = 'your_youtube_api_key_here'
```

## Usage

Run the script using Python:

```bash
python main.py
```

Upon launching, the application will prompt you to enter a search query. After processing, it will display the most relevant video's GIF along with extracted texts from the scenes.

## Contributing

Contributions to this project are welcome! Here are a few ways you can help:

- Report bugs and request features by creating issues.
- Improve or propose new documentation.
- Submit pull requests with bug fixes or new features.


## Acknowledgments

- Thanks to the developers of the libraries used in this project.


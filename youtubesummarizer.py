import cv2
import os
from pytube import YouTube
from googleapiclient.discovery import build
import isodate
from scenedetect import VideoManager
from scenedetect import SceneManager
from scenedetect.detectors import ContentDetector
from config import YOUTUBE_API_KEY
import easyocr  # Import EasyOCR library


def search_youtube(query):
    youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)
    request = youtube.search().list(
        q=query,
        part='snippet',
        type='video',
        maxResults=20,
        videoDuration='medium',  # Fetches videos from 4 minutes to 20 minutes
        order='viewCount'  # Sorted by view count
    )
    response = request.execute()

    for item in response.get('items', []):
        video_id = item['id']['videoId']
        video_title = item['snippet']['title']
        video_details = youtube.videos().list(
            part="contentDetails,statistics",
            id=video_id
        ).execute()

        if not video_details['items']:
            continue

        duration = video_details['items'][0]['contentDetails']['duration']
        duration_seconds = convert_duration(duration)
        views = video_details['items'][0]['statistics']['viewCount']

        if duration_seconds < 600:  # Less than 10 minutes
            return video_id, video_title, duration_seconds, views
    return None, None, None, None

def convert_duration(duration):
    """ Convert ISO 8601 duration to seconds """
    return isodate.parse_duration(duration).total_seconds()

def createWatermark(image):
    font = cv2.FONT_HERSHEY_SIMPLEX
    watermark_text = "Gilad Twili"
    text_size = cv2.getTextSize(watermark_text, font, 1, 2)[0]
    text_x = image.shape[1] - text_size[0] - 10  # 10 pixels from the right edge
    text_y = image.shape[0] - 10  # 10 pixels from the bottom edge
    cv2.putText(image, watermark_text, (text_x, text_y), font, 1, (255, 0, 0), 2, cv2.LINE_AA)

def find_scenes(video_path, threshold=500.0):
    # Create a video manager object for the video.
    video_manager = VideoManager([video_path])
    scene_manager = SceneManager()

    # Add ContentDetector algorithm (with a threshold).
    scene_manager.add_detector(ContentDetector(threshold=threshold))

    # Start the video manager and perform scene detection.
    video_manager.start()
    scene_manager.detect_scenes(frame_source=video_manager)

    # Obtain list of detected scenes.
    scene_list = scene_manager.get_scene_list()

    # We can save the scenes as images:
    save_images(video_path, scene_list)

    video_manager.release()

def save_images(video_path, scene_list, max_images=5):
    # Base directory where the script is running/
    save_dir = "images"
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)  # Create the directory if it doesn't exist

    video_capture = cv2.VideoCapture(video_path)
    count = 0  # Initialize counter for saved images

    reader = easyocr.Reader(['en'])  # Initialize the EasyOCR reader for English

    for start_time, _ in scene_list:
        if count >= max_images: 
            break  # Stop if the limit is reached

        # Set video to start frame
        video_capture.set(cv2.CAP_PROP_POS_MSEC, start_time.get_seconds() * 1000)
        success, image = video_capture.read()
        if success:
            # Perform OCR on the saved image
            results = reader.readtext(image)
            for (_ , text, _) in results:
                print(f'{text}')

            # Adding watermark to the image
            createWatermark(image)
            filename = os.path.join(save_dir, f'frame_at_{start_time.get_seconds()}.jpg')
            cv2.imwrite(filename, image)
            count += 1  # Increment the counter after saving an image

    video_capture.release()  # Make sure to release the video capture object

def download_and_detect_scenes(video_id, title):
    yt = YouTube(f'https://www.youtube.com/watch?v={video_id}')
    stream = yt.streams.filter(file_extension='mp4').first()
    video_path = stream.download()
    print(f'Downloaded {title}')
    find_scenes(video_path, threshold=27)  # You can adjust the threshold based on testing.

def main():
    subject = input("Please enter a subject for the video: ")
    video_id, title, duration, views = search_youtube(subject)
    if video_id:
        print(f'Top video: {title} ({duration} seconds, {views} views)')
        download_and_detect_scenes(video_id, title)
    else:
        print("No suitable video found.")

if __name__ == "__main__":
    main()
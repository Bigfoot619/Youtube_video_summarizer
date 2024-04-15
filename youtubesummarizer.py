import cv2
import os
import imageio
from pytube import YouTube
from googleapiclient.discovery import build
import isodate
from scenedetect import VideoManager
from scenedetect import SceneManager
from scenedetect.detectors import ContentDetector
from config import YOUTUBE_API_KEY
import easyocr  # Import EasyOCR library
from IPython.display import Image, display
import PySimpleGUI as sg



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

def find_scenes(video_path, threshold):
    # Create a video manager object for the video.
    video_manager = VideoManager([video_path])
    scene_manager = SceneManager()

    # Add ContentDetector algorithm (with a threshold).
    scene_manager.add_detector(ContentDetector(threshold=threshold))

    try:
        # Start the video manager and perform scene detection.
        video_manager.start()
        scene_manager.detect_scenes(frame_source=video_manager)

        # Obtain list of detected scenes.
        scene_list = scene_manager.get_scene_list(base_timecode=video_manager.get_base_timecode())  # Ensure this is set correctly

        return scene_list  # Make sure to return the scene list
    finally:
        video_manager.release()  # Ensure video manager is released even if an error occurs

def save_images(video_path, scene_list, max_images=4):
    # Base directory where the script is running/
    save_dir = "images"
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)  # Create the directory if it doesn't exist

    image_files = []  # List to hold image paths for GIF creation
    video_capture = cv2.VideoCapture(video_path)
    count = 0  # Initialize counter for saved images

    if scene_list is None or not scene_list:
        print("No scenes detected.")
        return image_files  # Return empty list if no scenes are detected
    
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
            image_files.append(filename)
            count += 1  # Increment the counter after saving an image

    video_capture.release()  # Make sure to release the video capture object
    return image_files

def download_and_detect_scenes(video_id, title):
    yt = YouTube(f'https://www.youtube.com/watch?v={video_id}')
    stream = yt.streams.filter(file_extension='mp4').first()
    video_path = stream.download()
    print(f'Downloaded {title}')
    scene_list = find_scenes(video_path, threshold=27)
    image_files = save_images(video_path, scene_list)
    process_and_display_gif(image_files)

def create_gif(image_files, output_path='output.gif'):
    with imageio.get_writer(output_path, mode='I', duration=0.5) as writer:
        for image_file in image_files:
            image = imageio.imread(image_file)
            writer.append_data(image)
    return output_path

def process_and_display_gif(image_files):
    gif_path = create_gif(image_files)
    display(Image(filename=gif_path))

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
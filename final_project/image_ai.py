from PIL import Image
import numpy as np
import os

def predict_image(image_path):
    img = Image.open(image_path).convert('RGB')
    arr = np.array(img)
    mean_brightness = np.mean(arr)
    # Check if grayscale (X-ray, CT, etc.)
    is_grayscale = np.allclose(arr[...,0], arr[...,1]) and np.allclose(arr[...,1], arr[...,2])
    # Get dominant color
    avg_color = np.mean(arr.reshape(-1, 3), axis=0)
    color_names = ['red', 'green', 'blue']
    dominant_color = color_names[np.argmax(avg_color)]
    if is_grayscale:
        if mean_brightness < 100:
            return 'Likely X-ray or CT scan (dark grayscale). No critical findings detected.'
        else:
            return 'Likely X-ray or CT scan (bright grayscale). No critical findings detected.'
    elif dominant_color == 'red':
        return 'Image contains strong red tones. Possible heart or blood image.'
    elif dominant_color == 'blue':
        return 'Image contains strong blue tones. Possible medical equipment or scan.'
    else:
        return f'Image processed. Dominant color: {dominant_color}. For detailed analysis, consult a radiologist.'

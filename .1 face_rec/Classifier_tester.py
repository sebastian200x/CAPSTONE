
from flask import Flask, render_template
import cv2

app = Flask(__name__)

@app.route('/')
def test_classifier():
    # Load the Haar classifier file
    classifier = cv2.CascadeClassifier('resources/haarcascade_frontalface_default.xml')

    # Check if the classifier is loaded successfully
    if classifier.empty():
        return 'Classifier not recognized by the app'

    return 'Classifier recognized by the app'

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=3333, debug=True)

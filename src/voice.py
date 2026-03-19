import speech_recognition as sr
import threading, time, io
from gtts import gTTS
from IPython.display import Audio, display

def get_voice_input(time_limit=5):
    recognizer = sr.Recognizer()

    with sr.Microphone() as source:
        print('다음 행동을 말씀해 주세요.')
        recognizer.adjust_for_ambient_noise(source, duration=0.5)
        audio = recognizer.record(source, duration=time_limit)

        user_input_text = recognizer.recognize_google(audio, language='ko-KR')
    
    return user_input_text


def play_voice(text):
    if not text:
        return
        
    try:
        tts = gTTS(text=text, lang='ko')
        filename = "temp_voice.mp3"
        tts.save(filename)

        display(Audio(filename, autoplay=True))
        
    except Exception as e:
        print(f"음성 재생 중 오류 발생: {e}")
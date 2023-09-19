import speech_recognition as sr
from pydub import AudioSegment


file_path = "audio.oga"

# Convert the audio file to OGG format
audio = AudioSegment.from_ogg(file_path)
ogg_file = file_path.replace(".oga", ".wav")
audio.export(ogg_file, format="wav")

# transcribe audio file
# use the audio file as the audio source
r = sr.Recognizer()
with sr.AudioFile("audio.wav") as source:
    audio = r.record(
        source)  # read the entire audio file

    transcript = r.recognize_google(audio, language="pt-BR")
print(transcript)

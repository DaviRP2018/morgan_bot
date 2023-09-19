import json
import logging
import os
import random

from datetime import date, datetime

import speech_recognition as sr
import telebot

from decouple import config
from gtts import gTTS
from pydub import AudioSegment
from telebot.types import InputFile, Message


SAVE_PATH = "tmp"
VALID_MIME_TYPES = ["ogg", "mp3", "wav", "flv", "m4a"]


def log(message: str, level: str = "info") -> None:
    """
    Levels of Log Message
    There are two built-in levels of the log message.
    Debug : These are used to give Detailed information, typically of interest
    only when diagnosing problems.
    Info : These are used to Confirm that things are working as expected
    Warning : These are used an indication that something unexpected happened,
    or indicative of some problem in the near
    future
    Error : This tells that due to a more serious problem, the software has not
     been able to perform some function
    Critical : This tells serious error, indicating that the program itself may
     be unable to continue running
    :param message:
    :param level:
    :rtype: None
    :return:
    """
    message = "{} ==|=====> {}".format(datetime.now().time(), message)
    filename = "logs/log - %s.log" % date.today()
    logging.basicConfig(
        filename=filename,
        format="%(asctime)s - %(levelname)s: %(message)s",
        filemode="w",
    )
    print(message)
    logger = logging.getLogger()
    if level == "info":
        logger.setLevel(logging.INFO)
        logger.info(message)
    elif level == "debug":
        logger.setLevel(logging.DEBUG)
        logger.debug(message)
    elif level == "warning":
        logger.setLevel(logging.WARNING)
        logger.warning(message)
    elif level == "error":
        logger.setLevel(logging.ERROR)
        logger.error(message)
    elif level == "critical":
        logger.setLevel(logging.CRITICAL)
        logger.critical(message)


def save_user(message: Message) -> None:
    log(message.from_user.first_name)
    with open("users.json", "r") as users_json:
        data = users_json.read()
    users = json.loads(data)

    if message.from_user.first_name not in users:
        users[message.from_user.first_name] = message.from_user.id
        with open("users.json", "w") as users_json:
            users_json.write(json.dumps(users))


def clean(file_unique_path) -> None:
    log("Cleaning tmp folder")
    try:
        os.remove(file_unique_path)
        log("Todos os arquivos em 'tmp' foram apagados com sucesso.")
    except Exception as err:
        log(f"Ocorreu um erro ao apagar os arquivos: {str(err)}")


def error_message(bot, message, err):
    log(str(err), "error")
    bot.send_animation(
        chat_id=message.chat.id,
        animation=InputFile(open("gifs/error/giphy_error_1.gif", "rb")),
    )
    bot.send_message(message.chat.id, "Deu ruim")


def prepare_audio(bot, message, sound_source):
    try:
        source = getattr(message, sound_source)
        if source.duration < 60:
            log(f"Estou ouvindo seu audio -- {source.duration}")
            bot.send_message(message.chat.id, "Estou ouvindo seu audio")
        elif 60 <= source.duration < 120:
            log(f"Esse vai demorar um pouco -- {source.duration}")
            bot.reply_to(message, "Esse vai demorar um pouco")
        elif 120 <= source.duration < 240:
            log(
                f"Esse vai demorar bastante,"
                f" te aviso quando acabar de ouvir -- {source.duration}"
            )
            bot.reply_to(
                message,
                "Esse vai demorar bastante, te aviso quando acabar de ouvir",
            )
        elif 240 <= source.duration < 480:
            log(f"Te mandaram um podcast? -- {source.duration}")
            bot.reply_to(
                message,
                "Te mandaram um podcast?"
                " Assim que eu acabar de ouvir te mando mensagem",
            )
        elif source.duration >= 480:
            log(f"Audio gigantesco -- {source.duration}")
            bot.send_animation(
                chat_id=message.chat.id,
                animation=InputFile(
                    open("gifs/surprised/giphy_surprised_1.gif", "rb")
                ),
            )
            bot.send_message(
                message.chat.id, f"{parse_time(source.duration)} de audio..."
            )
            bot.send_message(
                message.chat.id,
                "Minha versão não paga não vai aguentar"
                " tanto tempo de espera pra te responder."
                " Mas vou tentar.",
            )

        # Download file
        file_info = bot.get_file(source.file_id)
        downloaded_file = bot.download_file(file_info.file_path)

        # Parse to WAV
        log(f"File mime type is: {source.mime_type}")
        mime_type = source.mime_type.replace("audio/", "")
        if mime_type == "mpeg":
            log(
                f"Probably a whatsapp voice, changing"
                f" mime type from {mime_type} to m4a"
            )
            mime_type = "m4a"
        file_unique_path = f"{SAVE_PATH}/{source.file_unique_id}.{mime_type}"
        with open(file_unique_path, "wb") as new_file:
            new_file.write(downloaded_file)

        tries = 0
        trying = True
        while tries < len(VALID_MIME_TYPES) and trying:
            try:
                audio = AudioSegment.from_file(file_unique_path, mime_type)
                wav_file = file_unique_path.replace(f".{mime_type}", ".wav")
                audio.export(wav_file, format="wav")
                trying = False
            except Exception as err:
                log(str(err), "error")
                mime_type = VALID_MIME_TYPES[tries]
                log(f"Trying with mime_type: {mime_type}")
                tries += 1
        if trying:
            raise Exception("Couldn't convert file")
        # Convert the audio file to OGG format

        language_code = message.from_user.language_code.split("-")
        country = language_code[1].upper()
        raw_language = language_code[0]
        language = f"{raw_language}-{country}"

        # transcribe audio file
        # use the audio file as the audio source
        r = sr.Recognizer()
        with sr.AudioFile(wav_file) as source:
            audio = r.record(source)  # read the entire audio file
            try:
                transcript = r.recognize_google(audio, language=language)
            except Exception as err:
                log(str(err), "error")
                transcript = r.recognize_google(audio, language="pt-BR")
        print(transcript)

    except Exception as err:
        log(str(err), "error")
        raise err
    else:
        log("Tá aqui o que você quer")
        bot.send_message(message.chat.id, "Tá aqui o que você quer")
        bot.reply_to(message, transcript)


def text_to_speech(bot, message):
    try:
        log("Estou gravando seu audio")
        bot.send_message(message.chat.id, "Estou gravando seu audio")
        # The text that you want to convert to audio

        text = message.text
        log(text)

        # Language in which you want to convert
        language = "pt"

        # Passing the text and language to the engine,
        # here we have marked slow=False. Which tells
        # the module that the converted audio should
        # have a high speed

        sound = gTTS(text=text, lang=language, slow=False)

        # Saving the converted audio in a mp3 file named
        # speech
        sound.save("tmp/speech.mp3")

        bot.send_audio(
            chat_id=message.chat.id,
            title="MorganBot fala",
            audio=open("tmp/speech.mp3", "rb"),
        )
    except Exception as err:
        error_message(bot, message, err)


def base_reply(bot, message, sound_source):
    try:
        save_user(message)
    except Exception as err:
        log(str(err), "error")

    try:
        prepare_audio(bot, message, sound_source)
    except Exception as err:
        error_message(bot, message, err)

    # finally:
    #     clean(file_unique_path)


def parse_time(seconds):
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    seconds = seconds % 60

    result = ""
    if hours > 0:
        result += f"{hours} hora{'s' if hours > 1 else ''} "
    if minutes > 0:
        result += f"{minutes} minuto{'s' if minutes > 1 else ''} "
    if seconds > 0:
        result += f"{seconds} segundo{'s' if seconds > 1 else ''}"

    return result.strip()


def main() -> None:
    try:
        bot = telebot.TeleBot(config("TOKEN"), parse_mode=None)

        @bot.message_handler(commands=["start", "help"])
        def send_welcome(message: Message) -> None:
            bot.reply_to(
                message,
                "Bem vindo! Eu sou capaz de gravar audios do que você"
                " me escreve e também de escrever os audios que você me mandar",
            )

        @bot.message_handler(
            func=lambda m: True,
            content_types=[
                "photo",
                "video",
                "document",
                "location",
                "contact",
                "sticker",
            ],
        )
        def reply_unsuported(message: Message) -> None:
            log("wat?")
            log(f"Received message type: {message.content_type}")
            bot.reply_to(message, "wat?")
            gif_idx = random.randint(1, 2)
            log(f"Selected gif: {gif_idx}")
            bot.send_animation(
                chat_id=message.chat.id,
                animation=InputFile(open(f"gifs/giphy_{gif_idx}.gif", "rb")),
            )

        @bot.message_handler(func=lambda m: True, content_types=["text"])
        def reply_text(message: Message) -> None:
            text_to_speech(bot, message)

        @bot.message_handler(func=lambda m: True, content_types=["voice"])
        def reply_voice(message: Message) -> None:
            base_reply(bot, message, "voice")

        @bot.message_handler(func=lambda m: True, content_types=["audio"])
        def reply_audio(message: Message) -> None:
            base_reply(bot, message, "audio")

        log("Bot started.")
        bot.polling(none_stop=False, interval=0, timeout=60)
    except Exception as err:
        log(str(err), "error")


if __name__ == "__main__":
    while True:
        main()

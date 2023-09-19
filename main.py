import json
import logging
import speech_recognition as sr
from pydub import AudioSegment
import os
from datetime import date, datetime
import telebot
from telebot.types import Message
from decouple import config
SAVE_PATH = "tmp/"


def log(message: str, level: str = "info") -> None:
    """
    Levels of Log Message
    There are two built-in levels of the log message.
    Debug : These are used to give Detailed information, typically of interest only when diagnosing problems.
    Info : These are used to Confirm that things are working as expected
    Warning : These are used an indication that something unexpected happened, or indicative of some problem in the near
    future
    Error : This tells that due to a more serious problem, the software has not been able to perform some function
    Critical : This tells serious error, indicating that the program itself may be unable to continue running
    :param message:
    :param level:
    :rtype: None
    :return:
    """
    message = "{} ==|=====> {}".format(datetime.now().time(), message)
    filename = "logs/log - %s.log" % date.today()
    logging.basicConfig(
        filename=filename, format="%(asctime)s - %(levelname)s: %(message)s", filemode="w"
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


def manage_user(message: Message) -> None:
    log(message.from_user.first_name)
    with open("users.json", "r") as users_json:
        data = users_json.read()
    users = json.loads(data)

    if message.from_user.first_name not in users:
        users[message.from_user.first_name] = message.from_user.id
        with open("users.json", "w") as users_json:
            users_json.write(json.dumps(users))


def clean() -> None:
    log("Cleaning tmp folder")
    try:
        for arquivo in os.listdir("tmp"):
            caminho_arquivo = os.path.join("tmp", arquivo)
            if os.path.isfile(caminho_arquivo):
                os.remove(caminho_arquivo)
        log(f"Todos os arquivos em 'tmp' foram apagados com sucesso.")
    except Exception as err:
        log(f"Ocorreu um erro ao apagar os arquivos: {str(err)}")


def main() -> None:
    try:
        bot = telebot.TeleBot(config("TOKEN"), parse_mode=None)

        @bot.message_handler(commands=["start", "help"])
        def send_welcome(message: Message) -> None:
            bot.reply_to(
                message, "Bem vindo! Me grave um audio"
                         " ou encaminhe um audio mp3 e"
                         " eu vou tentar transcrever para você usando o Google."
            )

        @bot.message_handler(func=lambda m: True, content_types=["voice"])
        def reply_voice(message: Message) -> None:
            try:
                manage_user(message)
            except Exception as err:
                log(str(err), "error")
                bot.send_message(
                    message.from_user.id, "Erro de conexão, por favor tente novamente mais tarde."
                )
            else:
                try:
                    bot.send_message(message.from_user.id, "Baixando seu audio...")
                    file_info = bot.get_file(message.voice.file_id)
                    downloaded_file = bot.download_file(file_info.file_path)
                    oga_file_path = "tmp/audio.oga"
                    wav_file_path = "tmp/audio.wav"
                    with open(oga_file_path, 'wb') as new_file:
                        new_file.write(downloaded_file)

                    # Convert the audio file to OGG format
                    audio = AudioSegment.from_ogg(oga_file_path)
                    ogg_file = oga_file_path.replace(".oga", ".wav")
                    audio.export(ogg_file, format="wav")

                    # transcribe audio file
                    # use the audio file as the audio source
                    r = sr.Recognizer()
                    with sr.AudioFile(wav_file_path) as source:
                        audio = r.record(
                            source)  # read the entire audio file

                        transcript = r.recognize_google(audio, language="pt-BR")
                    print(transcript)

                except Exception as err:
                    log(str(err), "error")
                    bot.send_message(message.from_user.id, "Error")
                else:
                    bot.send_message(message.from_user.id, "Tá aqui o que você quer:")
                    bot.send_message(message.chat.id, transcript)
            finally:
                clean()

        @bot.message_handler(func=lambda m: True, content_types=["audio"])
        def reply_audio(message: Message) -> None:
            try:
                manage_user(message)
            except Exception as err:
                log(str(err), "error")
                bot.send_message(
                    message.from_user.id,
                    "Erro de conexão, por favor tente novamente mais tarde."
                )
            else:
                try:
                    bot.send_message(message.from_user.id,
                                     "Escutando seu audio...")
                    file_info = bot.get_file(message.audio.file_id)
                    downloaded_file = bot.download_file(file_info.file_path)
                    mp3_file_path = "tmp/audio.mp3"
                    wav_file_path = "tmp/audio.wav"
                    with open(mp3_file_path, 'wb') as new_file:
                        new_file.write(downloaded_file)

                    # Convert the audio file to OGG format
                    audio = AudioSegment.from_mp3(mp3_file_path)
                    ogg_file = mp3_file_path.replace(".mp3", ".wav")
                    audio.export(ogg_file, format="wav")

                    # transcribe audio file
                    # use the audio file as the audio source
                    r = sr.Recognizer()
                    with sr.AudioFile(wav_file_path) as source:
                        audio = r.record(
                            source)  # read the entire audio file

                        transcript = r.recognize_google(audio, language="pt-BR")
                    print(transcript)

                except Exception as err:
                    log(str(err), "error")
                    bot.send_message(message.from_user.id, "Error")
                else:
                    bot.send_message(message.from_user.id,
                                     "Tá aqui o que você quer:")
                    bot.send_message(message.chat.id, transcript)
            finally:
                clean()

        log("Bot started.")
        bot.polling(none_stop=False, interval=0, timeout=20)
    except AssertionError as err:
        log(str(err), "error")
    except Exception as err:
        log(str(err), "error")


if __name__ == "__main__":
    while True:
        main()
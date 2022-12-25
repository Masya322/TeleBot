from __future__ import print_function

from dotenv import load_dotenv
import os

import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters

import os.path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload


logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level = logging.INFO
)

def creds():
    SCOPES = ['https://www.googleapis.com/auth/drive']
    # Показывает базовое использование Drive v3 API.
    # Выводит имена и идентификаторы первых 10 файлов, к которым у пользователя есть доступ.
    
    creds = None
    # В файле token.json хранятся токены доступа и обновления пользователя.
    # создается автоматически, когда поток авторизации завершается в первый раз
    
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    
    # Если нет сохраненных данных, позволить войти
    if not creds or not creds.valid:
        
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Сохранить данные по авторизации
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    
    return creds

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Hello!")

async def list_files(update: Update, context: ContextTypes.DEFAULT_TYPE):
    
    try:
        service = build('drive', 'v3', credentials=creds())
        # Вызов Drive API v3
        results = service.files().list(
            pageSize=10, fields="nextPageToken, files(id, name)").execute()
        items = results.get('files', [])

        if not items:
            print('No files found.')
            return
        print('Files:')
        for item in items:
            await context.bot.send_message(chat_id=update.effective_chat.id, text=item.get("name"))
            print(u'{0} ({1})'.format(item['name'], item['id']))
    except HttpError as error:
        # TODO(developer) Обрабатывать ошибки из Drive API
        print(f'An error occurred: {error}')

async def upload_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print('1')
    newFile = await update.message.effective_attachment.get_file()
    print(newFile)
    await newFile.download_to_drive(custom_path="downloaded/" + update.message.effective_attachment.file_name)
    print('2')
    try:
        # создание drive API =клиента
        print('3')
        service = build('drive', 'v3', credentials=creds())
        print('4')
        file_metadata = {'name': update.message.document.file_name}
        media = MediaFileUpload("downloaded/" + update.message.document.file_name,
                                mimetype=update.message.document.mime_type, resumable=True)
        print('5')
        
        file = service.files().create(body=file_metadata, media_body=media,
                                      fields='id').execute()
        print(F'File ID: {file.get("id")}'+'1')

    except HttpError as error:
        print('6')
        print(F'An error occurred: {error}')
        file = None

    await context.bot.send_message(chat_id=update.effective_chat.id, text="Success")

    return file.get('id')

if __name__ == '__main__':
    load_dotenv()

    application = ApplicationBuilder().token(os.getenv('TOKEN')).build()
     
    application.add_handler(CommandHandler('start', start) )
    application.add_handler(CommandHandler('file', list_files) )    
    application.add_handler(MessageHandler(filters.Document.ALL, upload_file))
    
    application.run_polling()

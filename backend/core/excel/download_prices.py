import imaplib
import os
from pathlib import Path
import smtplib
import shutil
import zoneinfo
import zipfile

from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.header import decode_header
from email.utils import parsedate_to_datetime
from email import encoders
import email
import datetime
import time

from .price_list_edit import PriceListEdit
from users.models import EmailRecipient

from backend.settings import SMTP_SERVER, SMTP_PORT, SMTP_LOGIN, SMTP_PASSWORD, BASE_DIR, MAIL_LOGIN, MAIL_PASSWORD

# BASE_DIR = Path(__file__).resolve().parents[2]
# ENV_FILE = os.getenv('DJANGO_ENV_FILE', os.path.join(os.path.dirname(__file__), '..', '..', '.env.dev'))
save_dir = BASE_DIR / 'uploads' / 'attachments_original'
# print(f'Абсолютный путь к env-файлу: {os.path.abspath(ENV_FILE)}')
# print(f'Существует ли файл? {os.path.isfile(ENV_FILE)}')
# print(f'Сохранять в {save_dir}')
# print(datetime.datetime.now().date(), 'Загрузка цен из почты...')
# environ.Env.read_env(ENV_FILE)
# env = environ.Env()

# SMTP_SERVER = env('SMTP_SERVER')
# SMTP_PORT = env.int('SMTP_PORT')
# SMTP_LOGIN = env('SMTP_LOGIN')
# SMTP_PASSWORD = env('SMTP_PASSWORD')
FROM_EMAIL = SMTP_LOGIN


def process_price_list_edit(file_path):
    try:
        with open(file_path, 'rb') as f:
            file_bytes = f.read()
    except FileNotFoundError:
        return file_path, os.path.basename(file_path)

    basename = os.path.basename(file_path)
    print(f'Обработка файла {basename}...')

    try:
        if os.path.getsize(file_path) < 15 * 1024 * 1024:
            processor = PriceListEdit(file_bytes, basename)
            processed_data = processor.get_stream
        else:
            print(f'{file_path} слишком большой размер файла')
            return file_path, os.path.basename(file_path)

        if processed_data is None:
            return file_path, basename

        new_basename = processor.get_file_name
        new_file_path = save_dir / new_basename

        if os.path.isfile(file_path):
            os.remove(file_path)

        with open(new_file_path, 'wb') as f:
            f.write(processed_data)
        print(f'Новый файл сохранен: {new_file_path}')

        return new_file_path, new_basename

    except Exception as e:
        print(f'Ошибка при обработке файла {file_path}: {e}')
        return file_path, basename


def control_len_name(filename):
    if len(filename) <= 30:
        return filename
    ext = '.csv' if filename.endswith('.csv') else '.xlsx'
    max_basename = 30 - len(ext)
    print(f'Имя файла: {filename}, длина: {len(filename)}, обрезанное: {filename[:max_basename]}{ext}')
    return f'{filename[:max_basename]}{ext}'


def rename_file(mail):
    print(f'Переименовываем файл {mail['filename']}')
    os.rename(os.path.join(save_dir, mail['filename']),
              os.path.join(save_dir, control_len_name(mail['filename'])))
    mail['filename'] = control_len_name(mail['filename'])
    mail['dir'] = save_dir / mail['filename']


def get_basename(filename):
    basename = ''
    if filename.endswith('.csv'):
        basename = filename[:-4]
    if filename.endswith('.xlsx'):
        basename = filename[:-5]
    return '_'.join([x for x in basename.split('_') if not x.isdigit()])


def control_duplicate_files(filename, save_dir):
    files = os.listdir(save_dir)
    if not files:
        return False
    filename = get_basename(filename)
    for file in files:
        if filename in file:
            return True
    return False


def decode_name(name):
    if not name:
        return None

    decoded_parts = []

    for fragment, charset in decode_header(name):
        if isinstance(fragment, bytes):
            if charset:
                try:
                    fragment = fragment.decode(charset)
                except (UnicodeDecodeError, LookupError) as e:
                    fragment = fragment.decode('utf-8', errors='replace')
            else:
                try:
                    fragment = fragment.decode('utf-8')
                except UnicodeDecodeError:
                    fragment = fragment.decode('latin-1', errors='replace')
        decoded_parts.append(fragment)
    return ''.join(decoded_parts)


def body_to_text(filename, sender):
    message = f"""
                    Здравствуйте!

                    Отправитель: {sender}
                    Имя файла: {filename}

                    ---
                    С уважением,
                    Ваш Django-бот.
                    """
    return message


def send_mail(subject, recipient, mail_data=None):
    msg = MIMEMultipart()
    msg['From'] = FROM_EMAIL
    msg['To'] = recipient
    msg['Subject'] = subject
    msg.attach(MIMEText(body_to_text(mail_data['filename'], mail_data['sender']), 'plain', 'utf-8'))

    if mail_data:
        filepath = mail_data['dir']
        if not os.path.exists(filepath):
            print(f'Файл не найден: {filepath}')
            return
        if os.path.getsize(filepath) > 15 * 1024 * 1024:
            print(f'Файл слишком большой: {filepath}')
            return
        with open(filepath, 'rb') as mail_data:
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(mail_data.read())
            encoders.encode_base64(part)

            filename = os.path.basename(filepath)
            part.add_header('Content-Disposition', f'attachment; filename={filename}')
            msg.attach(part)
            print(f'Файл {filepath} добавлен к письму.Данные письма: {mail_data}')
    with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT) as server:
        server.login(SMTP_LOGIN, SMTP_PASSWORD)
        server.sendmail(FROM_EMAIL, recipient, msg.as_string())


def fake_send_mail(subject, recipient, mail_data=None):
    print(f'Список получателей: {recipient}')
    if mail_data:
        filepath = mail_data['dir']
        if not os.path.exists(filepath):
            print(f'Файл не найден: {filepath}')
            return
        if os.path.getsize(filepath) > 15 * 1024 * 1024:
            print(f'Файл слишком большой: {filepath}')
            return
        print(f'Файл {filepath} добавлен к письму.')
        print(f'Данные письма: {mail_data}')
        time.sleep(2)

    return


def extract_sender_from_email(save_dir, filename):
    if not filename.endswith('.zip'):
        # filename = control_len_name(filename)
        print(f'Файл {filename} не является архивом')
        return save_dir / filename, filename

    extract_dir = os.path.join(save_dir, os.path.splitext(filename)[0])
    print(f'Распаковка архива {filename} в {extract_dir}')

    with zipfile.ZipFile(save_dir / filename, 'r') as zip_ref:
        zip_ref.extractall(extract_dir)
    extract_files = []
    for root, dirs, files in os.walk(extract_dir):
        for file in files:
            extract_files.append(os.path.join(root, file))
    print(f'Файлы в архиве: {extract_files}')

    if len(extract_files) == 1:
        src = extract_files[0]
        src_filename = os.path.basename(extract_files[0])
        dst_filename = save_dir / src_filename
        print(f'Исходное расположение: {extract_dir}, имя файла: {src_filename}, конечное: {dst_filename}')
        if os.path.isfile(src):
            print(f'Файл из архива {src} перемещен в {save_dir}')
            try:
                shutil.move(src, save_dir)
            except shutil.Error as e:
                print(f'Ошибка перемещения файла: {e}')
        shutil.rmtree(extract_dir)
        os.remove(save_dir / filename)
        return dst_filename, os.path.basename(dst_filename)
    else:
        file_size = 0
        src = ''
        for file in extract_files:
            if os.path.getsize(file) > file_size:
                file_size = os.path.getsize(file)
                src = file
        src_filename = os.path.basename(src)
        dst_filename = save_dir / src_filename
        print(f'Исходное расположение: {src}, имя файла: {src_filename}, конечное: {dst_filename}')
        if os.path.isfile(src):
            print(f'Файл из архива {src} перемещен в {save_dir}')
            try:
                shutil.move(src, save_dir)
            except shutil.Error as e:
                print(f'Ошибка перемещения файла: {e}')
        shutil.rmtree(extract_dir)
        os.remove(save_dir / filename)
        return dst_filename, os.path.basename(dst_filename)


def clean_folder_content(folder_path):
    if not str(folder_path).startswith(str(save_dir)):
        raise ValueError(f'Пути {folder_path} и {save_dir} не совпадают')
    if not os.path.exists(folder_path):
        print(f'Папка {folder_path} не существует')
        return
    for item in os.listdir(folder_path):
        item_path = os.path.join(folder_path, item)
        if os.path.isfile(item_path):
            os.remove(item_path)
        if os.path.isdir(item_path):
            shutil.rmtree(item_path)
    print(f'Папка {folder_path} очищена')


def save_file(part, filename, filepath):
    with open(filepath, 'wb') as f:
        f.write(part.get_payload(decode=True))
    print(f'Вложение сохранено: {filename}')


def save_mail_data(save_dir, filename, from_header, msg_date_utc, mails):
    new_filepath, basename = extract_sender_from_email(save_dir, filename)
    new_filepath, basename = process_price_list_edit(new_filepath)
    if basename in [m['filename'] for m in mails]:
        return
    mails.append({'filename': basename,
                  'dir': new_filepath,
                  'sender': from_header,
                  'timestamp': msg_date_utc.time()})


def download_prices_from_email():
    email_login = MAIL_LOGIN
    email_password = MAIL_PASSWORD
    print(f'Данные почты получены {email_login}, {email_password}')
    imap_server = "imap.mail.ru"
    port = 993
    try:
        mail = imaplib.IMAP4_SSL(imap_server, port)
        mail.login(email_login, email_password)
        print(f'Вход в почту {email_login} успешен')
        mail.select('INBOX')
        print('Почта открыта')
    except imaplib.IMAP4.error as e:
        print(f'Ошибка входа в почту {email_login}: {e}')
        return
    except ConnectionRefusedError:
        print('Ошибка подключения к IMAPсерверу')
        return

    status, messages = mail.search(None, 'ALL')
    if status != 'OK':
        print("Ошибка при поиске писем")
        mail.close()
        mail.logout()
        return

    messages_ids = messages[0].split()
    print(f'Найдено писем {len(messages_ids)}')
    mails = []

    os.makedirs(save_dir, exist_ok=True)

    clean_folder_content(save_dir)

    messages_ids.reverse()
    for message_id in messages_ids[:30]:
        status, data = mail.fetch(message_id, '(RFC822)')
        raw_email = data[0][1]
        msg = email.message_from_bytes(raw_email)

        data_header = msg['Date']
        msg_date = parsedate_to_datetime(data_header)
        msg_date_utc = msg_date.astimezone(datetime.timezone.utc)
        nsk_tz = zoneinfo.ZoneInfo('Asia/Novosibirsk')
        msg_date_nsk = msg_date_utc.astimezone(nsk_tz)
        today = datetime.datetime.now(datetime.timezone.utc).date()
        print(f'Дата сообщения: {msg_date_utc.date()} {msg_date_utc.time()} ({msg_date_nsk}), сегодня: {today}')
        from_header_original = msg['From']
        from_header = decode_name(from_header_original)

        if msg_date_nsk.date() != today:
            print(f'Отправитель: {from_header}')
            print()
            continue

        print(f'Отправитель: {from_header}')
        print(f'Дата: {msg_date_utc}')

        for part in msg.walk():
            if part.get_content_maintype() == 'multipart':
                print('Пропускаем вложение')
                continue
            if part.get_content_disposition() == 'attachment':
                print('Вложение найдено')

                original_filename = part.get_filename()
                filename = decode_name(original_filename)
                filepath = save_dir / filename
                # if not filename.endswith('.csv'):
                #     save_file(part, filename, filepath)
                #     save_mail_data(save_dir, filename, from_header, msg_date_utc, mails)
                if not control_duplicate_files(filename, save_dir) or not filename.endswith('.csv'):
                    # filename = control_len_name(str(filename))
                    save_file(part, filename, filepath)
                    save_mail_data(save_dir, filename, from_header, msg_date_utc, mails)
                else:
                    print(f'Обнаружен дубликат {filename}')

                print()

    mail.close()
    mail.logout()
    print('Почта закрыта')
    # print(f'Принято писем: {mails}')
    subjects = f'Отчет о количестве писем: {len(messages_ids)}'

    recipient_email = EmailRecipient.objects.filter(is_active=True).values_list('allowed_email__email', flat=True)

    if not recipient_email:
        raise Exception('Получателей не найдено')
    for mail in mails:
        # if mail['filename'] != control_len_name(mail['filename']):
        #     rename_file(mail)
        send_mail(subjects, recipient_email, mail)
    print(f'Отчет отправлен. Писем сохранено: {len(mails)}')

    # clean_folder_content(save_dir)


if __name__ == "__main__":
    download_prices_from_email()

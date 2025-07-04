from flask import Flask, render_template, redirect, url_for, request, flash, send_file
import subprocess
import os
import json
from utils.logger import setup_logging
from werkzeug.utils import secure_filename


setup_logging()

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Пути к файлам логов и отчётов
LOG_FILE = os.path.join('logs', 'delivery_log')
RECIPIENTS_FILE = 'data/recipients.csv'
SMTP_ACCOUNTS = 'config/smtp_accounts.json'
BURNED_ACCOUNTS = 'logs/burned_accounts.json'

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/run', methods=['POST'])
def run_workflow():
    try:
        subprocess.Popen(['python3', 'main.py', '--run-workflow'])
        flash('Пайплайн запущен!')
    except Exception as e:
        flash(f'Ошибка при запуске: {e}')
    return redirect(url_for('home'))

@app.route('/run-parser', methods=['POST'])
def run_parser():
    try:
        subprocess.Popen(['python3', 'main.py', '--run-parser'])
        flash('Парсер запущен!')
    except Exception as e:
        flash(f'Ошибка при запуске парсера: {e}')
    return redirect(url_for('home'))

@app.route('/run-checker', methods=['POST'])
def run_checker():
    try:
        subprocess.Popen(['python3', 'main.py', '--run-checker'])
        flash('Чекер запущен!')
    except Exception as e:
        flash(f'Ошибка при запуске чекера: {e}')
    return redirect(url_for('home'))

@app.route('/run-sender', methods=['POST'])
def run_sender():
    try:
        subprocess.Popen(['python3', 'main.py', '--run-sender'])
        flash('Рассылка запущена!')
    except Exception as e:
        flash(f'Ошибка при запуске рассылки: {e}')
    return redirect(url_for('home'))


@app.route('/logs')
def logs():
    log_path = os.path.join('logs', 'delivery_log.json')  # путь к файлу
    try:
        with open(log_path, 'r', encoding='utf-8') as f:
            log_entries = json.load(f)  # читаем как JSON-массив
    except FileNotFoundError:
        log_entries = []
    except json.JSONDecodeError:
        log_entries = []

    return render_template('logs.html', logs=log_entries)

@app.route('/recipients')
def recipients():
    try:
        with open(RECIPIENTS_FILE, 'r', encoding='utf-8') as f:
            rows = f.readlines()
    except FileNotFoundError:
        rows = ['Файл не найден']
    return render_template('recipients.html', rows=rows)

@app.route('/accounts')
def accounts():
    try:
        with open(SMTP_ACCOUNTS, 'r', encoding='utf-8') as f:
            accounts = json.load(f)
    except Exception as e:
        accounts = []
        flash(f'Ошибка при загрузке аккаунтов: {e}')
    return render_template('accounts.html', accounts=accounts)

@app.route('/accounts/edit/<username>', methods=['GET', 'POST'])
def edit_account(username):
    with open(SMTP_ACCOUNTS, 'r', encoding='utf-8') as f:
        accounts = json.load(f)

    account = next((a for a in accounts if a['username'] == username), None)
    if not account:
        flash('Аккаунт не найден.')
        return redirect(url_for('accounts'))

    if request.method == 'POST':
        account['host'] = request.form['host']
        account['port'] = int(request.form['port'])
        account['password'] = request.form['password']
        account['from_name'] = request.form['from_name']
        account['active'] = request.form.get('active') == 'on'

        # Обновим в списке
        for i in range(len(accounts)):
            if accounts[i]['username'] == username:
                accounts[i] = account

        with open(SMTP_ACCOUNTS, 'w', encoding='utf-8') as f:
            json.dump(accounts, f, indent=2, ensure_ascii=False)

        flash('Аккаунт обновлён!')
        return redirect(url_for('accounts'))

    return render_template('edit_account.html', account=account)

@app.route('/accounts/upload', methods=['GET', 'POST'])
def upload_accounts():
    if request.method == 'POST':
        file = request.files.get('json_file')
        if file and file.filename.endswith('.json'):
            try:
                uploaded_accounts = json.load(file)
                with open(SMTP_ACCOUNTS, 'r', encoding='utf-8') as f:
                    existing_accounts = json.load(f)
            except Exception as e:
                flash(f'Ошибка чтения файла: {e}')
                return redirect(request.url)

            existing_accounts.extend(uploaded_accounts)
            with open(SMTP_ACCOUNTS, 'w', encoding='utf-8') as f:
                json.dump(existing_accounts, f, indent=2, ensure_ascii=False)
            flash('Аккаунты успешно загружены.')
            return redirect(url_for('accounts'))
        else:
            flash('Пожалуйста, выберите корректный JSON-файл.')
    return render_template('upload_accounts.html')

@app.route('/download/logs')
def download_logs():
    log_path = os.path.join('logs', 'delivery_log.json')
    try:
        return send_file(log_path, as_attachment=True)
    except FileNotFoundError:
        flash('Файл логов не найден.')
        return redirect(url_for('logs'))

@app.route('/download/recipients')
def download_recipients():
    try:
        return send_file(RECIPIENTS_FILE, as_attachment=True)
    except FileNotFoundError:
        flash('Файл получателей не найден.')
        return redirect(url_for('recipients'))

@app.route('/status')
def status():
    try:
        with open('logs/pipeline_status.log', 'r', encoding='utf-8') as f:
            log_lines = f.readlines()[-50:]  # последние 50 строк
    except:
        log_lines = ['Лог не найден']
    return render_template('status.html', log_lines=log_lines)

# Обработка favicon.ico (чтобы убрать 404 в логах)
@app.route('/favicon.ico')
def favicon():
    return '', 204

@app.route('/accounts/add', methods=['GET', 'POST'])
def add_account():
    if request.method == 'POST':
        new_account = {
            "host": request.form['host'],
            "port": int(request.form['port']),
            "username": request.form['username'],
            "password": request.form['password'],
            "from_name": request.form['from_name'],
            "limit_per_session": int(request.form['limit_per_session']),
            "delay_seconds": int(request.form['delay_seconds'])
        }

        try:
            with open(SMTP_ACCOUNTS, 'r', encoding='utf-8') as f:
                accounts = json.load(f)
        except:
            accounts = []

        accounts.append(new_account)
        with open(SMTP_ACCOUNTS, 'w', encoding='utf-8') as f:
            json.dump(accounts, f, indent=2, ensure_ascii=False)

        flash('Аккаунт успешно добавлен!')
        return redirect(url_for('accounts'))

    return render_template('add_account.html')


@app.route('/accounts/delete/<username>', methods=['POST'])
def delete_account(username):
    try:
        with open(SMTP_ACCOUNTS, 'r', encoding='utf-8') as f:
            accounts = json.load(f)
        accounts = [acc for acc in accounts if acc['username'] != username]
        with open(SMTP_ACCOUNTS, 'w', encoding='utf-8') as f:
            json.dump(accounts, f, indent=2, ensure_ascii=False)
        flash('Аккаунт удалён.')
    except Exception as e:
        flash(f'Ошибка при удалении: {e}')
    return redirect(url_for('accounts'))


@app.route('/accounts/archive')
def archived_accounts():
    try:
        with open(BURNED_ACCOUNTS, 'r', encoding='utf-8') as f:
            accounts = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        accounts = []
    return render_template('archived_accounts.html', accounts=accounts)

@app.route('/accounts/restore/<username>', methods=['POST'])
def restore_account(username):
    try:
        with open(BURNED_ACCOUNTS, 'r', encoding='utf-8') as f:
            archived = json.load(f)
        with open(SMTP_ACCOUNTS, 'r', encoding='utf-8') as f:
            active = json.load(f)
    except:
        flash('Ошибка при чтении файлов.')
        return redirect(url_for('archived_accounts'))

    # Найти аккаунт
    to_restore = [acc for acc in archived if acc['username'] == username]
    if not to_restore:
        flash('Аккаунт не найден.')
        return redirect(url_for('archived_accounts'))

    # Удалить из архива и добавить в активные
    archived = [acc for acc in archived if acc['username'] != username]
    active.append(to_restore[0])

    with open(BURNED_ACCOUNTS, 'w', encoding='utf-8') as f:
        json.dump(archived, f, indent=2, ensure_ascii=False)
    with open(SMTP_ACCOUNTS, 'w', encoding='utf-8') as f:
        json.dump(active, f, indent=2, ensure_ascii=False)

    flash('Аккаунт восстановлен!')
    return redirect(url_for('archived_accounts'))

if __name__ == '__main__':
    app.run(debug=True, port=8000)

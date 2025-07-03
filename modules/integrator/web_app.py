from flask import Flask, render_template, redirect, url_for, request, flash
import subprocess
import os
import json

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Пути к файлам логов и отчётов
LOG_FILE = 'logs/smtp_delivery.log'
RECIPIENTS_FILE = 'data/recipients.csv'
SMTP_ACCOUNTS = 'config/smtp_accounts.json'

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

@app.route('/logs')
def logs():
    try:
        with open(LOG_FILE, 'r', encoding='utf-8') as f:
            log_content = f.read()
    except FileNotFoundError:
        log_content = 'Файл логов не найден.'
    return render_template('logs.html', log=log_content)

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
    except:
        accounts = []
    return render_template('accounts.html', accounts=accounts)

@app.route('/status')
def status():
    try:
        with open('logs/sender.txt', 'r', encoding='utf-8') as f:
            log_lines = f.readlines()[-50:]  # последние 50 строк
    except:
        log_lines = ['Лог не найден']
    return render_template('status.html', log_lines=log_lines)


if __name__ == '__main__':
    app.run(debug=True, port=8000)

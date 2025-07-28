import time
from plyer import notification
import logging
from datetime import datetime
import requests
import socket
import json
import sys
import os

# Конфигурация программы (можно изменить в config.json)
CONFIG = {
    "CHECK_INTERVAL": 600,          # 10 минут в секундах
    "RESPONSE_TIME": 120,           # 2 минуты в секундах
    "TARGET_WORD": "проверкавнимания",      # Слово для проверки
    "SERVER_URL": "http://localhost:5000",  # URL сервера для отправки логов
    "USER_ID": None,                # Идентификатор пользователя (устанавливается при регистрации)
    "MACHINE_ID": socket.gethostname(),  # Идентификатор машины
    "LOG_LOCALLY": True,            # Сохранять логи локально
    "LOG_TO_SERVER": True           # Отправлять логи на сервер
}

def load_config():
    """Загрузить конфигурацию из файла"""
    config_path = os.path.join(os.path.dirname(__file__), 'config.json')
    if os.path.exists(config_path):
        with open(config_path, 'r') as f:
            CONFIG.update(json.load(f))

def save_config():
    """Сохранить конфигурацию в файл"""
    config_path = os.path.join(os.path.dirname(__file__), 'config.json')
    with open(config_path, 'w') as f:
        json.dump(CONFIG, f, indent=4)

def setup_logger():
    """Настройка логгера"""
    logger = logging.getLogger('attention_checker')
    logger.setLevel(logging.INFO)
    
    if CONFIG['LOG_LOCALLY']:
        # Локальный файловый лог
        log_path = os.path.join(os.path.dirname(__file__), 'attention_check.log')
        file_handler = logging.FileHandler(log_path)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s', 
            datefmt='%Y-%m-%d %H:%M:%S'
        ))
        logger.addHandler(file_handler)
    
    # Консольный лог
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s', 
        datefmt='%Y-%m-%d %H:%M:%S'
    ))
    logger.addHandler(console_handler)
    
    return logger

def send_log_to_server(data):
    """Отправить лог на сервер"""
    if not CONFIG['LOG_TO_SERVER'] or not CONFIG['SERVER_URL']:
        return False
    
    try:
        data.update({
            'user_id': CONFIG['USER_ID'],
            'machine_id': CONFIG['MACHINE_ID'],
            'timestamp': datetime.now().isoformat()
        })
        
        response = requests.post(
            f"{CONFIG['SERVER_URL']}/api/logs",
            json=data,
            timeout=5
        )
        return response.status_code == 200
    except Exception as e:
        logger.warning(f"Ошибка при отправке лога на сервер: {str(e)}")
        return False

def show_notification(title, message):
    """Показать уведомление"""
    try:
        notification.notify(
            title=title,
            message=message,
            app_name="Проверка внимания"
        )
    except Exception as e:
        logger.warning(f"Ошибка при показе уведомления: {str(e)}")

def check_user_input():
    """Проверить ввод пользователя"""
    start_time = time.time()
    attempts = 0
    success = False
    
    while time.time() - start_time < CONFIG['RESPONSE_TIME']:
        try:
            user_input = input(f"Введите слово '{CONFIG['TARGET_WORD']}' в течение {CONFIG['RESPONSE_TIME']//60} минут: ")
            attempts += 1
            
            if user_input.strip().lower() == CONFIG['TARGET_WORD'].lower():
                print("Правильно! Проверка пройдена.")
                logger.info(f"Проверка пройдена. Попыток: {attempts}")
                log_data = {
                    'event_type': 'check_success',
                    'attempts': attempts,
                    'response_time': time.time() - start_time
                }
                send_log_to_server(log_data)
                success = True
                break
        except Exception as e:
            logger.error(f"Ошибка при вводе: {str(e)}")
            break
    
    if not success:
        print(f"Время вышло! Вы не ввели правильное слово '{CONFIG['TARGET_WORD']}'.")
        logger.warning("Проверка не пройдена: время истекло")
        log_data = {
            'event_type': 'check_failed',
            'attempts': attempts,
            'response_time': CONFIG['RESPONSE_TIME']
        }
        send_log_to_server(log_data)
    
    return success

def register_user():
    """Зарегистрировать нового пользователя на сервере"""
    if not CONFIG['LOG_TO_SERVER'] or not CONFIG['SERVER_URL']:
        logger.info("Регистрация на сервере отключена в настройках")
        return True
    
    try:
        response = requests.post(
            f"{CONFIG['SERVER_URL']}/api/register",
            json={
                'machine_id': CONFIG['MACHINE_ID'],
                'username': input("Введите имя пользователя для регистрации: ")
            },
            timeout=5
        )
        
        if response.status_code == 200:
            data = response.json()
            CONFIG['USER_ID'] = data['user_id']
            save_config()
            logger.info(f"Успешная регистрация. User ID: {CONFIG['USER_ID']}")
            return True
        else:
            logger.error(f"Ошибка регистрации: {response.text}")
            return False
    except Exception as e:
        logger.error(f"Ошибка при регистрации: {str(e)}")
        return False

def check_registration():
    """Проверить регистрацию пользователя"""
    if not CONFIG['USER_ID']:
        print("Вы не зарегистрированы в системе.")
        while not register_user():
            print("Попробуйте еще раз или нажмите Ctrl+C для выхода.")
    else:
        logger.info(f"Используется User ID: {CONFIG['USER_ID']}")

def main():
    """Основная функция программы"""
    global logger
    
    # Инициализация
    load_config()
    logger = setup_logger()
    
    logger.info("Программа проверки внимания запущена")
    logger.info(f"Идентификатор машины: {CONFIG['MACHINE_ID']}")
    
    # Проверка регистрации
    check_registration()
    
    # Основной цикл
    while True:
        try:
            time.sleep(CONFIG['CHECK_INTERVAL'])
            
            show_notification(
                "Проверка внимания",
                f"Введите слово '{CONFIG['TARGET_WORD']}' в течение 2 минут в консоль программы."
            )
            
            print(f"\nПроверка внимания! Введите слово '{CONFIG['TARGET_WORD']}' в течение 2 минут.")
            check_user_input()
            
        except KeyboardInterrupt:
            logger.info("Программа завершена пользователем")
            send_log_to_server({'event_type': 'program_exit'})
            sys.exit(0)
        except Exception as e:
            logger.error(f"Критическая ошибка: {str(e)}")
            time.sleep(60)  # Подождать перед повторной попыткой

if __name__ == "__main__":
    main()

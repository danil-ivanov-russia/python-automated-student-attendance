def get_key():
    file = open('constants/fernet_key.key', 'rb')
    key = file.read()
    file.close()
    return key


ENCRYPTION_KEY = get_key()

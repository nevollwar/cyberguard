# Базовые исключения приложения для понятных сообщений об ошибках

class CyberGuardError(Exception):
    pass

class ModelLoadError(CyberGuardError):
    pass

class DataValidationError(CyberGuardError):
    pass

class ClassificationError(CyberGuardError):
    pass

class StorageError(CyberGuardError):
    pass
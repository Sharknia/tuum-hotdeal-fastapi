import logging
import sys  # sys.stderr 사용 위해 임포트


class AppLogger:
    _instance = None

    def __new__(cls, name: str):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize(name)
        # 참고: 이름이 다른 로거를 요청해도 기존 인스턴스를 반환하는 현재 로직 유지
        # 필요시 여러 이름의 로거를 관리하도록 수정 가능
        return cls._instance

    def _initialize(self, name: str):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)  # 기본 로그 레벨 설정

        # 콘솔 핸들러 추가 (중복 방지)
        if not self.logger.handlers:
            console_handler = logging.StreamHandler(sys.stderr)  # stderr 명시
            console_handler.setLevel(logging.INFO)  # 핸들러 레벨 설정
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - [%(levelname)s] - %(message)s"  # 포맷 개선
            )
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)
            # 루트 로거로 전파 방지 (선택 사항, Uvicorn 등 사용 시 중복 로깅 방지 도움)
            self.logger.propagate = False

    def info(self, message: str, *args, **kwargs):
        self.logger.info(message, *args, **kwargs)

    def warning(self, message: str, *args, **kwargs):
        self.logger.warning(message, *args, **kwargs)

    def error(self, message: str, *args, **kwargs):
        self.logger.error(message, *args, **kwargs)

    def debug(self, message: str, *args, **kwargs):
        self.logger.debug(message, *args, **kwargs)

    def exception(self, message: str, *args, **kwargs):
        """예외 정보와 함께 에러 로그 기록"""
        self.logger.exception(message, *args, **kwargs)


# 공통 Logger 인스턴스 생성 (모듈 이름으로 로거 이름 지정)
# AppLogger 인스턴스의 logger 속성을 직접 할당
logger = AppLogger(__name__).logger


# 다른 모듈에서 쉽게 가져다 쓰기 위한 함수 (선택 사항)
def get_logger(name: str = "app") -> logging.Logger:
    # 싱글턴 인스턴스를 통해 로거가 설정되도록 보장 (이름은 다를 수 있음)
    AppLogger(name)
    return logging.getLogger(name)

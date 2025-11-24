import pytest
import requests
import logging
from typing import Dict, Any, Optional
import urllib3
import warnings

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
warnings.filterwarnings("ignore", message="Unverified HTTPS request")

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class RedfishClient:
    def __init__(self, base_url: str, username: str, password: str):
        self.base_url = base_url.rstrip('/')
        self.username = username
        self.password = password
        self.session = requests.Session()
        self.session.verify = False
        self.token = None
        self.authenticated = False
        
    def authenticate(self) -> Optional[str]:
        auth_url = f"{self.base_url}/redfish/v1/SessionService/Sessions"
        auth_data = {
            "UserName": self.username,
            "Password": self.password
        }
        
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                response = self.session.post(auth_url, json=auth_data)
            
            logger.info(f"Статус аутентификации: {response.status_code}")
            
            if response.status_code == 401:
                logger.error("Ошибка аутентификации: неверные учетные данные")
                return None
            
            response.raise_for_status()
            self.token = response.headers.get('X-Auth-Token')

            if self.token:
                self.session.headers.update({'X-Auth-Token': self.token})
                self.authenticated = True
                logger.info("Токен аутентификации получен")
            else:
                logger.warning("Токен не получен")
                self.session.auth = (self.username, self.password)
                self.authenticated = True
            
            return self.token
            
        except Exception as e:
            logger.error(f"Ошибка аутентификации: {e}")
            return None
    
    def get(self, endpoint: str) -> Dict[Any, Any]:
        url = f"{self.base_url}{endpoint}"

        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            response = self.session.get(url)

        response.raise_for_status()
        
        return response.json()
    
    def post(self, endpoint: str, data: Dict[Any, Any]) -> requests.Response:
        url = f"{self.base_url}{endpoint}"

        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            response = self.session.post(url, json=data)

        logger.info(f"POST {endpoint} - статус: {response.status_code}")

        return response

def pytest_addoption(parser):
    parser.addoption("--bmc-url", default="https://localhost:2443", help="URL OpenBMC сервера")
    parser.addoption("--username", default="root", help="Имя пользователя OpenBMC")
    parser.addoption("--password", default="0penBmc", help="Пароль OpenBMC")

@pytest.fixture(scope="session")
def redfish_client(request) -> RedfishClient:
    base_url = request.config.getoption("--bmc-url")
    username = request.config.getoption("--username")
    password = request.config.getoption("--password")
    
    logger.info(f"Подключение к {base_url} с пользователем {username}")
    client = RedfishClient(base_url, username, password)
    
    token = client.authenticate()

    if token:
        logger.info(f"Успешно подключено к {base_url}")
    else:
        pytest.fail(f"Не удалось аутентифицироваться на {base_url}")
    
    return client

@pytest.fixture(scope="session")
def system_info(redfish_client):
    try:
        info = redfish_client.get("/redfish/v1/Systems/system")
        logger.info(f"Информация о системе получена")

        return info
    except Exception as e:
        pytest.fail(f"Не удалось получить информацию о системе: {e}")
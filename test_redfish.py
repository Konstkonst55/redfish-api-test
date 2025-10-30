import pytest
import requests
import logging
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from conftest import RedfishClient

logger = logging.getLogger(__name__)

class TestRedfishAuthentication:
    """Тесты аутентификации в Redfish API"""
    
    def test_authentication_success(self, redfish_client):
        """Тест успешной аутентификации"""
        assert redfish_client.authenticated == True
        assert redfish_client.token is not None

        logger.info("Аутентификация прошла успешно")
    
    def test_authentication_response_code(self, redfish_client):
        """Тест кода ответа при аутентификации"""
        response = redfish_client.session.get(f"{redfish_client.base_url}/redfish/v1/")
        assert response.status_code == 200

        logger.info("Код ответа 200 при аутентифицированном запросе")

class TestSystemInfo:
    """Тесты получения информации о системе"""
    
    def test_get_system_info_status_code(self, redfish_client):
        """Тест статус-кода при получении информации о системе"""
        response = redfish_client.session.get(
            f"{redfish_client.base_url}/redfish/v1/Systems/system"
        )
        assert response.status_code == 200

        logger.info("Код ответа 200 при запросе информации о системе")
    
    def test_system_info_contains_status_and_powerstate(self, system_info):
        """Тест наличия Status и PowerState в ответе"""
        assert "Status" in system_info
        assert "PowerState" in system_info

        logger.info(f"Статус системы: {system_info.get('Status')}")
        logger.info(f"Состояние питания: {system_info.get('PowerState')}")
    
    def test_system_info_structure(self, system_info):
        """Тест структуры ответа информации о системе"""
        required_fields = ["Id", "Name", "Status", "PowerState", "Actions"]
        
        for field in required_fields:
            assert field in system_info, f"Отсутствует обязательное поле: {field}"
        
        logger.info("Все обязательные поля присутствуют в ответе")

class TestPowerManagement:
    """Тесты управления питанием"""
    
    def test_power_state_reading(self, redfish_client):
        """Тест чтения состояния питания"""
        system_info = redfish_client.get("/redfish/v1/Systems/system")
        power_state = system_info.get("PowerState")
        
        valid_states = ["On", "Off", "PoweringOn", "PoweringOff", "Paused", "Reset"]
        assert power_state in valid_states, f"Неизвестное состояние питания: {power_state}"
        
        logger.info(f"Текущее состояние питания: {power_state}")
    
    def test_power_control_endpoint_accessible(self, redfish_client):
        """Тест доступности endpoint управления питанием"""

        power_control_url = "/redfish/v1/Systems/system/Actions/ComputerSystem.Reset"
        test_data = {"ResetType": "On"}
        
        response = redfish_client.post(power_control_url, test_data)
        
        assert response.status_code in [200, 202, 204], f"Неожиданный код ответа: {response.status_code}" 
        
        logger.info(f"Endpoint управления питанием доступен, код ответа: {response.status_code}")
    
    def test_power_command_validation(self, redfish_client):
        """Тест валидации различных команд питания"""
        power_control_url = "/redfish/v1/Systems/system/Actions/ComputerSystem.Reset"
        
        safe_commands = ["On", "GracefulRestart"]
        
        for command in safe_commands:
            test_data = {"ResetType": command}
            response = redfish_client.post(power_control_url, test_data)
            
            assert response.status_code != 400, f"Команда {command} невалидна"
            logger.info(f"Команда {command} принята, код: {response.status_code}")

class TestSystemComponents:
    """Тесты компонентов системы"""
    
    def test_system_processor_info(self, redfish_client):
        """Тест информации о процессорах"""
        system_info = redfish_client.get("/redfish/v1/Systems/system")
        processor_summary = system_info.get("ProcessorSummary", {})
        
        count = processor_summary.get("Count", 0)
        logger.info(f"Количество процессоров: {count}")
        
        processors_url = "/redfish/v1/Systems/system/Processors"
        processors_data = redfish_client.get(processors_url)

        assert "Members" in processors_data
        logger.info(f"Processors endpoint доступен")
    
    def test_system_memory_info(self, redfish_client):
        """Тест информации о памяти"""
        system_info = redfish_client.get("/redfish/v1/Systems/system")
        memory_summary = system_info.get("MemorySummary", {})
        
        total_memory = memory_summary.get("TotalSystemMemoryGiB", 0)
        logger.info(f"Общая память системы: {total_memory} GiB")
        
        memory_url = "/redfish/v1/Systems/system/Memory"
        memory_data = redfish_client.get(memory_url)

        assert "Members" in memory_data
        logger.info(f"Memory endpoint доступен")
    
class TestChassisInfo:
    """Тесты информации о шасси"""
    
    def test_chassis_discovery(self, redfish_client):
        """Тест обнаружения шасси"""
        chassis_url = "/redfish/v1/Chassis"
        chassis_data = redfish_client.get(chassis_url)
        
        assert "Members" in chassis_data
        assert len(chassis_data["Members"]) > 0
        
        first_chassis = chassis_data["Members"][0]
        chassis_detail = redfish_client.get(first_chassis["@odata.id"])
        
        assert "Name" in chassis_detail
        logger.info(f"Найдено шасси: {chassis_detail.get('Name')}")
        
    def test_chassis_thermal(self, redfish_client):
        """Тест thermal информации шасси"""
        chassis_url = "/redfish/v1/Chassis"
        chassis_data = redfish_client.get(chassis_url)
        
        assert "Members" in chassis_data
        assert len(chassis_data["Members"]) > 0
        
        first_chassis = chassis_data["Members"][0]
        chassis_detail = redfish_client.get(first_chassis["@odata.id"])
        
        if "ThermalSubsystem" in chassis_detail:
            thermal_url = chassis_detail["ThermalSubsystem"]["@odata.id"]
            try:
                thermal_data = redfish_client.get(thermal_url)
                logger.info("Thermal информация доступна")
                
                if "Temperatures" in thermal_data:
                    logger.info(f"Найдено {len(thermal_data['Temperatures'])} температурных датчиков")

                if "Fans" in thermal_data:
                    logger.info(f"Найдено {len(thermal_data['Fans'])} вентиляторов")
                    
            except requests.exceptions.HTTPError:
                logger.info("Thermal endpoint не доступен")
        else:
            logger.info("Thermal информация отсутствует в шасси")

class TestErrorHandling:
    """Тесты обработки ошибок"""
    
    def test_invalid_authentication(self):
        """Тест неверной аутентификации"""
        invalid_client = RedfishClient(
            base_url="https://localhost:2443",
            username="wrong_user", 
            password="wrong_password"
        )
        
        result = invalid_client.authenticate()

        assert result is None, "Аутентификация с неверными данными должна возвращать None"
        assert invalid_client.authenticated == False, "Флаг authenticated должен быть False"
        
        logger.info("Обработка неверной аутентификации работает корректно")
    
    def test_invalid_endpoint(self, redfish_client):
        """Тест запроса к несуществующему endpoint"""
        response = redfish_client.session.get(
            f"{redfish_client.base_url}/redfish/v1/InvalidEndpoint"
        )
        
        assert response.status_code == 404

        logger.info("Обработка неверного endpoint работает корректно")

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
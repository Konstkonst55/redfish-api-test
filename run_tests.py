import subprocess
import sys

def run_tests():
    """Запуск тестов"""
    cmd = [
        "pytest",
        "test_redfish.py",
        "--bmc-url=https://localhost:2443",
        "--username=root", 
        "--password=0penBmc",
        "-v",
        "--html=test_report.html",
        "--self-contained-html",
        "--disable-warnings"
    ]
    
    print(f"Команда: {' '.join(cmd)}\n")
    
    result = subprocess.run(cmd)
    
    if result.returncode == 0:
        print("Все тесты прошли успешно!")
    else:
        print("Некоторые тесты не прошли")
        
    return result.returncode

if __name__ == "__main__":
    sys.exit(run_tests())
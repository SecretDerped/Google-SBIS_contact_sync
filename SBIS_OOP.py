import json
import logging
import requests
from datetime import date

console_out = logging.StreamHandler()
file_log = logging.FileHandler(f"application.log", mode="w")
logging.basicConfig(handlers=(file_log, console_out), level=logging.DEBUG,
                    format='[%(asctime)s | %(levelname)s]: %(message)s')


class SABYAccessDenied(Exception):
    pass


class SBISManager:
    def __init__(self, login: str = '', password: str = ''):
        self.login = login
        self.password = password
        self.base_url = 'https://api.sbis.ru'
        self.headers = {
            'Host': 'online.sbis.ru',
            'Content-Type': 'application/json-rpc; charset=utf-8',
            'Accept': 'application/json-rpc'
        }

    def auth(self):
        payload = {
            "jsonrpc": "2.0",
            "method": 'СБИС.Аутентифицировать',
            "params": {"login": self.login, "password": self.password},
            "protocol": 3,
            "id": 1
        }
        res = requests.post(f'{self.base_url}/auth/service/', headers=self.headers, data=json.dumps(payload))
        print(json.loads(res.text))
        sid = json.loads(res.text)['result']

        with open(f"{self.login}_sbis_token.txt", "w+") as file:
            file.write(sid)

        return sid

    def get_sid(self):
        try:
            with open(f"{self.login}_sbis_token.txt", "r") as file:
                sid = file.read()
                return sid
        except FileNotFoundError:
            try:
                return self.auth()
            except Exception:
                logging.critical(f"Не удалось авторизоваться в СБИС.", exc_info=True)

    def main_query(self, method: str, params: dict or str):
        self.headers['X-SBISSessionID'] = self.get_sid()
        payload = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params,
            "protocol": 5,
            "id": 1
        }

        res = requests.post(f'{self.base_url}/spp-rest-api/service/', headers=self.headers, data=json.dumps(payload))

        logging.info(f'Method: {method} | Code: {res.status_code}')
        logging.debug(f'URL: {self.base_url}/service/ \n'
                      f'Headers: {self.headers}\n'
                      f'Parameters: {params}\n'
                      f'Result: {json.loads(res.text)}')

        match res.status_code:
            case 200:
                return json.loads(res.text)['result']
            case 401:
                logging.info('Требуется обновление токена.')
                self.headers['X-SBISSessionID'] = self.auth()
                res = requests.post(f'{self.base_url}/service/', headers=self.headers, data=json.dumps(payload))
                return json.loads(res.text)['result']
            case 500:
                raise AttributeError(f'{method}: Check debug logs.')

    def search_doc(self, num, doc_type, doc_date):
        """Возвращает первый найденный документ из СБИСа по номеру документа, типу и дате.
            Номер можно прописать частично.

            Пример:
            num = 03254 - вернёт № КРТД0003254
            doc_type = "ДокОтгрВх" - поступления, "ДоговорИсх" - исходящие договоры
            doc_date: "ДД.ММ.ГГГГ" - поиск документа будет выполняться по этому дню"""
        assert any(map(str.isdigit, num)), 'СБИС не сможет найти документ по номеру без цифр'
        params = {
            "Фильтр": {
                "Маска": num,
                "ДатаС": doc_date,
                "ДатаПо": doc_date,
                "Тип": doc_type
            }
        }
        res = self.main_query("СБИС.СписокДокументов", params)
        return None if res['Документ'] == [] else res['Документ'][0]

    def search_agr(self, inn):
        """Ищет договор в СБИСе по номеру документа.
        В качестве номера договора используется ИНН поставщика.
        ИНН: Состоит из 10-и или 12-и цифр строкой"""
        if inn is not None:
            assert any(map(str.isdigit, inn)), 'СБИС не сможет найти договор по номеру, в котором нет цифр'
        params = {
            "Фильтр": {
                "Маска": inn,
                "ДатаС": '01.01.2000',
                "ДатаПо": date.today().strftime('%d.%m.%Y'),
                "Тип": "ДоговорИсх"
            }
        }
        res = self.main_query("СБИС.СписокДокументов", params)
        return None if res['Документ'] == [] else res['Документ'][0]


if __name__ == '__main__':
    sbis = SBISManager('ХарьковскийАМ', 'rx7SiNZtAb')
    answer = sbis.main_query('Contractor.Find', {'requisites': '83494939615', "page": 0, "size": 15})
    print(json.dumps(answer, ensure_ascii=False, indent=4, sort_keys=True))

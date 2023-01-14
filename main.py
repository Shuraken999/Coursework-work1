import requests
import json
import time
import sys
from progress.bar import IncrementalBar
from datetime import datetime
from settings import TOKEN, TOKEN2


class Yandex:
    host = 'https://cloud-api.yandex.net/'

    def __init__(self, token):
        self.token = token

    def get_headers(self):
        return {'Content-Type': 'application/json', 'Authorization': f'OAuth {self.token}'}

    def get_files_list(self, id_user):
        uri = 'v1/disk/resources'
        url = self.host + uri
        headers = self.get_headers()
        params = {'path': f'/{id_user}', 'fields': {'name', '_embedded.items.name'}, 'limit': 1000,
                  'media_type': 'image'}
        response = requests.get(url, headers=headers, params=params)
        list_name_file = []
        for name_file in response.json()['_embedded']['items']:
            list_name_file.append(name_file['name'])
        return list_name_file

    def create_folder(self, name_folder):
        uri = 'v1/disk/resources/'
        url = self.host + uri
        params = {'path': f'/{name_folder}'}
        response = requests.put(url, headers=self.get_headers(), params=params)
        if response.status_code == 201:
            print(f'Папка с именем {name_folder} создана')
        elif response.status_code == 409:
            print(f'Папка с именем {name_folder} уже существует')
        else:
            print('Конфликт с яндекс-диском')

    def get_upload_link(self, disk_file_name):
        uri = 'v1/disk/resources/upload/'
        url = self.host + uri
        params = {'path': f'/{disk_file_name}'}
        response = requests.get(url, headers=self.get_headers(), params=params)
        return response.json()['href']

    def upload_from_internet(self, file_url, id_user, file_name):
        uri = 'v1/disk/resources/upload/'
        url = self.host + uri
        params = {'path': f'/{id_user}/{file_name}', 'url': file_url}
        requests.post(url, headers=self.get_headers(), params=params)


class VK:

    def __init__(self, access_token, user_id, version='5.131'):
        self.token = access_token
        self.id = user_id
        self.version = version
        self.params = {'access_token': self.token, 'v': self.version}

    def users_foto(self, id_user, numb_foto=5):
        url = 'https://api.vk.com/method/photos.get'
        params = {'owner_id': id_user, 'album_id': 'profile', 'extended': '1'}
        response = requests.get(url, params={**self.params, **params})
        return response.json()['response']['items'][0:numb_foto]


access_token = TOKEN2
user_id = '684604349'
vk = VK(access_token, user_id)
ya = Yandex(TOKEN)
id_user_foto = input()
ya.create_folder(id_user_foto)

numb_foto = 4
bar = IncrementalBar('Загрузка фото', max=numb_foto)
if len(vk.users_foto(id_user_foto, numb_foto)) < numb_foto:
    print(f'Необходимо {numb_foto} в профили юзера {len(vk.users_foto(id_user_foto, numb_foto))} фото')
    sys.exit()
data_foto = []
for album in vk.users_foto(id_user_foto, numb_foto):
    bar.next()
    file_url = album['sizes'][-1]['url']
    name_like = str(album['likes']['count'])
    if name_like in ya.get_files_list(id_user_foto):
        name_data = f'{name_like}_{datetime.utcfromtimestamp(int(album["date"])).strftime("%d%m%Y")}'
        ya.upload_from_internet(file_url, id_user_foto, name_data)
        data_foto.append({'file_name': f'{name_data}.jpg', 'size': f'{album["sizes"][-1]["type"]}'})
    else:
        ya.upload_from_internet(file_url, id_user_foto, name_like)
        data_foto.append({'file_name': f'{name_like}.jpg', 'size': f'{album["sizes"][-1]["type"]}'})
    time.sleep(0.1)
bar.finish()
with open(f'data_{id_user_foto}.json', 'x') as file:
    json.dump(data_foto, file)

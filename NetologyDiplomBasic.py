import requests
from pprint import pprint
from datetime import datetime
from collections import Counter
from alive_progress import alive_bar
import json


class Backup:
    def __init__(self, vktoken, yatoken):
        self.vktoken = vktoken
        self.yatoken = yatoken

    def get_photos_from_vk(self):
        url_dict = {}
        owner_id = input('Введите ID пользователя ВК: ')
        count = int(input('Сколько фотографий нужно сохранить?: '))
        
        response = requests.get('https://api.vk.com/method/photos.get', 
                                params = {
                                    'owner_id': owner_id,
                                    'access_token': self.vktoken,
                                    'album_id': 'profile',
                                    'v': 5.131,
                                    'count': count,
                                    'extended': True
                                })
        
        photos = response.json()
        
        list_of_likes = [x['likes']['count'] for x in photos['response']['items']]
        counter = Counter(list_of_likes)

        for photo in photos['response']['items']:
            list_of_sizes = [s['type'] for s in photo['sizes']]
            max_size = max(list_of_sizes)
            for size in photo['sizes']:
                if size['type'] == str(max_size):
                    num_of_likes = photo['likes']['count']
                    if counter[num_of_likes] > 1:    
                        new_name = f"likes-{photo['likes']['count']}" + '_' + str(datetime.utcfromtimestamp(photo['date']).strftime(r'%d-%m-%Y_%H-%M-%S'))
                    else:
                        new_name = f"likes-{photo['likes']['count']}"  
                    url_dict[new_name] = [size['url'], size['type']]
                    break
                    
        return url_dict
    
    def get_headers(self):
        return {
            'Content-Type': 'application/json',
            'Authorization': 'OAuth {}'.format(self.yatoken)
        }

    def create_folder_on_disk(self, name):
        headers = self.get_headers()
        requests.put(f'https://cloud-api.yandex.net/v1/disk/resources?path={name}', headers=headers)    


    def upload_photos_on_disk(self):
        name_of_folder = input('Введите название папки для сохранения: ')
        self.create_folder_on_disk(name_of_folder)
        photos = self.get_photos_from_vk()
        data_file = []
        with alive_bar(len(photos), title='Downloading photos...') as bar:
            for name, url in photos.items():
                upload_url = "https://cloud-api.yandex.net/v1/disk/resources/upload"
                headers = self.get_headers()
                params = {
                    "path": f'/{name_of_folder}/{name}',
                    "url": url[0]
                }
                response = requests.post(upload_url, params=params, headers=headers)
                response.raise_for_status()
                if response.status_code in [201, 202]:
                    data_file.append({"file_name": name,
                                    "size": url[1]})
                    bar()
        
        with open('data_file.txt', 'w') as result:
            result.write(json.dumps(data_file))

        print(f'Загрузка завершена. Создан файл с отчётом в data_file.txt')
        
        
with open('vktoken.txt', 'r') as vktoken:
    my_vktoken = vktoken.read()

with open('yatoken.txt', 'r') as yatoken:
    my_yatoken = yatoken.read()

photos = Backup(my_vktoken, my_yatoken)


photos.upload_photos_on_disk()

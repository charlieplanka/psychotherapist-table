from django.core.management.base import BaseCommand
from psychotherapists.models import Therapist, Method, AirtableRaw
from requests.exceptions import HTTPError
from meta.settings import MEDIA_ROOT
import requests
import datetime
import json
import os.path
from dateutil.parser import parse

# safe read-only key
API_KEY = 'keyyQ4y9FQVXyzLz3'
API_URL = 'https://api.airtable.com/v0'
BASE_ID = 'appazv5uiri4NCfCn'
TABLE = 'Psychotherapists'


class Command(BaseCommand):
    help = 'Synchronize DB data with Airtable data'

    def add_arguments(self, parser):
        parser.add_argument('-k', '--key', type=str, default=API_KEY, help='Airtable API key')
        parser.add_argument('-b', '--base', type=str, default=BASE_ID, help='ID of the Airtable base')
        parser.add_argument('-t', '--table', type=str, default=TABLE, help='Title of the Airtable table')

    def handle(self, *args, **options):
        API_KEY = options['key']
        BASE_ID = options['base']
        TABLE = options['table']
        AIRTABLE_URL = f'{API_URL}/{BASE_ID}/{TABLE}'

        try:
            self.stdout.write('Retreiving data from Airtable..')
            table = get_airtable_data(AIRTABLE_URL, API_KEY).json()
        except HTTPError as err:
            self.stdout.write(f'Oops! HTTP error occurred: {err}')
            return
        else:
            self.stdout.write('Success')
        
        self.stdout.write('Saving raw data..')
        save_raw_airtable_data(table)
        self.stdout.write('Success')

        self.stdout.write('Updating DB..')
        update_therapist_db_data(table)
        self.stdout.write('Success')


class EmptyRowError(Exception):
    pass


def get_airtable_data(url, api_key):
    headers = {'Authorization': 'Bearer ' + api_key}
    r = requests.get(url, headers=headers)
    r.raise_for_status()
    return r


def save_raw_airtable_data(table):
    airtable = AirtableRaw.objects.create(data=json.dumps(table, ensure_ascii=False))
    airtable.save()


def update_therapist_db_data(table):
    remove_deleted_rows_from_db(table)

    for therapist in table['records']:
        try:
            therapist_id = get_airtable_record_id(therapist)
            last_modified_datetime = get_airtable_last_modified(therapist)
            therapist_obj = get_therapist_from_db(therapist_id)

            if not therapist_obj:
                create_therapist_object(therapist)

            elif therapist_obj.airtable_modified != last_modified_datetime:
                therapist_obj.delete()
                create_therapist_object(therapist)
        except EmptyRowError:
            continue


def remove_deleted_rows_from_db(table):
    record_ids = [record['id'] for record in table['records']]
    rows_to_delete = Therapist.objects.exclude(airtable_id__in=record_ids)
    for row in rows_to_delete:
        row.delete()
        photo_path = os.path.join(MEDIA_ROOT, row.photo.url)
        os.remove(photo_path)


def get_airtable_record_id(record):
    return record['id']


def get_airtable_last_modified(record):
    fields = record['fields']
    if not fields:
        raise EmptyRowError()
    modified = fields['Изменено']
    return parse(modified)


def get_therapist_from_db(id):
    return Therapist.objects.filter(airtable_id=id).first()


def create_therapist_object(therapist):
    therapist_id, name, photo_url, methods, modified = get_airtable_record_data(therapist)
    photo_path = save_photo_to_media(photo_url, therapist_id) # TODO: change to autouplodaing
    therapist_obj = Therapist.objects.create(name=name, photo=photo_path, airtable_id=therapist_id, airtable_modified=modified)
    therapist_obj.save()
    for method in methods:
        add_method(method, therapist_obj)
    therapist_obj.save()


def get_airtable_record_data(record):
    fields = record['fields']
    if not fields:
        raise EmptyRowError()
    name, photo_url, methods = fields['Имя'], fields['Фотография'][0]['url'], fields['Методы']
    record_id = get_airtable_record_id(record)
    modified = get_airtable_last_modified(record)
    return record_id, name, photo_url, methods, modified


def save_photo_to_media(url, person_id):
    photo = requests.get(url)
    photo_path = os.path.join(MEDIA_ROOT, 'therapists', f'{person_id}.jpg')
    with open(photo_path, 'wb') as f:
        f.write(photo.content)
    return photo_path


def add_method(method, therapist):
    method_object = Method.objects.filter(title=method).first()
    if not method_object:
        method_object = Method.objects.create(title=method)
        method_object.save()
    therapist.methods.add(method_object)

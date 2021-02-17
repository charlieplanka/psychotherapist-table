import requests
import os
from dateutil.parser import parse
import sqlalchemy as sa
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship

# safe read-only key
API_KEY = 'keyyQ4y9FQVXyzLz3'
AIRTABLE_URL = 'https://api.airtable.com/v0/appazv5uiri4NCfCn/Psychotherapists'
DB_PATH = 'postgresql+psycopg2://meta:meta@/psycho'
MEDIA_PATH = 'media'

Base = declarative_base()

association_table = sa.Table('psychotherapists_therapist_methods', Base.metadata,
    sa.Column('therapist_id', sa.Integer, sa.ForeignKey('psychotherapists_therapist.id')),
    sa.Column('method_id', sa.Integer, sa.ForeignKey('psychotherapists_method.id'))
)


class Therapist(Base):
    __tablename__ = 'psychotherapists_therapist'
    id = sa.Column(sa.Integer, primary_key=True)
    airtable_id = sa.Column(sa.Text)   # TODO: make primary key
    airtable_modified = sa.Column(sa.DateTime)
    name = sa.Column(sa.Text)
    photo = sa.Column(sa.Text)
    methods = relationship('Method',
                    secondary=association_table,
                    backref='therapists')


class Method(Base):
    __tablename__ = 'psychotherapists_method'
    id = sa.Column(sa.Integer, primary_key=True)
    title = sa.Column(sa.Text)


def connect_to_db(DB_PATH):
    engine = sa.create_engine(DB_PATH)
    Session = sessionmaker(engine)
    return Session()


def get_airtable_data(url, api_key):
    headers = {'Authorization': 'Bearer ' + api_key}
    return requests.get(url,  headers=headers)


def get_airtable_record_data(record):
    fields = record['fields']
    # TODO: handle empty row without fields (exception?)
    name, photo_url, methods = fields['Имя'], fields['Фотография'][0]['url'], fields['Методы']
    record_id = get_airtable_record_id(record)
    modified = get_airtable_modified(record)
    return record_id, name, photo_url, methods, modified


def get_airtable_record_id(record):
    return record['id']


def get_airtable_modified(record):
    modified = record['fields']['Изменено']
    return parse(modified)


def save_photo_to_media(url, person_id):
    photo = requests.get(url)
    photo_path = f'therapists\\{person_id}.jpg'
    with open(f'{MEDIA_PATH}\\{photo_path}', 'wb') as f:
        f.write(photo.content)
    return photo_path


def add_method(method, therapist):
    method_object = session.query(Method).filter(Method.title == method).first()
    if not method_object:
        method_object = Method(title=method)
    therapist.methods.append(method_object)


def get_therapist_from_db(id):
    return session.query(Therapist).filter(Therapist.airtable_id == id).first()


def remove_deleted_rows_from_db(table):
    record_ids = [record['id'] for record in table['records']]
    rows_to_delete = session.query(Therapist).filter(Therapist.airtable_id.notin_(record_ids)).all()
    for row in rows_to_delete:
        session.delete(row)
        os.remove(f'{MEDIA_PATH}\\{row.photo}')


def create_therapist_object(therapist):
    therapist_id, name, photo_url, methods, modified = get_airtable_record_data(therapist)
    photo_path = save_photo_to_media(photo_url, therapist_id)
    therapist_obj = Therapist(name=name, photo=photo_path, airtable_id=therapist_id, airtable_modified=modified)
    for method in methods:
        add_method(method, therapist_obj)
    session.add(therapist_obj)


table = get_airtable_data(AIRTABLE_URL, API_KEY).json()
session = connect_to_db(DB_PATH)

remove_deleted_rows_from_db(table)

for therapist in table['records']:
    therapist_id = get_airtable_record_id(therapist)
    modified = get_airtable_modified(therapist)
    therapist_obj = get_therapist_from_db(therapist_id)    

    if not therapist_obj:
        create_therapist_object(therapist)
    
    elif therapist_obj.airtable_modified != modified:
        session.delete(therapist_obj)
        create_therapist_object(therapist)

session.commit()

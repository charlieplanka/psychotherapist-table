import requests
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
    name = sa.Column(sa.Text)
    photo = sa.Column(sa.Text)
    photo_url = sa.Column(sa.Text) # убрать поле
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
    record_id, name, photo_url, methods = record['id'], fields['Имя'], fields['Фотография'][0]['url'], fields['Методы']
    return record_id, name, photo_url, methods


def save_photo_to_media(url, person_id):
    photo = requests.get(photo_url)
    photo_path = f'therapists\\{person_id}.jpg'
    with open(f'{MEDIA_PATH}\\{photo_path}', 'wb') as f:
        f.write(photo.content)
    return photo_path


def add_method(method, therapist):
    method_object = session.query(Method).filter(Method.title == method).first()
    if not method_object:
        method_object = Method(title=method)
    therapist.methods.append(method_object)


table = get_airtable_data(AIRTABLE_URL, API_KEY).json()
session = connect_to_db(DB_PATH)

for therapist in table['records']:
    therapist_id, name, photo_url, methods = get_airtable_record_data(therapist)
    photo_path = save_photo_to_media(photo_url, therapist_id)
    therapist_object = Therapist(name=name, photo=photo_path)
    for method in methods:
        add_method(method, therapist_object)
    session.add(therapist_object)
session.commit()

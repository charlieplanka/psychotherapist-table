import requests
import sqlalchemy as sa
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship

# safe read-only key
API_KEY = 'keyyQ4y9FQVXyzLz3'
AIRTABLE_URL = 'https://api.airtable.com/v0/appazv5uiri4NCfCn/Psychotherapists'
DB_PATH = 'postgresql+psycopg2://meta:meta@/psycho'

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


def get_airtable_data(url, api_key):
    headers = {'Authorization': 'Bearer ' + api_key}
    return requests.get(url,  headers=headers)


def connect_to_db(DB_PATH):
    engine = sa.create_engine(DB_PATH)
    Session = sessionmaker(engine)
    return Session()


table = get_airtable_data(AIRTABLE_URL, API_KEY).json()
session = connect_to_db(DB_PATH)

therapists = session.query(Therapist).all()
for therapist in table['records']:
    fields = therapist['fields']
    name, photo_url, methods = fields['Имя'], fields['Фотография'][0]['url'], fields['Методы']

    photo = requests.get(photo_url)
    photo_path = f'therapists\\{therapist["id"]}.jpg'
    with open(f'media\\{photo_path}', 'wb') as f:
        f.write(photo.content)

    therapist = Therapist(name=name, photo=photo_path)
    for method in methods:
        # убрать дублирующиеся методы
        method = Method(title=method)
        therapist.methods.append(method)
    session.add(therapist)
session.commit()

# print(therapist.name, therapist.photo_url) 
# for method in therapist.methods:
#     print(method.title)
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

table = get_airtable_data(AIRTABLE_URL, API_KEY)
print(table.json())

engine = create_engine(DB_PATH)
Sessions = sessionmaker(engine)
session = Sessions()

therapists = session.query(Therapist).all()
for therapist in therapists:
    print(therapist.name)
    for method in therapist.methods:
        print(method.title)
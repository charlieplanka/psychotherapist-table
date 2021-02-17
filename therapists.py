import requests, os, datetime, json, argparse
from requests.exceptions import HTTPError
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


class AirtableRaw(Base):
    __tablename__ = 'psychotherapists_airtableraw'
    id = sa.Column(sa.Integer, primary_key=True)
    timestamp = sa.Column(sa.DateTime)
    data = sa.Column(sa.Text)


class EmptyRowError(Exception):
    pass


def connect_to_db(DB_PATH):
    engine = sa.create_engine(DB_PATH)
    Session = sessionmaker(engine)
    return Session()


def get_airtable_data(url, api_key):
    headers = {'Authorization': 'Bearer ' + api_key}
    r = requests.get(url,  headers=headers)
    r.raise_for_status()
    return r        


def save_raw_airtable_data(session, table):
    airtable_obj = AirtableRaw(timestamp=datetime.datetime.now(), data=json.dumps(table, ensure_ascii=False))
    session.add(airtable_obj)


def remove_deleted_rows_from_db(session, table):
    record_ids = [record['id'] for record in table['records']]
    rows_to_delete = session.query(Therapist).filter(Therapist.airtable_id.notin_(record_ids)).all()
    for row in rows_to_delete:
        session.delete(row)
        os.remove(f'{MEDIA_PATH}\\{row.photo}')


def update_therapist_db_data(session, table):
    remove_deleted_rows_from_db(session, table)
    
    for therapist in table['records']:
        try:
            therapist_id = get_airtable_record_id(therapist)
            modified = get_airtable_modified(therapist)
            therapist_obj = get_therapist_from_db(session, therapist_id)

            if not therapist_obj:
                create_therapist_object(session, therapist)

            elif therapist_obj.airtable_modified != modified:
                session.delete(therapist_obj)
                create_therapist_object(session, therapist)
        except EmptyRowError:
            continue


def get_airtable_record_data(record):
    fields = record['fields']
    if not fields:
        raise EmptyRowError()
    name, photo_url, methods = fields['Имя'], fields['Фотография'][0]['url'], fields['Методы']
    record_id = get_airtable_record_id(record)
    modified = get_airtable_modified(record)
    return record_id, name, photo_url, methods, modified


def get_airtable_record_id(record):
    return record['id']


def get_airtable_modified(record):
    fields = record['fields']
    if not fields:
        raise EmptyRowError()
    modified = fields['Изменено']
    return parse(modified)


def save_photo_to_media(url, person_id):
    photo = requests.get(url)
    photo_path = f'therapists\\{person_id}.jpg'
    with open(f'{MEDIA_PATH}\\{photo_path}', 'wb') as f:
        f.write(photo.content)
    return photo_path


def add_method(session, method, therapist):
    method_object = session.query(Method).filter(Method.title == method).first()
    if not method_object:
        method_object = Method(title=method)
    therapist.methods.append(method_object)


def get_therapist_from_db(session, id):
    return session.query(Therapist).filter(Therapist.airtable_id == id).first()


def create_therapist_object(session, therapist):
    therapist_id, name, photo_url, methods, modified = get_airtable_record_data(therapist)
    photo_path = save_photo_to_media(photo_url, therapist_id)
    therapist_obj = Therapist(name=name, photo=photo_path, airtable_id=therapist_id, airtable_modified=modified)
    for method in methods:
        add_method(session, method, therapist_obj)
    session.add(therapist_obj)


def parse_args():
    parser = argparse.ArgumentParser(description='Synchronize DB data with Airtable data.')
    parser.add_argument('-k', '--key', type=str, default=API_KEY, help='Airtable API key')
    parser.add_argument('-u', '--url', type=str, default=AIRTABLE_URL, help='API URL of the Airtable table')
    return parser.parse_args()


def main():
    args = parse_args()
    API_KEY = args.key
    AIRTABLE_URL = args.url

    try:
        print('Retreiving data from Airtable..')
        table = get_airtable_data(AIRTABLE_URL, API_KEY).json()
    except HTTPError as err:
        print(f'Oops! HTTP error occurred: {err}')
        return
    else:
        print('Success')
    
    session = connect_to_db(DB_PATH)

    print('Saving raw data..')
    save_raw_airtable_data(session, table)
    print('Success')

    print('Updating DB..')
    update_therapist_db_data(session, table)
    session.commit()
    print('Success')


if __name__ == "__main__":
    main()

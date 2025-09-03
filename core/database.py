import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from configparser import ConfigParser

def load_db_config(filename='database.ini', section='postgresql'):
    """ Load database configuration from a file. """
    # create a parser
    parser = ConfigParser()
    # read config file
    if not os.path.exists(filename):
        raise Exception(f'Section {section} not found in the {filename} file')

    parser.read(filename)

    # get section, default to postgresql
    db = {}
    if parser.has_section(section):
        params = parser.items(section)
        for param in params:
            db[param[0]] = param[1]
    else:
        raise Exception(f'Section {section} not found in the {filename} file')

    return db

def get_db_engine():
    """ Creates and returns a new SQLAlchemy engine. """
    try:
        db_config = load_db_config()
        # Construct the database URL
        db_url = f"postgresql+psycopg2://{db_config['user']}:{db_config['password']}@{db_config['host']}:{db_config['port']}/{db_config['database']}"
        engine = create_engine(db_url)
        return engine
    except Exception as e:
        print(f"Error creating database engine: {e}")
        return None

def get_db_session():
    """ Creates and returns a new SQLAlchemy session. """
    engine = get_db_engine()
    if engine:
        Session = sessionmaker(bind=engine)
        session = Session()
        return session
    return None

if __name__ == '__main__':
    # This is for testing the connection
    engine = get_db_engine()
    if engine:
        try:
            connection = engine.connect()
            print("Database connection successful!")
            connection.close()
        except Exception as e:
            print(f"Database connection failed: {e}")
    else:
        print("Could not create database engine.")

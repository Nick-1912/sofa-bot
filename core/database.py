import psycopg2
from core.config_parser import DatabaseConfig


class Database:
    """db format:
    table name: data
    columns: match_date: str, status: str, team1: str, team2: str, is_live: int
    """
    DB_CONFIG = DatabaseConfig()
    PARAMS = {'host': 'localhost',
              'database': DB_CONFIG['database'],
              'user': DB_CONFIG['user'],
              'password': DB_CONFIG['password']}

    def get_rows(self, n: int = 100):
        data = None
        connection = None
        sql = f"""SELECT * FROM data
                  LIMIT {n}"""
        try:
            connection = psycopg2.connect(**self.PARAMS)
            cursor = connection.cursor()
            cursor.execute(sql)
            data = cursor.fetchall()
            cursor.close()
        except Exception as e:
            print(e)
        finally:
            if connection is not None:
                connection.close()
        return data

    def get_rows_by_team(self, team: str):
        data = None
        connection = None
        sql = f"""SELECT * FROM data
                  WHERE team1='{team}' OR team2='{team}';"""
        try:
            connection = psycopg2.connect(**self.PARAMS)
            cursor = connection.cursor()
            cursor.execute(sql)
            data = cursor.fetchall()
            cursor.close()
        except Exception as e:
            print(e)
        finally:
            if connection is not None:
                connection.close()
        return data

    def get_rows_by_teams_data(self, row: dict):
        data = None
        connection = None
        sql = f"""SELECT * FROM data
                  WHERE (team1='{row["team1"]}' AND team2='{row["team2"]}' 
                  OR team1='{row["team2"]}' AND team2='{row["team1"]}') AND 
                  match_date='{row["time"]}' AND status='{row["status"]}';"""
        try:
            connection = psycopg2.connect(**self.PARAMS)
            cursor = connection.cursor()
            cursor.execute(sql)
            data = cursor.fetchall()
            cursor.close()
        except Exception as e:
            print(e)
        finally:
            if connection is not None:
                connection.close()
        return data

    def insert_row(self, row: dict):
        sql = """INSERT INTO data
                 VALUES(%s,%s,%s,%s,%s);"""
        connection = None
        try:
            connection = psycopg2.connect(**self.PARAMS)
            cursor = connection.cursor()
            cursor.execute(sql, (row['time'], row['status'], row['team1'], row['team2'],
                                 1 if row['is live'] else 0))
            connection.commit()
            cursor.close()
        except (Exception, psycopg2.DatabaseError) as error:
            print(error)
        finally:
            if connection is not None:
                connection.close()


if __name__ == '__main__':
    temp_db = Database()
    print(temp_db.get_rows())
    print(temp_db.get_rows_by_team('test1'))

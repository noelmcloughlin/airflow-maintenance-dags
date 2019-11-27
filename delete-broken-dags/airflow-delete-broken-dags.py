"""
A maintenance workflow that you can deploy into Airflow to periodically delete broken DAG file(s).

airflow trigger_dag airflow-delete-broken-dags

"""
from airflow.models import DAG, ImportError
from airflow.operators.python_operator import PythonOperator
from airflow import settings
from datetime import timedelta
import os
import os.path
import socket
import logging
import airflow


DAG_ID = '%s-${project.version}' % os.path.basename(__file__).replace(".pyc", "").replace(".py", "")  # airflow-delete-broken-dags
START_DATE = airflow.utils.dates.days_ago(1)
SCHEDULE_INTERVAL = "@daily"        # How often to Run. @daily - Once a day at Midnight
DAG_OWNER_NAME = "operations"       # Who is listed as the owner of this DAG in the Airflow Web Server
ALERT_EMAIL_ADDRESSES = []          # List of email address to send email alerts to if this job fails
ENABLE_DELETE = True                # Whether the job should delete the logs or not. Included if you want to temporarily avoid deleting the logs

default_args = {
    'owner': DAG_OWNER_NAME,
    'email': ALERT_EMAIL_ADDRESSES,
    'email_on_failure': True,
    'email_on_retry': False,
    'start_date': START_DATE,
    'retries': 1,
    'retry_delay': timedelta(minutes=1)
}

dag = DAG(DAG_ID, default_args=default_args, schedule_interval=SCHEDULE_INTERVAL, start_date=START_DATE)
if hasattr(dag, 'doc_md'):
    dag.doc_md = __doc__
if hasattr(dag, 'catchup'):
    dag.catchup = False


def delete_broken_dag_files(**context):

    logging.info("Starting to run Clear Process")

    try:
        host_name = socket.gethostname()
        host_ip = socket.gethostbyname(host_name)
        logging.info("Running on Machine with Host Name: " + host_name)
        logging.info("Running on Machine with IP: " + host_ip)
    except Exception as e:
        print("Unable to get Host Name and IP: " + str(e))

    session = settings.Session()

    logging.info("Configurations:")
    logging.info("enable_delete:            " + str(ENABLE_DELETE))
    logging.info("session:                  " + str(session))
    logging.info("")

    errors = session.query(ImportError).all()

    logging.info("Process will be removing broken DAG file(s) from the file system:")
    for error in errors:
        logging.info("\tFile: " + str(error.filename))
    logging.info("Process will be Deleting " + str(len(errors)) + " DAG file(s)")

    if ENABLE_DELETE:
        logging.info("Performing Delete...")
        for error in errors:
            if os.path.exists(error.filename):
                os.remove(error.filename)
            session.delete(error)
        logging.info("Finished Performing Delete")
    else:
        logging.warn("You're opted to skip Deleting the DAG file(s)!!!")

    logging.info("Finished")


delete_broken_dag_files = PythonOperator(
    task_id='delete_broken_dag_files',
    python_callable=delete_broken_dag_files,
    provide_context=True,
    dag=dag)

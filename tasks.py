# tasks.py

from celery import Celery

from corporate_fetch import fetch_corporates as fetch_corporates_func

app = Celery("tasks_fetch", broker='pyamqp://guest:guest@rabbitmq:5672//', backend="rpc://")
@app.task
def fetch_corporates_celery():
    result1 = fetch_corporates_func()
    result2 = "Görev başarıyla tamamlandı"

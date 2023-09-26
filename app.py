
import uuid
import os

from flask import Flask, send_file, jsonify, request
from flask.views import MethodView
from celery import Celery
from celery.result import AsyncResult
from werkzeug.exceptions import NotFound

from upscale import upscale

UPLOAD_FOLDER = "files"

app_name = 'app'
app = Flask(app_name)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
celery = Celery(
    app_name,
    backend='redis://localhost:6379/3',
    broker='redis://localhost:6379/4'
)
celery.conf.update(app.config)


class ContextTask(celery.Task):
    def __call__(self, *args, **kwargs):
        with app.app_context():
            return self.run(*args, **kwargs)

celery.Task = ContextTask


@celery.task()
def upscale_photo(path_in, path_out):
    result = upscale(path_in, path_out)
    return result



class Upscale(MethodView):

    result_files = {}

    def get(self, task_id):
        task = AsyncResult(task_id, app=celery)
        result = {'status': task.status}
        if task.status == "SUCCESS":
            result["filename"] = self.result_files[task.id]
        return jsonify(result)

    def post(self):
        image_name = self.save_image('image_name')
        task = upscale_photo.delay(os.path.join(UPLOAD_FOLDER, image_name),
                                   os.path.join(UPLOAD_FOLDER, f'upscaled_{image_name}'))
        self.result_files[task.id] = f'upscaled_{image_name}'
        return jsonify(
            {'task_id': task.id}
        )

    def save_image(self, field):
        image = request.files.get(field)
        extension = image.filename.split('.')[-1]
        file_name = f'{uuid.uuid4()}.{extension}'
        image.save(os.path.join(UPLOAD_FOLDER, file_name))
        return file_name


class Processed(MethodView):

    def get(self, file_name):
        result_path = os.path.join(UPLOAD_FOLDER, file_name)
        if os.path.isfile(result_path):
            return send_file(result_path, download_name=file_name)
        else:
            return NotFound()


upscale_view = Upscale.as_view('upscale')
app.add_url_rule('/upscale/', view_func=upscale_view, methods=['POST'])
app.add_url_rule('/tasks/<string:task_id>', view_func=upscale_view, methods=['GET'])
processed_view = Processed.as_view('processed')
app.add_url_rule('/processed/<string:file_name>', view_func=processed_view, methods=['GET'])


if __name__ == '__main__':
    app.run()

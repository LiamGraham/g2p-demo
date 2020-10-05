from flask import Flask, render_template, request
from werkzeug.utils import secure_filename
import glob
import os
from collections import namedtuple
from uuid import uuid4

app = Flask(__name__)

MODEL_PATH = "/root/uni/anylang/high_resource/high_resource_openfst"
UPLOAD_FOLDER = "/root/uni/demo/uploads"

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024


def get_models(dir_path):
    models = {}
    paths = glob.glob(os.path.join(dir_path, "*"))
    for path in paths:
        model_file = os.path.basename(path)
        model_name = os.path.splitext(model_file)[0]
        models[model_name] = path
    return models

models = get_models(MODEL_PATH)


def save_file(storage):
    filename = os.path.join(app.config["UPLOAD_FOLDER"], secure_filename(uuid4().hex))
    storage.save(filename)
    return filename


@app.route("/", methods=["GET", "POST"])
def index():
    model_names = sorted(models.keys())
    if request.method == "POST":
        model = request.form["model"]
        inventory = save_file(request.files["inventory"])
        word_list = save_file(request.files["word-list"])
        #convert(word_list, inventory, model_names[model])
    return render_template("index.html", models=model_names)

@app.route("/lexicon/{<int:lex_id>}")
def get_lexicon(lex_id):
    return str(lex_id)

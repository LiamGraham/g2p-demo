from flask import Flask, render_template, request, redirect, url_for, send_from_directory
from werkzeug.utils import secure_filename
import glob
import os
from collections import namedtuple
from uuid import uuid4

from ..g2p import g2p

app = Flask(__name__)

MODEL_PATH = "/root/uni/anylang/high_resource/high_resource_openfst"
UPLOAD_FOLDER = "/root/uni/g2p/demo/uploads"
LEXICON_FOLDER = "/root/uni/g2p/demo/lexicons"

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


def generate_id():
    return uuid4().hex[:10]


def get_lexicon_path(lex_id):
    return os.path.join(LEXICON_FOLDER, lex_id) + ".lex"


def save_file(storage):
    filename = os.path.join(app.config["UPLOAD_FOLDER"], generate_id())
    storage.save(filename)
    return filename


def save_lexicon(lexicon):
    lex_id = generate_id()
    filename = get_lexicon_path(lex_id)
    with open(filename, "w") as f:
        for entry in lexicon:
            f.write(str(entry) + "\n")
    return lex_id


def update_lexicon(lex_id, prons):
    lexicon = list(load_lexicon(lex_id))
    print("Update lexicon")
    with open(get_lexicon_path(lex_id), "w") as f:
        for entry in lexicon:
            entry.pron = next(prons)
            f.write(str(entry) + "\n")


def load_lexicon(lex_id):
    with open(get_lexicon_path(lex_id), "r") as f:
        for line in f:
            word, pron = line.strip().split(" ", maxsplit=1)
            yield g2p.PronEntry(word, pron)


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        model = request.form["model"]
        inventory = save_file(request.files["inventory"])
        word_list = save_file(request.files["word-list"])
        converter = g2p.Converter(word_list, inventory, models[model])
        lexicon = converter.convert()
        lex_id = save_lexicon(lexicon)
        print("Save lexicon")
        return redirect(url_for("show_lexicon", lex_id=lex_id))
    else:
        model_names = sorted(models.keys())
        return render_template("index.html", models=model_names)


@app.route("/lexicon/<lex_id>", methods=["GET", "POST"])
def show_lexicon(lex_id):
    if request.method == "POST":
        update_lexicon(lex_id, request.form.values())
        return redirect(url_for("send_lexicon", lex_id=lex_id))
    else:
        lexicon = load_lexicon(lex_id)
        return render_template("lexicon.html", 
            lexicon=lexicon, 
        )

@app.route("/lexicon/<lex_id>/download")
def send_lexicon(lex_id):
    filename = lex_id + ".lex"
    return send_from_directory(LEXICON_FOLDER, filename, as_attachment=True)

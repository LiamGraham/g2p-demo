from flask import Flask, render_template, request, redirect, url_for, send_from_directory
from werkzeug.utils import secure_filename
import glob
import os
from collections import namedtuple
from uuid import uuid4
from typing import List

from ..g2p import g2p

app = Flask(__name__)

MODEL_PATH = "/root/uni/anylang/high_resource/high_resource_openfst"
UPLOAD_FOLDER = "/root/uni/g2p/demo/uploads"
LEXICON_FOLDER = "/root/uni/g2p/demo/lexicons"

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024


def get_models(dir_path) -> List[str]:
    """Returns the list of paths of models in the given directory.
    """
    models = {}
    paths = glob.glob(os.path.join(dir_path, "*"))
    for path in paths:
        model_file = os.path.basename(path)
        model_name = os.path.splitext(model_file)[0]
        models[model_name] = path
    return models

models = get_models(MODEL_PATH)


def generate_id() -> str:
    """
    Returns a new unique ID.
    """
    return uuid4().hex[:10]


def get_lexicon_path(lex_id):
    return os.path.join(LEXICON_FOLDER, lex_id) + ".lex"


def save_file(storage) -> str:
    """
    Saves the given file storage object as a file in the upload folder and returns the file path. 
    """
    filename = os.path.join(app.config["UPLOAD_FOLDER"], generate_id())
    storage.save(filename)
    return filename


def save_lexicon(lexicon) -> str:
    """
    Saves the given Lexicon to a file and returns the generated lexicon ID.
    """
    lex_id = generate_id()
    filename = get_lexicon_path(lex_id)
    lexicon.save(filename)
    return lex_id


def save_lexicon_file(storage):
    """
    Saves the given uploaded lexicon file and returns the generated lexicon ID.
    """
    lex_id = generate_id()
    filename = get_lexicon_path(lex_id)
    storage.save(filename)
    return lex_id


def update_lexicon(lex_id, prons):
    """
    Updates the lexicon with the given lexicon ID using the given pronunciations.
    """
    lexicon = load_lexicon(lex_id)
    lexicon.update(prons)
    lexicon.save()


def load_lexicon(lex_id):
    return g2p.Lexicon(get_lexicon_path(lex_id))


def prepare_data(lex_id, ref_id):
    lexicon = load_lexicon(lex_id)
    reference = load_lexicon(ref_id)
    
    ref_prons = []
    distances = []
    for entry in lexicon:
        actual = reference.entries.get(entry.word)
        if actual:
            ref_prons.append(actual.pron)
            distance = round(entry.compare(actual), 3)
            distances.append(distance)
        else:
            ref_prons.append(g2p.NULL_PRON)
            distances.append(1.0)
    return zip(lexicon, ref_prons, distances)

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        model = request.form["model"]
        inventory = save_file(request.files["inventory"])
        word_list = save_file(request.files["word-list"])
        
        converter = g2p.Converter(word_list, inventory, models[model])
        lexicon = converter.convert()
        
        print("Save lexicon")
        lex_id = save_lexicon(lexicon)
        ref_id = save_lexicon_file(request.files["reference"])
        return redirect(url_for("show_lexicon", lex_id=lex_id, ref_id=ref_id))
    else:
        model_names = sorted(models.keys())
        return render_template("index.html", models=model_names)


@app.route("/lexicon/<lex_id>", methods=["GET", "POST"])
def show_lexicon(lex_id):
    if request.method == "POST":
        prons = list(request.form.values())
        update_lexicon(lex_id, prons)
        return redirect(url_for("send_lexicon", lex_id=lex_id))
    else:
        ref_id = request.args.get("ref_id")
        if not ref_id:
            return "Error: Reference ID not specified"

        data = prepare_data(lex_id, ref_id)
        return render_template("lexicon.html", 
            data=data
        )

@app.route("/lexicon/<lex_id>/download")
def send_lexicon(lex_id):
    filename = lex_id + ".lex"
    return send_from_directory(LEXICON_FOLDER, filename, as_attachment=True)
